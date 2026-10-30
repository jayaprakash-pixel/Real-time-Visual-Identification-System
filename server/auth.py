"""P2.2: operator accounts (scrypt-hashed passwords) and HMAC-signed, expiring tokens."""

import base64
import hashlib
import hmac
import json
import os
import time


class AuthError(Exception):
    def __init__(self, status, message, field=None):
        super().__init__(message)
        self.status, self.message, self.field = status, message, field


def _hash(password, salt):
    return hashlib.scrypt(password.encode(), salt=salt, n=2 ** 14, r=8, p=1).hex()


class Users:

    def __init__(self, db, lock, secret, token_hours=12.0, allow_signup=False):
        self.db, self.lock = db, lock
        self.secret = secret if isinstance(secret, bytes) else secret.encode()
        self.token_seconds, self.allow_signup = token_hours * 3600, allow_signup
        self.failures = {}                # email -> timestamps of recent failed logins
        with lock, db:
            db.execute("""CREATE TABLE IF NOT EXISTS users (
                email TEXT PRIMARY KEY, name TEXT NOT NULL, role TEXT NOT NULL,
                salt BLOB NOT NULL, hash TEXT NOT NULL)""")

    # ---- accounts ----
    def signup(self, name, email, password):
        email = (email or "").strip().lower()
        if "@" not in email:
            raise AuthError(400, "Enter a valid email.", "email")
        if len(password or "") < 8:
            raise AuthError(400, "Password must be at least 8 characters.", "password")
        with self.lock:
            first = self.db.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0
            if not first and not self.allow_signup:      # open signup would let anyone into police records
                raise AuthError(403, "Signup is closed. Ask an administrator.")
            if self.db.execute("SELECT 1 FROM users WHERE email=?", (email,)).fetchone():
                raise AuthError(409, "An account with this email already exists.", "email")
            salt = os.urandom(16)
            role = "Admin" if first else "Operator"
            with self.db:
                self.db.execute("INSERT INTO users VALUES (?,?,?,?,?)",
                                (email, (name or email.split("@")[0]).strip(), role, salt, _hash(password, salt)))
        return self._session(email, name or email.split("@")[0], role)

    def login(self, email, password):
        email = (email or "").strip().lower()
        self._throttle(email)
        with self.lock:
            row = self.db.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
        # Hash even for unknown users so response time does not reveal which emails exist.
        salt = row["salt"] if row else b"\0" * 16
        ok = hmac.compare_digest(_hash(password or "", salt), row["hash"] if row else "0" * 64)
        if not row or not ok:
            self.failures.setdefault(email, []).append(time.time())
            raise AuthError(401, "Invalid email or password.")
        self.failures.pop(email, None)
        return self._session(row["email"], row["name"], row["role"])

    def _throttle(self, email, limit=5, window=60):
        """Slows password guessing: after `limit` failures in `window` s that email is locked for the rest of it."""
        recent = [t for t in self.failures.get(email, []) if time.time() - t < window]
        self.failures[email] = recent
        if len(recent) >= limit:
            raise AuthError(429, "Too many failed attempts. Try again in a minute.")

    def _session(self, email, name, role):
        return {"token": self.issue(email), "user": {"name": name, "email": email, "role": role}}

    # ---- tokens ----
    def issue(self, email, ttl=None, scope="api"):
        body = base64.urlsafe_b64encode(json.dumps(
            {"sub": email, "scope": scope, "exp": time.time() + (ttl or self.token_seconds)}).encode()).decode().rstrip("=")
        return f"{body}.{self._sign(body)}"

    def verify(self, token, scope="api"):
        """Returns the email or raises AuthError(401). A token only works for its own scope."""
        try:
            body, sig = (token or "").split(".")
            if not hmac.compare_digest(sig, self._sign(body)):
                raise ValueError
            claims = json.loads(base64.urlsafe_b64decode(body + "=" * (-len(body) % 4)))
            if claims["exp"] < time.time() or claims["scope"] != scope:
                raise ValueError
            return claims["sub"]
        except (ValueError, KeyError, json.JSONDecodeError):
            raise AuthError(401, "Not authenticated.") from None

    def _sign(self, body):
        return hmac.new(self.secret, body.encode(), hashlib.sha256).hexdigest()

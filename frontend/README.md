# 🛡️ Survelliance — AI-Powered Missing Person Surveillance System

> A React-based frontend for a real-time AI surveillance command center designed to assist in locating missing persons using live camera feeds and facial recognition.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Pages & Features](#pages--features)
- [Components](#components)
- [Authentication](#authentication)
- [Styling & Theme](#styling--theme)
- [Design System](#design-system)
- [Getting Started](#getting-started)
- [Scripts](#scripts)
- [Planned / Upcoming](#planned--upcoming)

---

## Overview

**Survelliance** is the frontend interface for an AI-powered missing person surveillance platform. It provides:

- A secure **operator login / signup** gate
- A **live surveillance dashboard** waiting for camera feed integration
- A **missing person registration form** that captures details and photographs to forward to the AI Recognition Module
- A persistent **sidebar navigation** and **topbar** with a live system status indicator

The app is structured for future integration with a backend database and an AI facial recognition pipeline.

---

## Tech Stack

| Technology | Version | Purpose |
|---|---|---|
| **React** | 19.x | UI framework |
| **React Router DOM** | 7.x | Client-side routing |
| **Vite** | 8.x | Build tool & dev server |
| **Lucide React** | 1.x | Icon library |
| **Plain CSS** | — | Styling (no CSS framework) |
| **oxlint** | 1.x | Linter |

---

## Project Structure

```
Frontend/
├── public/
├── src/
│   ├── components/
│   │   ├── Layout.jsx        # Shell layout (Sidebar + Topbar + Outlet)
│   │   ├── Sidebar.jsx       # Fixed left navigation panel
│   │   └── Topbar.jsx        # Sticky top header with live badge
│   ├── context/
│   │   └── AuthContext.jsx   # Auth state management (login, signup, logout)
│   ├── pages/
│   │   ├── Login.jsx         # Login / Sign-up page
│   │   ├── Home.jsx          # Dashboard — Live feed & detection alerts
│   │   └── Registration.jsx  # Missing person registration form
│   ├── styles/
│   │   ├── index.css         # Global design system & CSS variables
│   │   ├── Login.css         # Login page styles
│   │   └── Home.css          # Dashboard, sidebar, form styles
│   ├── App.jsx               # Root component with routing logic
│   └── main.jsx              # React DOM entry point
├── package.json
└── README.md
```

---

## Pages & Features

### 🔐 Login Page — `/` (unauthenticated)

**File:** [`src/pages/Login.jsx`](src/pages/Login.jsx)  
**Styles:** [`src/styles/Login.css`](src/styles/Login.css)

The entry gate to the system. Supports two modes toggled inline:

**Sign In Mode**
- Email + Password fields with icon decorators
- Show/hide password toggle (Eye / EyeOff icons)
- Client-side form validation (email format, min 8-char password)
- 800ms simulated async login (placeholder for future DB)
- Inline error messages with animated alert banner
- "256-bit encrypted · Authorized personnel only" security badge

**Sign Up Mode**
- Adds Full Name + Confirm Password fields
- Validates name presence and password match
- Creates an operator account (localStorage-persisted)

**Visual Features**
- Animated floating orb background blobs (CSS `::before` / `::after`)
- Subtle dot-grid background overlay
- Glassmorphism card with gradient border glow
- Floating animated logo with Shield icon
- `fadeInUp` card entrance animation

---

### 🏠 Home / Dashboard — `/`

**File:** [`src/pages/Home.jsx`](src/pages/Home.jsx)

The main command center view shown after login. Currently displays two placeholder panels awaiting backend/hardware integration:

- **Live Surveillance Feed** panel — Video icon placeholder, awaiting mobile streaming module connection
- **Recent Detection Alerts** panel — Empty state, will populate when the AI matches a face from the live feed to the database

---

### 📋 Missing Person Registration — `/register`

**File:** [`src/pages/Registration.jsx`](src/pages/Registration.jsx)  
**Styles:** [`src/styles/Home.css`](src/styles/Home.css)

A comprehensive data-entry form to register a missing individual into the AI recognition system.

**Fields:**
| Field | Type | Required |
|---|---|---|
| Photograph | File upload (JPG/PNG, max 5MB) | ✅ |
| Full Name | Text input | ✅ |
| Age | Number input | ✅ |
| Gender | Select (Male / Female / Other) | ✅ |
| Missing Date | Date picker | ✅ |
| Missing Location | Text input | ✅ |
| Additional Description | Textarea | ❌ |

**Behavior:**
- Photo preview with one-click removal
- All required fields validated before submission
- On submit: logs details and forwards photograph to AI Recognition Module (mock)
- 5-second auto-dismissing green success banner
- Form resets after successful submission

---

## Components

### Layout — [`src/components/Layout.jsx`](src/components/Layout.jsx)
Shell wrapper used for all authenticated routes. Renders `<Sidebar>` + `<Topbar>` + `<Outlet>` (page content). Dynamically computes the page title and subtitle from the current route path.

### Sidebar — [`src/components/Sidebar.jsx`](src/components/Sidebar.jsx)
Fixed 260px left navigation panel with:
- **Brand header** — Shield icon + "Survelliance" title
- **Main Menu** — Dashboard, Register Person (active state highlighted)
- **System** — Live Feeds, Settings (placeholder buttons)
- **User footer** — Avatar initials, username/email, role badge, logout button
- Mobile-responsive: slides in/out via `open` class

### Topbar — [`src/components/Topbar.jsx`](src/components/Topbar.jsx)
Sticky top bar with:
- Hamburger menu button (mobile only, hidden on desktop)
- Dynamic page title + subtitle
- **"System Active"** live status badge with animated pulsing green dot

---

## Authentication

**File:** [`src/context/AuthContext.jsx`](src/context/AuthContext.jsx)

Implemented using React Context API (`createContext` + `useContext`).

| Feature | Detail |
|---|---|
| **Persistence** | `localStorage` key: `sentinel_user` |
| **Login** | Validates in UI, stores `{ email, role: 'Operator' }` |
| **Signup** | Stores `{ name, email, role: 'Operator' }` |
| **Logout** | Clears user state + removes from localStorage |
| **Route Guard** | `App.jsx` renders `<Login>` if `user` is `null` |

> **Note:** Login and signup are currently placeholder implementations. Real credential verification against a backend database is planned for a future sprint.

---

## Styling & Theme

### Current Theme — **Neon Cyberpunk (Violet / Pink)**

The theme was updated from the original Indigo/Cyan palette to a more vibrant Neon Cyberpunk aesthetic:

| Token | Old Value | New Value |
|---|---|---|
| `--primary-500` | `#6366f1` (Indigo) | `#8b5cf6` (Violet) |
| `--primary-600` | `#4f46e5` | `#7c3aed` |
| `--accent-*` (cyan) | `#06b6d4` | `#ec4899` (Neon Pink) |
| `--accent-*` (emerald) | `#10b981` | `#14b8a6` (Bright Teal) |
| `--accent-*` (rose) | `#f43f5e` | `#ef4444` (Bright Red) |
| `--bg-base` | `#0a0e1a` (Navy) | `#0f0e17` (Midnight Purple) |
| `--bg-surface` | `#111827` | `#1a1625` |
| `--bg-elevated` | `#1e2538` | `#2d2438` |
| Body gradient (top) | `rgba(99, 102, 241, ...)` | `rgba(139, 92, 246, ...)` |
| Body gradient (bottom) | `rgba(6, 182, 212, ...)` | `rgba(236, 72, 153, ...)` |

### Previous Theme — **Space Indigo / Cyan**
Original dark theme built around indigo (`#6366f1`) primaries and cyan (`#06b6d4`) accents on a deep navy (`#0a0e1a`) base.

---

## Design System

**File:** [`src/styles/index.css`](src/styles/index.css)

All styling is built on a CSS custom properties (variables) design system. No external CSS framework is used.

### Color Tokens
```css
--primary-50 / --primary-500 / --primary-600 / --primary-900
--accent-pink / --accent-teal / --accent-red
--bg-base / --bg-surface / --bg-elevated / --bg-card / --bg-input
--border-subtle
--text-primary / --text-secondary / --text-muted
```

### Spacing Scale
```css
--sp-1: 4px   --sp-2: 8px   --sp-3: 12px  --sp-4: 16px
--sp-5: 20px  --sp-6: 24px  --sp-8: 32px  --sp-10: 40px
```

### Border Radius
```css
--radius-sm: 6px   --radius-md: 10px
--radius-lg: 16px  --radius-xl: 24px  --radius-full: 9999px
```

### Animations
| Keyframe | Effect |
|---|---|
| `fadeIn` | Fade up from 8px below |
| `float` | Gentle 6px vertical bob (6–8s loop) |
| `pulse` | Opacity pulse 1 → 0.6 (2s loop) |
| `spin` | 360° rotation (used for loading spinner) |

### Visual Techniques
- **Glassmorphism** — `backdrop-filter: blur()` + semi-transparent `rgba` backgrounds
- **Gradient borders** — `::before` pseudo-elements with `linear-gradient` + `z-index: -1`
- **Glow shadows** — `box-shadow` with primary color and opacity
- **Animated background orbs** — Large blurred circles with `float` animation on `::before`/`::after`
- **Dot-grid overlay** — Repeating `linear-gradient` pattern at low opacity

---

## Getting Started

### Prerequisites
- Node.js 18+
- npm or yarn

### Installation

```bash
# Clone the repository
git clone <repo-url>
cd Frontend

# Install dependencies
npm install
```

### Run Development Server

```bash
npm run dev
```

The app will be available at `http://localhost:5173`.

### Build for Production

```bash
npm run build
```

---

## Scripts

| Command | Description |
|---|---|
| `npm run dev` | Start Vite dev server with HMR |
| `npm run build` | Production build to `dist/` |
| `npm run preview` | Preview the production build locally |
| `npm run lint` | Run oxlint code linter |

---

## Planned / Upcoming

- [ ] Backend API integration for real authentication (login / signup)
- [ ] Database storage for registered missing persons
- [ ] Live camera feed connection via mobile streaming module
- [ ] AI facial recognition module integration
- [ ] Real-time detection alerts populated from AI scan results
- [ ] Settings page
- [ ] Live Feeds management page
- [ ] Role-based access control (Admin vs Operator)
- [ ] Search and filter across the missing persons database

---

> **Project Status:** 🚧 Active Development — Frontend scaffold complete, backend integration pending.

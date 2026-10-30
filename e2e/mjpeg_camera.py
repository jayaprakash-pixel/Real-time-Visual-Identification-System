"""Fake phone camera: serves a video file as an MJPEG stream (like the IP Webcam app) on /video.
   python mjpeg_camera.py <video.mp4> <port>"""
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import cv2

path, port = sys.argv[1], int(sys.argv[2])


class H(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=frame")
        self.end_headers()
        cap = cv2.VideoCapture(path)
        try:
            while True:
                ok, frame = cap.read()
                if not ok:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue
                jpg = cv2.imencode(".jpg", frame)[1].tobytes()
                self.wfile.write(b"--frame\r\nContent-Type: image/jpeg\r\nContent-Length: %d\r\n\r\n" % len(jpg) + jpg + b"\r\n")
                time.sleep(1 / 15)
        except (BrokenPipeError, ConnectionResetError, OSError):
            pass
        finally:
            cap.release()

    def log_message(self, *a):
        pass


ThreadingHTTPServer(("127.0.0.1", port), H).serve_forever()

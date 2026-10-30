"""Minimal HTTP service used to demonstrate the build and deploy pipeline.

Standard library only, so the image stays small and has no dependencies to patch.
"""

import json
import os
import signal
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

VERSION = os.environ.get("APP_VERSION", "dev")


def route(path):
    """Return (status, body) for a request path."""
    if path == "/health":
        return 200, {"status": "ok"}
    if path == "/":
        return 200, {"service": "aws-oidc-deploy-demo", "version": VERSION}
    return 404, {"error": "not found"}


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        status, body = route(self.path.split("?", 1)[0])
        payload = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, fmt, *args):
        # One line per request on stdout, which is what container log drivers expect.
        sys.stdout.write("%s %s\n" % (self.address_string(), fmt % args))
        sys.stdout.flush()


def main():
    port = int(os.environ.get("PORT", "8080"))
    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    # Exit cleanly on SIGTERM so ECS/Kubernetes rollouts don't wait for the kill timeout.
    # server.shutdown() would deadlock here: it waits for serve_forever(), which runs
    # in this same thread. Raising SystemExit unwinds serve_forever() instead.
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))
    print(f"listening on :{port} (version {VERSION})", flush=True)
    try:
        server.serve_forever()
    finally:
        server.server_close()
        print("stopped", flush=True)


if __name__ == "__main__":
    main()

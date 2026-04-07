"""
server.py — Lightweight Dashboard Server
=========================================
Serves the generated HTML dashboard via a simple HTTP server.
Also exposes a /api/stats endpoint for programmatic access.

Usage:
    python server.py                  # Serve on port 8080
    python server.py --port 3000      # Custom port
"""

import argparse
import json
import logging
import sys
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from functools import partial

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent


class DashboardHandler(SimpleHTTPRequestHandler):
    """Custom handler that serves the dashboard and provides a simple API."""

    def __init__(self, *args, data_dir: Path = None, **kwargs):
        self.data_dir = data_dir or PROJECT_ROOT / "data" / "processed"
        super().__init__(*args, directory=str(PROJECT_ROOT / "visualization"), **kwargs)

    def do_GET(self):
        self._handle_all()

    def do_HEAD(self):
        self._handle_all()

    def _handle_all(self):
        # Health check for monitoring
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            if self.command == "GET":
                self.wfile.write(json.dumps({"status": "ok"}).encode())
            return

        # Serve static files or API
        if self.path == "/api/stats":
            self._serve_json("stats.json")
            return

        if self.command == "GET":
            super().do_GET()
        else:
            super().do_HEAD()

    def _serve_json(self, filename: str):
        filepath = self.data_dir / filename
        if filepath.exists():
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(filepath.read_bytes())
        else:
            self.send_error(404, f"Data file not found: {filename}")

    def log_message(self, format, *args):
        logger.info(f"  {args[0]}")


def run_server(port: int = 8080):
    """Start the dashboard HTTP server."""
    handler = partial(
        DashboardHandler,
        data_dir=PROJECT_ROOT / "data" / "processed",
    )

    server = HTTPServer(("0.0.0.0", port), handler)

    print("")
    print("╔══════════════════════════════════════════════════════════╗")
    print("║   📊 Tech Layoff Dashboard Server                      ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print("")
    print(f"   🌐 Dashboard:  http://localhost:{port}/layoff_chart.html")
    print(f"   📡 API Stats:  http://localhost:{port}/api/stats")
    print(f"   ❤️  Health:     http://localhost:{port}/health")
    print("")
    print("   Press Ctrl+C to stop.")
    print("")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Server stopped.")
        server.server_close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    parser = argparse.ArgumentParser(description="Serve the layoff dashboard")
    parser.add_argument("--port", "-p", type=int, default=8080, help="Port (default: 8080)")
    args = parser.parse_args()

    run_server(port=args.port)

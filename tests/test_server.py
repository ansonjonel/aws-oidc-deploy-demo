import json
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

from app.server import Handler, route


class RouteTest(unittest.TestCase):
    def test_health(self):
        self.assertEqual(route("/health"), (200, {"status": "ok"}))

    def test_root_reports_version(self):
        status, body = route("/")
        self.assertEqual(status, 200)
        self.assertIn("version", body)

    def test_unknown_path(self):
        self.assertEqual(route("/nope")[0], 404)


class ServerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        cls.port = cls.server.server_address[1]
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def get(self, path):
        return urllib.request.urlopen(f"http://127.0.0.1:{self.port}{path}", timeout=5)

    def test_health_over_http(self):
        with self.get("/health?probe=1") as resp:
            self.assertEqual(resp.status, 200)
            self.assertEqual(resp.headers["Content-Type"], "application/json")
            self.assertEqual(json.load(resp), {"status": "ok"})

    def test_404_over_http(self):
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            self.get("/missing")
        self.assertEqual(ctx.exception.code, 404)


if __name__ == "__main__":
    unittest.main()

import unittest
from app import flask_app


class TestApp(unittest.TestCase):
    def setUp(self):
        self.app = flask_app.test_client()
        self.app.testing = True

    def test_hello(self):
        response = self.app.get("/api/hello")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {"hello": "world"})

    def test_goodbye(self):
        response = self.app.get("/api/goodbye")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {"goodbye": "world"})

    # Füge weitere Tests hinzu
    def test_invalid_endpoint(self):
        response = self.app.get("/api/invalid")
        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()

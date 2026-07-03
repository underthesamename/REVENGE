import unittest
from unittest.mock import Mock

from modules.base import DiscordWorker, clean_discord_token


class RecordingSession:
    def __init__(self):
        self.headers = {"Content-Type": "application/json"}
        self.last_headers = None

    def request(self, method, url, timeout=30, **kwargs):
        self.last_headers = dict(kwargs.get("headers", self.headers))
        return Mock(status_code=204, content=b"")


class DiscordWorkerTests(unittest.TestCase):
    def test_clean_token_removes_wrapping_quotes(self):
        self.assertEqual("abc.def.ghi", clean_discord_token('"abc.def.ghi"'))

    def test_clean_token_rejects_log_output(self):
        bad_token = (
            "[13:20:44] Friend removal stopped: Discord API returned 400\n"
            "[13:20:44] Ready."
        )

        with self.assertRaisesRegex(ValueError, "no spaces or line breaks"):
            clean_discord_token(bad_token)

    def test_session_does_not_default_to_json_content_type(self):
        worker = DiscordWorker("token", dry_run=False)

        self.assertNotIn("Content-Type", worker.session.headers)

    def test_delete_requests_do_not_send_json_content_type_without_body(self):
        worker = DiscordWorker("token", dry_run=False)
        worker.session = RecordingSession()

        worker.request("DELETE", "/users/@me/relationships/123")

        self.assertNotIn("Content-Type", worker.session.last_headers)

    def test_query_params_do_not_count_as_json_body(self):
        worker = DiscordWorker("token", dry_run=False)
        worker.session = RecordingSession()

        worker.request("POST", "/users/@me/channels", params={"limit": 100})

        self.assertNotIn("Content-Type", worker.session.last_headers)

    def test_json_body_keeps_json_content_type(self):
        worker = DiscordWorker("token", dry_run=False)
        worker.session = RecordingSession()

        worker.request("POST", "/users/@me/channels", json={})

        self.assertEqual("application/json", worker.session.last_headers["Content-Type"])


if __name__ == "__main__":
    unittest.main()

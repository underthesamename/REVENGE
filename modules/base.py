import time

import requests
from PyQt5.QtCore import QObject, pyqtSignal


def clean_discord_token(token):
    token = (token or "").strip()
    if len(token) >= 2 and token[0] == token[-1] and token[0] in {"'", '"'}:
        token = token[1:-1].strip()

    if not token:
        return ""

    if any(character.isspace() for character in token):
        raise ValueError(
            "Token must be a single value with no spaces or line breaks. "
            "Clear the token field and paste only the Discord token."
        )

    if any(ord(character) < 32 or ord(character) == 127 for character in token):
        raise ValueError("Token contains unsupported control characters.")

    return token


class DiscordWorker(QObject):
    status = pyqtSignal(str)
    progress = pyqtSignal(int, int)
    finished = pyqtSignal()

    API_BASE = "https://discord.com/api/v10"
    SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}

    def __init__(self, token, dry_run=True):
        super().__init__()
        self.token = clean_discord_token(token)
        self.dry_run = bool(dry_run)
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": self.token,
                "User-Agent": "discord-cleaner-local/1.0",
            }
        )

    def request(self, method, path, **kwargs):
        if not self.token:
            raise RuntimeError("Discord token is not configured.")

        method = method.upper()
        if self.dry_run and method not in self.SAFE_METHODS:
            return None

        headers = dict(self.session.headers)
        has_body = any(kwargs.get(key) is not None for key in {"data", "json"})
        if method in self.SAFE_METHODS or method == "DELETE" or not has_body:
            headers.pop("Content-Type", None)
        else:
            headers.setdefault("Content-Type", "application/json")

        kwargs = {**kwargs, "headers": headers}

        url = path if path.startswith("http") else f"{self.API_BASE}{path}"
        for _ in range(8):
            response = self.session.request(method, url, timeout=30, **kwargs)

            if response.status_code == 429:
                retry_after = self._retry_after(response)
                self.status.emit(f"Rate limited. Waiting {retry_after:.1f}s.")
                time.sleep(max(retry_after, 0.5))
                continue

            if response.status_code in {204, 404}:
                return None

            if response.status_code >= 400:
                detail = response.text.strip().replace("\n", " ")
                if len(detail) > 240:
                    detail = f"{detail[:237]}..."
                raise RuntimeError(f"Discord API returned {response.status_code}: {detail}")

            if not response.content:
                return None

            try:
                return response.json()
            except ValueError:
                return response.text

        raise RuntimeError("Discord API kept rate limiting this operation.")

    def _retry_after(self, response):
        try:
            return float(response.json().get("retry_after", 1.0))
        except (TypeError, ValueError):
            try:
                return float(response.headers.get("Retry-After", 1.0))
            except (TypeError, ValueError):
                return 1.0

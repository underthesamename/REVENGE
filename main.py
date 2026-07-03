import sys
import json
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QThread
from modules.base import clean_discord_token
from modules.cleaner import ConversationCleaner
from modules.friend_remover import FriendRemover
from modules.guild_leaver import GuildLeaver
from ui.main_window import UIMainWindow


class MainController:
    DEFAULT_CONFIG = {
        "token": "",
        "remember_token": False,
        "dry_run": True,
    }

    def __init__(self):
        self.token = None
        self.dry_run = True
        self.config = {}
        self.active_threads = []
        self.active_workers = []
        self.load_config()

    def load_config(self):
        try:
            with open("config.json", "r", encoding="utf-8") as f:
                content = f.read().strip()
            loaded_config = json.loads(content) if content else {}
            if not isinstance(loaded_config, dict):
                loaded_config = {}
        except (FileNotFoundError, json.JSONDecodeError):
            loaded_config = {}

        self.config = self.DEFAULT_CONFIG.copy()
        self.config.update(loaded_config)

        if not self.config.get("remember_token"):
            self.config["token"] = ""
            self.save_config()

        try:
            self.token = clean_discord_token(self.config.get("token", ""))
        except ValueError:
            self.token = ""
            self.config["token"] = ""
            self.config["remember_token"] = False
            self.save_config()
        self.dry_run = bool(self.config.get("dry_run", True))

    def save_config(self):
        with open("config.json", "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=2)

    def set_token(self, token, remember_token=False):
        self.token = clean_discord_token(token)
        self.config["remember_token"] = bool(remember_token)
        self.config["token"] = self.token if remember_token else ""
        self.save_config()

    def set_dry_run(self, dry_run):
        self.dry_run = bool(dry_run)
        self.config["dry_run"] = self.dry_run
        self.save_config()

    def _require_token(self):
        if not self.token:
            raise ValueError("Add your Discord token before starting an action.")

    def _start_worker(self, worker):
        thread = QThread()
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(lambda: self._discard_worker(thread, worker))
        self.active_threads.append(thread)
        self.active_workers.append(worker)
        thread.start()
        return worker

    def _discard_worker(self, thread, worker):
        if thread in self.active_threads:
            self.active_threads.remove(thread)
        if worker in self.active_workers:
            self.active_workers.remove(worker)

    def start_cleaner(self, days_to_keep, conversation_query, dry_run=None, max_messages=100):
        self._require_token()
        dry_run = self.dry_run if dry_run is None else bool(dry_run)
        return self._start_worker(
            ConversationCleaner(self.token, days_to_keep, conversation_query, dry_run, max_messages)
        )

    def remove_friends(self, dry_run=None, max_items=100):
        self._require_token()
        dry_run = self.dry_run if dry_run is None else bool(dry_run)
        return self._start_worker(FriendRemover(self.token, dry_run, max_items))

    def leave_all_guilds(self, dry_run=None, max_items=100):
        self._require_token()
        dry_run = self.dry_run if dry_run is None else bool(dry_run)
        return self._start_worker(GuildLeaver(self.token, dry_run, max_items))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = UIMainWindow()
    controller = MainController()
    window.controller = controller
    window.show()
    sys.exit(app.exec_())

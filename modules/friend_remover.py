import time

from .base import DiscordWorker


class FriendRemover(DiscordWorker):
    def __init__(self, token, dry_run=True, max_items=100):
        super().__init__(token, dry_run)
        self.max_items = max(int(max_items or 1), 1)

    def run(self):
        try:
            self._run()
        except Exception as exc:
            self.status.emit(f"Friend removal stopped: {exc}")
        finally:
            self.finished.emit()

    def _run(self):
        relationships = self.request("GET", "/users/@me/relationships") or []
        friends = [relationship for relationship in relationships if relationship.get("type") == 1]
        total = len(friends)
        affected = 0

        if self.dry_run:
            self.status.emit("Dry run enabled. No friends will be removed.")
        self.status.emit(f"Found {total} friend(s).")
        for index, relationship in enumerate(friends, start=1):
            if affected >= self.max_items:
                self.status.emit(f"Limit reached ({self.max_items} friend(s)).")
                break

            user = relationship.get("user") or {}
            user_id = user.get("id")
            if not user_id:
                continue

            name = user.get("global_name") or user.get("username") or user_id
            action = "Would remove" if self.dry_run else "Removing"
            self.status.emit(f"{action} {name}.")
            self.request("DELETE", f"/users/@me/relationships/{user_id}")
            affected += 1
            self.progress.emit(affected, self.max_items)
            time.sleep(0.5)

        action = "Would remove" if self.dry_run else "Removed"
        self.status.emit(f"Finished. {action} {affected} friend(s).")

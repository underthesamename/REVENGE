import time

from .base import DiscordWorker


class GuildLeaver(DiscordWorker):
    def __init__(self, token, dry_run=True, max_items=100):
        super().__init__(token, dry_run)
        self.max_items = max(int(max_items or 1), 1)

    def run(self):
        try:
            self._run()
        except Exception as exc:
            self.status.emit(f"Server leaving stopped: {exc}")
        finally:
            self.finished.emit()

    def _run(self):
        guilds = self.request("GET", "/users/@me/guilds") or []
        total = len(guilds)
        affected = 0

        if self.dry_run:
            self.status.emit("Dry run enabled. No servers will be left.")
        self.status.emit(f"Found {total} server(s).")
        for index, guild in enumerate(guilds, start=1):
            if affected >= self.max_items:
                self.status.emit(f"Limit reached ({self.max_items} server(s)).")
                break

            guild_id = guild.get("id")
            if not guild_id:
                continue

            name = guild.get("name") or guild_id
            if guild.get("owner"):
                self.status.emit(f"Skipping owned server: {name}.")
                self.progress.emit(index, total)
                continue

            action = "Would leave" if self.dry_run else "Leaving"
            self.status.emit(f"{action} {name}.")
            self.request("DELETE", f"/users/@me/guilds/{guild_id}")
            affected += 1
            self.progress.emit(affected, self.max_items)
            time.sleep(0.5)

        action = "Would leave" if self.dry_run else "Left"
        self.status.emit(f"Finished. {action} {affected} server(s).")

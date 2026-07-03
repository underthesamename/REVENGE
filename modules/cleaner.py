import time
import re
from datetime import datetime, timedelta, timezone

from .base import DiscordWorker


class ConversationCleaner(DiscordWorker):
    def __init__(self, token, days_to_keep, conversation_query, dry_run=True, max_messages=100):
        super().__init__(token, dry_run)
        self.days_to_keep = max(int(days_to_keep), 0)
        self.conversation_query = (conversation_query or "").strip()
        self.normalized_query = self.conversation_query.lower()
        self.query_ids = set(re.findall(r"\d{15,25}", self.conversation_query))
        self.max_messages = max(int(max_messages or 1), 1)

    def run(self):
        try:
            self._run()
        except Exception as exc:
            self.status.emit(f"Cleaner stopped: {exc}")
        finally:
            self.finished.emit()

    def _run(self):
        me = self.request("GET", "/users/@me") or {}
        user_id = str(me.get("id", ""))
        if not user_id:
            raise RuntimeError("Could not identify the account for this token.")

        if not self.conversation_query:
            raise RuntimeError("Choose a conversation before cleaning.")

        channels = self.request("GET", "/users/@me/channels") or []
        channels = [channel for channel in channels if self._matches_channel(channel)]
        if not channels:
            raise RuntimeError(f"No private channel matched '{self.conversation_query}'.")
        if len(channels) > 1:
            exact_matches = [channel for channel in channels if self._is_exact_match(channel)]
            if len(exact_matches) == 1:
                channels = exact_matches
            else:
                matches = ", ".join(self._channel_name(channel) for channel in channels[:5])
                raise RuntimeError(f"Multiple private channels matched. Use the channel ID. Matches: {matches}")

        cutoff = self._cutoff()
        affected = 0

        if self.dry_run:
            self.status.emit("Dry run enabled. No messages will be deleted.")
        self.status.emit(f"Matched {len(channels)} private channel(s).")
        for channel in channels:
            channel_id = channel.get("id")
            if not channel_id:
                continue

            self.status.emit(f"Scanning {self._channel_name(channel)}.")
            before = None
            while True:
                params = {"limit": 100}
                if before:
                    params["before"] = before

                messages = self.request("GET", f"/channels/{channel_id}/messages", params=params) or []
                if not messages:
                    break

                before = messages[-1].get("id")
                for message in messages:
                    author = message.get("author") or {}
                    if str(author.get("id", "")) != user_id:
                        continue

                    created_at = self._parse_timestamp(message.get("timestamp"))
                    if cutoff and created_at and created_at >= cutoff:
                        continue

                    message_id = message.get("id")
                    if not message_id:
                        continue

                    if affected >= self.max_messages:
                        self.status.emit(f"Limit reached ({self.max_messages} message(s)).")
                        self._finish(affected)
                        return

                    self.request("DELETE", f"/channels/{channel_id}/messages/{message_id}")
                    affected += 1
                    self.progress.emit(affected, self.max_messages)
                    time.sleep(0.25)

                if len(messages) < 100 or not before:
                    break

        self._finish(affected)

    def _cutoff(self):
        if self.days_to_keep <= 0:
            return None
        return datetime.now(timezone.utc) - timedelta(days=self.days_to_keep)

    def _parse_timestamp(self, value):
        if not value:
            return None
        return datetime.fromisoformat(value.replace("Z", "+00:00"))

    def _channel_name(self, channel):
        if channel.get("name"):
            return channel["name"]
        recipients = channel.get("recipients") or []
        names = [recipient.get("username") for recipient in recipients if recipient.get("username")]
        return ", ".join(names) if names else f"channel {channel.get('id', 'unknown')}"

    def _matches_channel(self, channel):
        channel_id = str(channel.get("id", ""))
        if channel_id in self.query_ids or channel_id == self.conversation_query:
            return True

        searchable = [channel_id, channel.get("name", "")]
        for recipient in channel.get("recipients") or []:
            searchable.extend(
                [
                    recipient.get("id", ""),
                    recipient.get("username", ""),
                    recipient.get("global_name", ""),
                    recipient.get("display_name", ""),
                ]
            )

        for value in searchable:
            value = str(value or "").lower()
            if not value:
                continue
            if self.normalized_query == value or self.normalized_query in value:
                return True

        return False

    def _is_exact_match(self, channel):
        channel_id = str(channel.get("id", ""))
        if channel_id in self.query_ids or channel_id == self.conversation_query:
            return True

        exact_values = [channel_id, channel.get("name", "")]
        for recipient in channel.get("recipients") or []:
            exact_values.extend(
                [
                    recipient.get("id", ""),
                    recipient.get("username", ""),
                    recipient.get("global_name", ""),
                    recipient.get("display_name", ""),
                ]
            )

        return any(self.normalized_query == str(value or "").lower() for value in exact_values)

    def _finish(self, affected):
        action = "Would delete" if self.dry_run else "Deleted"
        self.status.emit(f"Finished. {action} {affected} message(s).")

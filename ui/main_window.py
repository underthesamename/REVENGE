from datetime import datetime
from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont, QPainter
from PyQt5.QtWidgets import (
    QCheckBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)


class GlitchLogo(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("AsciiLogoFrame")
        self.setMinimumHeight(210)
        self.logo_lines = self._load_ascii_logo().splitlines()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.logo_canvas = AsciiLogoCanvas(self.logo_lines)
        layout.addWidget(self.logo_canvas, stretch=1)

        self.subtitle_label = QLabel("@sxsui on discord")
        self.subtitle_label.setObjectName("LogoSubtitle")
        self.subtitle_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.subtitle_label)

    def _load_ascii_logo(self):
        logo_path = Path(__file__).resolve().parents[1] / "assets" / "logo_ascii.txt"
        try:
            return logo_path.read_text(encoding="utf-8").strip("\n")
        except OSError:
            return "SUI TOOLS"


class AsciiLogoCanvas(QWidget):
    def __init__(self, lines, parent=None):
        super().__init__(parent)
        self.lines = [line.rstrip() for line in lines if line.strip()] or ["REVENGE"]
        self.setMinimumHeight(175)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.TextAntialiasing, False)
        painter.fillRect(self.rect(), QColor("#000000"))

        font = QFont("Consolas", self._font_size(), QFont.Bold)
        font.setStyleHint(QFont.Monospace)
        font.setStyleStrategy(QFont.NoAntialias)
        painter.setFont(font)

        metrics = painter.fontMetrics()
        line_height = metrics.height() - 1
        char_width = max(1, metrics.horizontalAdvance("█"))
        logo_width = max(metrics.horizontalAdvance(line) for line in self.lines)
        x = max(0, (self.width() - logo_width) // 2)
        y = 14 + metrics.ascent()

        self._draw_blood_drips(painter, x, y, char_width, line_height)
        layers = (
            (QColor(18, 2, 5, 245), 6, 7),
            (QColor(57, 8, 16, 230), -3, 3),
            (QColor(88, 13, 24, 215), 3, 2),
            (QColor("#8f1828"), 0, 0),
            (QColor(190, 44, 58, 135), 1, -1),
        )
        for color, dx, dy in layers:
            painter.setPen(color)
            for index, line in enumerate(self.lines):
                painter.drawText(x + dx, y + index * line_height + dy, line)
        self._draw_top_gloss(painter, x, y, line_height)

    def _font_size(self):
        longest = max(len(line) for line in self.lines)
        if longest <= 0:
            return 10
        return max(8, min(14, (self.width() - 24) // longest + 1))

    def _draw_blood_drips(self, painter, x, y, char_width, line_height):
        painter.setPen(Qt.NoPen)
        body_bottom = y + (len(self.lines) - 1) * line_height + 3
        columns = self._drip_columns()
        for order, column in enumerate(columns):
            height = 20 + ((column * 17 + order * 11) % 68)
            width = max(3, char_width // 3)
            drip_x = x + column * char_width + char_width // 2
            if order % 5 == 0:
                height += 26
            if order % 7 == 0:
                width += 2

            painter.fillRect(drip_x - width // 2, body_bottom - 4, width + 3, 7, QColor(74, 9, 18, 220))
            painter.fillRect(drip_x + 3, body_bottom + 5, width + 2, height, QColor(18, 2, 5, 210))
            painter.fillRect(drip_x, body_bottom, width, height, QColor(96, 13, 25, 235))
            painter.fillRect(drip_x + max(1, width // 2), body_bottom, 1, max(10, height - 8), QColor(172, 31, 45, 145))

            for speck in range(3):
                speck_x = drip_x + ((column * (speck + 3) + order) % 17) - 8
                speck_y = body_bottom + height - 12 + ((column + speck * 9) % 22)
                speck_size = 1 + ((column + speck) % 2)
                painter.fillRect(speck_x, speck_y, speck_size, speck_size + 1, QColor(128, 17, 30, 160))

            if order % 3 == 0:
                drop_size = max(5, width + 3)
                painter.setBrush(QColor(76, 8, 17, 235))
                painter.drawEllipse(drip_x - 1, body_bottom + height - 1, drop_size, drop_size + 2)
                painter.setBrush(QColor(151, 24, 38, 130))
                painter.drawEllipse(drip_x, body_bottom + height, max(2, drop_size - 2), max(2, drop_size - 1))

    def _drip_columns(self):
        columns = []
        max_width = max(len(line) for line in self.lines)
        for column in range(max_width):
            lower_body = any(column < len(line) and line[column] != " " for line in self.lines[2:])
            if lower_body and (column * 7 + max_width) % 9 in {0, 3, 6}:
                columns.append(column)
        return columns

    def _draw_top_gloss(self, painter, x, y, line_height):
        painter.setPen(QColor(204, 52, 62, 85))
        for index, line in enumerate(self.lines[:2]):
            painter.drawText(x, y + index * line_height - 2, line)


class UIMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._controller = None
        self.setWindowTitle("REVENGE | @sxsui on discord")
        self.setMinimumSize(660, 620)
        self.resize(700, 660)
        self._build_ui()
        self._apply_style()

    @property
    def controller(self):
        return self._controller

    @controller.setter
    def controller(self, value):
        self._controller = value
        if value and getattr(value, "token", None):
            self.token_input.setText(value.token)
        if value:
            self.remember_token_checkbox.setChecked(bool(value.config.get("remember_token", False)))
            self.dry_run_checkbox.setChecked(bool(value.config.get("dry_run", True)))

    def _build_ui(self):
        root = QWidget()
        root.setObjectName("Root")
        page = QVBoxLayout(root)
        page.setContentsMargins(12, 12, 12, 12)
        page.setSpacing(0)

        shell = QFrame()
        shell.setObjectName("Shell")
        layout = QVBoxLayout(shell)
        layout.setContentsMargins(18, 16, 18, 18)
        layout.setSpacing(12)

        layout.addWidget(GlitchLogo())

        form = QFrame()
        form.setObjectName("Panel")
        form_layout = QGridLayout(form)
        form_layout.setContentsMargins(14, 12, 14, 12)
        form_layout.setHorizontalSpacing(10)
        form_layout.setVerticalSpacing(10)

        token_label = QLabel("token")
        token_label.setObjectName("FieldLabel")
        form_layout.addWidget(token_label, 0, 0)

        self.token_input = QLineEdit()
        self.token_input.setEchoMode(QLineEdit.Password)
        self.token_input.setPlaceholderText("discord token")
        form_layout.addWidget(self.token_input, 0, 1)

        save_button = QPushButton("save")
        save_button.setObjectName("AccentButton")
        save_button.setFixedHeight(34)
        save_button.clicked.connect(self._save_token)
        form_layout.addWidget(save_button, 0, 2)

        store_label = QLabel("store")
        store_label.setObjectName("FieldLabel")
        form_layout.addWidget(store_label, 1, 0)

        self.remember_token_checkbox = QCheckBox("remember token")
        self.remember_token_checkbox.setChecked(False)
        form_layout.addWidget(self.remember_token_checkbox, 1, 1, 1, 2)

        target_label = QLabel("dm")
        target_label.setObjectName("FieldLabel")
        form_layout.addWidget(target_label, 2, 0)

        self.conversation_input = QLineEdit()
        self.conversation_input.setPlaceholderText("channel id / username / group name")
        form_layout.addWidget(self.conversation_input, 2, 1, 1, 2)

        keep_label = QLabel("keep")
        keep_label.setObjectName("FieldLabel")
        form_layout.addWidget(keep_label, 3, 0)

        self.days_spin = QSpinBox()
        self.days_spin.setRange(0, 3650)
        self.days_spin.setValue(30)
        self.days_spin.setSuffix(" days")
        form_layout.addWidget(self.days_spin, 3, 1, 1, 2)

        limit_label = QLabel("limit")
        limit_label.setObjectName("FieldLabel")
        form_layout.addWidget(limit_label, 4, 0)

        self.limit_spin = QSpinBox()
        self.limit_spin.setRange(1, 10000)
        self.limit_spin.setValue(100)
        self.limit_spin.setSuffix(" items")
        form_layout.addWidget(self.limit_spin, 4, 1, 1, 2)

        mode_label = QLabel("mode")
        mode_label.setObjectName("FieldLabel")
        form_layout.addWidget(mode_label, 5, 0)

        self.dry_run_checkbox = QCheckBox("dry run")
        self.dry_run_checkbox.setChecked(True)
        form_layout.addWidget(self.dry_run_checkbox, 5, 1)

        self.confirm_input = QLineEdit()
        self.confirm_input.setPlaceholderText("CLEAR / FRIENDS / LEAVE")
        form_layout.addWidget(self.confirm_input, 5, 2)
        form_layout.setColumnStretch(1, 1)

        layout.addWidget(form)

        action_row = QHBoxLayout()
        action_row.setSpacing(10)
        self.clean_button = QPushButton("clean selected")
        self.clean_button.clicked.connect(self._clean_conversations)
        action_row.addWidget(self.clean_button)

        self.friends_button = QPushButton("remove friends")
        self.friends_button.clicked.connect(self._remove_friends)
        action_row.addWidget(self.friends_button)

        self.guilds_button = QPushButton("leave servers")
        self.guilds_button.clicked.connect(self._leave_servers)
        action_row.addWidget(self.guilds_button)
        layout.addLayout(action_row)

        self.progress = QProgressBar()
        self.progress.setRange(0, 1)
        self.progress.setValue(0)
        self.progress.setFormat("%p%")
        layout.addWidget(self.progress)

        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        layout.addWidget(self.log, stretch=1)

        page.addWidget(shell)
        self.setCentralWidget(root)
        self._log("Ready.")

    def _apply_style(self):
        self.setStyleSheet(
            """
            QMainWindow, QWidget#Root {
                background: #000000;
                color: #f0c7c5;
                font-family: Consolas, Courier New, monospace;
                font-size: 12px;
            }

            QFrame#Shell {
                background: #000000;
                border: 1px solid #3d0710;
            }

            QFrame#Panel {
                background: #070102;
                border: 1px solid #4c0a15;
            }

            QFrame#AsciiLogoFrame {
                background: #000000;
                border: 0;
            }

            QLabel#LogoSubtitle {
                color: #c66b70;
                background: transparent;
                font-family: Consolas, Courier New, monospace;
                font-size: 12px;
                padding-top: 2px;
            }

            QLabel#FieldLabel {
                color: #a91b2d;
                font-weight: bold;
                letter-spacing: 0px;
            }

            QLineEdit, QSpinBox, QPlainTextEdit {
                background: #020000;
                border: 1px solid #5f0d1a;
                color: #d99a9d;
                selection-background-color: #6d101e;
                padding: 7px;
            }

            QLineEdit:focus, QSpinBox:focus, QPlainTextEdit:focus {
                border: 1px solid #a91b2d;
            }

            QLineEdit::placeholder {
                color: #6f3439;
            }

            QPushButton {
                background: #0b0103;
                border: 1px solid #5f0d1a;
                color: #d99a9d;
                min-height: 34px;
                padding: 8px 12px;
            }

            QPushButton:hover {
                background: #180308;
                border-color: #a91b2d;
                color: #f0b3b5;
            }

            QPushButton:pressed {
                background: #000000;
                color: #a91b2d;
            }

            QPushButton:disabled {
                background: #050101;
                border-color: #25050a;
                color: #54262b;
            }

            QPushButton#AccentButton {
                color: #bd3140;
            }

            QCheckBox {
                color: #d99a9d;
                spacing: 8px;
            }

            QCheckBox::indicator {
                width: 14px;
                height: 14px;
                background: #020000;
                border: 1px solid #5f0d1a;
            }

            QCheckBox::indicator:checked {
                background: #8f1828;
                border: 1px solid #bd3140;
            }

            QProgressBar {
                background: #020000;
                border: 1px solid #5f0d1a;
                color: #d99a9d;
                height: 16px;
                text-align: center;
            }

            QProgressBar::chunk {
                background: #8f1828;
            }

            QPlainTextEdit {
                line-height: 130%;
            }
            """
        )

    def _sync_settings(self, require_token=True):
        if not self._controller:
            QMessageBox.warning(self, "Missing Controller", "Controller is not ready yet.")
            return False

        token = self.token_input.text().strip()
        if require_token and not token:
            QMessageBox.warning(self, "Missing Token", "Enter a token first.")
            return False

        remember_token = self.remember_token_checkbox.isChecked()
        try:
            self._controller.set_token(token, remember_token)
        except ValueError as exc:
            QMessageBox.warning(self, "Invalid Token", str(exc))
            return False
        self._controller.set_dry_run(self.dry_run_checkbox.isChecked())
        return True

    def _save_token(self):
        if not self._sync_settings():
            return False

        if self.remember_token_checkbox.isChecked():
            self._log("Token saved to config.")
        else:
            self._log("Token loaded for this session only.")
        return True

    def _clean_conversations(self):
        if not self._sync_settings():
            return
        days = self.days_spin.value()
        conversation = self.conversation_input.text().strip()
        if not conversation:
            QMessageBox.warning(self, "Missing Conversation", "Enter a channel ID, username, or group name first.")
            return

        if not self._live_action_allowed("CLEAR"):
            return

        dry_run = self.dry_run_checkbox.isChecked()
        limit = self.limit_spin.value()
        mode = "Dry run" if dry_run else "LIVE"
        message = f"{mode}: clean up to {limit} message(s) from '{conversation}'?"
        if self._confirm("Clean Conversation", message):
            self._start_worker(self._controller.start_cleaner(days, conversation, dry_run, limit))

    def _remove_friends(self):
        if not self._sync_settings():
            return
        if not self._live_action_allowed("FRIENDS"):
            return

        dry_run = self.dry_run_checkbox.isChecked()
        limit = self.limit_spin.value()
        mode = "Dry run" if dry_run else "LIVE"
        if self._confirm("Remove Friends", f"{mode}: remove up to {limit} friend(s)?"):
            self._start_worker(self._controller.remove_friends(dry_run, limit))

    def _leave_servers(self):
        if not self._sync_settings():
            return
        if not self._live_action_allowed("LEAVE"):
            return

        dry_run = self.dry_run_checkbox.isChecked()
        limit = self.limit_spin.value()
        mode = "Dry run" if dry_run else "LIVE"
        if self._confirm("Leave Servers", f"{mode}: leave up to {limit} server(s) that this account does not own?"):
            self._start_worker(self._controller.leave_all_guilds(dry_run, limit))

    def _live_action_allowed(self, phrase):
        if self.dry_run_checkbox.isChecked():
            return True

        typed = self.confirm_input.text().strip().upper()
        if typed == phrase:
            return True

        QMessageBox.warning(self, "Live Confirmation", f"Live mode requires typing {phrase}.")
        return False

    def _start_worker(self, worker):
        worker.status.connect(self._log)
        worker.progress.connect(self._set_progress)
        worker.finished.connect(lambda: self._set_busy(False))
        self._set_progress(0, 1)
        self.confirm_input.clear()
        self._set_busy(True)

    def _set_busy(self, busy):
        for button in (self.clean_button, self.friends_button, self.guilds_button):
            button.setEnabled(not busy)
        for widget in (
            self.token_input,
            self.conversation_input,
            self.days_spin,
            self.limit_spin,
            self.dry_run_checkbox,
            self.confirm_input,
            self.remember_token_checkbox,
        ):
            widget.setEnabled(not busy)
        if not busy:
            self._log("Ready.")

    def _set_progress(self, current, total):
        if total:
            self.progress.setRange(0, total)
            self.progress.setValue(current)
        else:
            self.progress.setRange(0, 0)

    def _confirm(self, title, message):
        result = QMessageBox.question(
            self,
            title,
            message,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        return result == QMessageBox.Yes

    def _log(self, message):
        now = datetime.now().strftime("%H:%M:%S")
        self.log.appendPlainText(f"[{now}] {message}")

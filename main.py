import sys
import tomllib
from pathlib import Path

from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)
from PyQt6.QtWebEngineWidgets import QWebEngineView


CONFIG_FILE = Path("config.toml")


class TV(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("TV")

        # Main page stack
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        # Home screen
        self.home = QWidget()
        self.create_home_screen()
        self.stack.addWidget(self.home)

        # Keep browser widgets alive so sessions/pages persist
        self.browsers = {}

        # Start on home
        self.stack.setCurrentWidget(self.home)

        # Catch Escape even when the web browser has focus
        QApplication.instance().installEventFilter(self)

        # Fullscreen TV interface
        self.showFullScreen()

    def create_home_screen(self):
        layout = QGridLayout(self.home)
        layout.setSpacing(30)
        layout.setContentsMargins(50, 50, 50, 50)

        with open(CONFIG_FILE, "rb") as f:
            config = tomllib.load(f)

        apps = config.get("apps", [])

        columns = 3

        for index, app in enumerate(apps):
            row = index // columns
            column = index % columns

            button = QPushButton()
            button.setMinimumSize(300, 220)

            button_layout = QVBoxLayout(button)

            # App image
            image = QLabel()

            image_path = Path(app["image"])

            if image_path.exists():
                pixmap = QPixmap(str(image_path))
                pixmap = pixmap.scaled(
                    180,
                    140,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                image.setPixmap(pixmap)

            image.setAlignment(Qt.AlignmentFlag.AlignCenter)

            # App name
            name = QLabel(app["name"])
            name.setAlignment(Qt.AlignmentFlag.AlignCenter)
            name.setStyleSheet("font-size: 24px;")

            button_layout.addWidget(image)
            button_layout.addWidget(name)

            button.clicked.connect(
                lambda checked=False, app=app: self.open_app(app)
            )

            layout.addWidget(button, row, column)

    def open_app(self, app):
        name = app["name"]

        if name not in self.browsers:
            browser = QWebEngineView()

            browser_page = QWidget()
            browser_layout = QVBoxLayout(browser_page)

            browser_layout.setContentsMargins(0, 0, 0, 0)
            browser_layout.setSpacing(0)

            # Only create browser controls when requested
            if app.get("address_bar", False):
                back_button = QPushButton("←")
                forward_button = QPushButton("→")
                reload_button = QPushButton("⟳")

                for button in (back_button, forward_button, reload_button):
                    button.setFixedSize(60, 50)
                    button.setStyleSheet("font-size: 28px;")

                back_button.clicked.connect(browser.back)
                forward_button.clicked.connect(browser.forward)
                reload_button.clicked.connect(browser.reload)

                address_bar = QLineEdit()
                address_bar.setPlaceholderText(
                    "Enter website address or search..."
                )
                address_bar.setMinimumHeight(50)
                address_bar.setStyleSheet(
                    "font-size: 20px; padding: 5px;"
                )

                def navigate():
                    text = address_bar.text().strip()

                    if not text:
                        return

                    if text.startswith(("http://", "https://")):
                        url = text
                    elif "." in text and " " not in text:
                        url = "https://" + text
                    else:
                        url = (
                            "https://duckduckgo.com/?q="
                            + QUrl.toPercentEncoding(text).data().decode()
                        )

                    browser.load(QUrl(url))

                address_bar.returnPressed.connect(navigate)

                browser.urlChanged.connect(
                    lambda url: address_bar.setText(url.toString())
                )

                toolbar = QHBoxLayout()
                toolbar.setSpacing(8)
                toolbar.setContentsMargins(10, 10, 10, 10)

                toolbar.addWidget(back_button)
                toolbar.addWidget(forward_button)
                toolbar.addWidget(reload_button)
                toolbar.addWidget(address_bar)

                browser_layout.addLayout(toolbar)

            browser_layout.addWidget(browser)

            self.browsers[name] = {
                "page": browser_page,
                "browser": browser,
            }

            self.stack.addWidget(browser_page)

            browser.load(QUrl(app["url"]))

        self.stack.setCurrentWidget(
            self.browsers[name]["page"]
        )

    def eventFilter(self, watched, event):
        if event.type() == event.Type.KeyPress:

            # Escape always returns to the TV home screen
            if event.key() == Qt.Key.Key_Escape:

                self.stack.setCurrentWidget(self.home)

                return True

        return super().eventFilter(watched, event)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = TV()
    window.show()

    sys.exit(app.exec())
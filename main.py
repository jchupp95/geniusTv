import sys
import tomllib
from pathlib import Path

from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QIcon, QPixmap
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
from PyQt6.QtWebEngineCore import QWebEnginePage


CONFIG_FILE = Path("config.toml")


class SinglePage(QWebEnginePage):
    def createWindow(self, window_type):
        return self


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
        self.home.setStyleSheet("background-color: black; color: white;")

        layout = QGridLayout(self.home)
        layout.setSpacing(40)
        layout.setContentsMargins(60, 60, 60, 60)
        

        with open(CONFIG_FILE, "rb") as f:
            config = tomllib.load(f)

        apps = config.get("apps", [])

        columns = 5

        for index, app in enumerate(apps):
            row = index // columns
            column = index % columns

            # Container for icon + name
            container = QWidget()
            container_layout = QVBoxLayout(container)
            container_layout.setContentsMargins(10, 10, 10, 10)
            container_layout.setSpacing(10)

            # Square app logo button
            button = QPushButton()
            button.setFixedSize(160, 160)
            button.setStyleSheet("""
                QPushButton {
                    border: none;
                    border-radius: 0px;
                    background: transparent;
                }

                QPushButton:hover {
                    background: rgba(255, 255, 255, 20);
                }

                QPushButton:focus {
                    border: 4px solid white;
                    background: rgba(255, 255, 255, 30);
                }
            """)

            image_path = CONFIG_FILE.parent / app["image"]

            if image_path.exists():
                pixmap = QPixmap(str(image_path))

                pixmap = pixmap.scaled(
                    150,
                    150,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )

                # Put the image on the button
                button.setIcon(QIcon(pixmap))
                button.setIconSize(pixmap.size())

            button.clicked.connect(
                lambda checked=False, app=app: self.open_app(app)
            )

            # App name
            name = QLabel(app["name"])
            name.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            name.setStyleSheet("""
                QLabel {
                    color: white;
                    font-size: 22px;
                }
            """)

            container_layout.addWidget(
                button,
                alignment=Qt.AlignmentFlag.AlignHCenter
            )

            container_layout.addWidget(name)

            layout.addWidget(
                container,
                row,
                column,
                alignment=Qt.AlignmentFlag.AlignTop
            )

    def open_app(self, app):
        name = app["name"]

        if name not in self.browsers:
            browser = QWebEngineView()

            page = SinglePage(browser)
            browser.setPage(page)

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
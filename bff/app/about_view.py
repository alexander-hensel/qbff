import sys
import markdown
from PyQt6.QtWidgets import (    
    QWidget,
    QTextBrowser,   
    QPushButton,
    QHBoxLayout,    
    QVBoxLayout
)
from PyQt6.QtCore import QUrl
from PyQt6.QtGui import QDesktopServices
from bff.app.config import Config
from bff.app.theming import set_widget_icon

class AboutView(QWidget):
    def __init__(self):
        super().__init__()
        # --- Layouts ---
        main_layout = QHBoxLayout(self)
        self.setLayout(main_layout)
        # --- Markdown Viewer (QTextBrowser) ---
        self.text_browser = QTextBrowser()
        self.text_browser.setOpenExternalLinks(True)  # Make links clickable
        # Convert Markdown to HTML
        markdown_text = sys.modules["__main__"].__doc__ if sys.modules["__main__"].__doc__ else """ - """
        html = markdown.markdown(markdown_text, extensions=["tables"])
        # add minimal CSS styling
        styled_html = f"""
        <style>
            table {{ border-collapse: collapse; width: 100%; }}
            th, td {{ border: 1px solid #ccc; padding: 8px; text-align: left; }}
            body {{ font-family: Arial, sans-serif; }}
        </style>
        {html}
        """
        self.text_browser.setHtml(styled_html)

        # --- Buttons for URLs ---
        button_urls = [
            ("Find Me On Bitbucket", Config.repository, "storage"),
            ("Get Help", Config.docu_depot, "help"),
            ("About HTTP server", f"http://127.0.0.1:{Config.server_port}/docs", "api"),
        ]
        button_layout = QVBoxLayout()
        for label, url, icon in button_urls:
            btn = QPushButton(label)
            set_widget_icon(icon, btn)  # Set icon if available
            btn.setFlat(True)
            btn.setStyleSheet("text-align: left; padding-left: 8px;") 
            if not url:
                btn.setEnabled(False)
            else:
                btn.clicked.connect(lambda _, link=url: self.open_url(link))
            button_layout.addWidget(btn)
        button_layout.addStretch()

        # --- Assemble layouts ---
        main_layout.addWidget(self.text_browser, 3)   # Markdown view
        main_layout.addLayout(button_layout, 1)       # Buttons

    def open_url(self, url):
        """Open the given URL in the system's default browser."""
        QDesktopServices.openUrl(QUrl(url))
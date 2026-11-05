from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
)

class BackgroundScreen(QWidget):
    back_requested = pyqtSignal()

    def __init__(self):
        super().__init__()

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(30,10,30,30)

        self.header_layout = QHBoxLayout()
        self.layout.addLayout(self.header_layout)

        self.back_button = QPushButton('←')
        self.configure_back_button()

        self.screen_title = QLabel('BACKGROUNDS')
        self.configure_screen_title()

        self.layout.addStretch()

    def configure_back_button(self):
        button_font = QFont()
        button_font.setPointSize(22)

        self.back_button.setFont(button_font)
        self.back_button.setFixedSize(40,40)
        self.back_button.setStyleSheet(
            'QPushButton { border: none; background: transparent; padding: 0px; }'
        )
        self.back_button.setToolTip('Back')
        self.back_button.clicked.connect(self.back_requested.emit)

        self.header_layout.addWidget(self.back_button)

    def configure_screen_title(self):
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)

        self.screen_title.setFont(title_font)
        self.screen_title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.header_layout.addWidget(self.screen_title, 1)
        self.header_layout.addSpacing(40)

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
)

class RingAlarmScreen(QWidget):
    close_alarm = pyqtSignal()
    postpone_alarm = pyqtSignal()

    def __init__(self):
        super().__init__()

        self.layout = QVBoxLayout(self)
        self.setContentsMargins(30,10,30,30)

        self.screen_title = QLabel('ALARM!')
        self.configure_screen_title()

        self.layout.addSpacing(70)

        self.time_label = QLabel('--:--')
        self.configure_time_label()

        self.layout.addStretch()

        self.configure_buttons_layout()

        self.postpone_button = QPushButton('✖')
        self.configure_postpone_button()
        self.postpone_button.clicked.connect(self.postpone_alarm.emit)

        self.close_button = QPushButton('✓')
        self.configure_close_button()
        self.close_button.clicked.connect(self.close_alarm.emit)

    def configure_screen_title(self):
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)

        self.screen_title.setFont(title_font)
        self.screen_title.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        self.layout.addWidget(self.screen_title)

    def configure_time_label(self):
        time_font = QFont()
        time_font.setPointSize(70)

        self.time_label.setFont(time_font)
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        self.layout.addWidget(self.time_label)

    def configure_postpone_button(self):
        button_font = QFont('DejaVu Sans')
        button_font.setPointSize(32)

        self.postpone_button.setFont(button_font)
        self.postpone_button.setFixedSize(80, 80)
        self.postpone_button.setStyleSheet(
            'border: 2px solid #333333; border-radius: 40px;'
        )

        self.postpone_column.addWidget(
            self.postpone_button, 0, Qt.AlignmentFlag.AlignHCenter
        )

        self.postpone_label = QLabel('Postpone')
        self.postpone_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.postpone_column.addWidget(self.postpone_label)


    def configure_close_button(self):
        button_font = QFont()
        button_font.setPointSize(36)
        button_font.setWeight(QFont.Weight.DemiBold)

        self.close_button.setFont(button_font)
        self.close_button.setFixedSize(80, 80)
        self.close_button.setStyleSheet(
            'border: 2px solid #333333; border-radius: 40px; padding: 0px;'
        )

        self.close_column.addWidget(
            self.close_button, 0, Qt.AlignmentFlag.AlignHCenter
        )

        self.close_label = QLabel('Close')
        self.close_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.close_column.addWidget(self.close_label)

    def configure_buttons_layout(self):
        self.buttons_row = QHBoxLayout()
        self.postpone_column = QVBoxLayout()
        self.close_column = QVBoxLayout()

        self.buttons_row.addLayout(self.postpone_column)
        self.buttons_row.addStretch()
        self.buttons_row.addLayout(self.close_column)

        self.layout.addLayout(self.buttons_row)

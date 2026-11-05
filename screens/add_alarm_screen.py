from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
)

from alarm_utils import seconds_until_alarm

class AddAlarmScreen(QWidget):
    open_set_alarm_screen = pyqtSignal()
    alarm_selected = pyqtSignal(dict)
    back_requested = pyqtSignal()
    open_settings_screen = pyqtSignal()

    def __init__(self):
        super().__init__()

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(30, 10, 30, 30)

        self.configure_header_layout()

        self.back_button = QPushButton('←')
        self.configure_back_button()

        self.add_alarm_title = QLabel('ALARMS')
        self.configure_alarms_title()

        self.settings_button = QPushButton('⚙')
        self.configure_settings_button()

        self.layout.addSpacing(30)

        self.saved_alarm_buttons = []

        self.add_alarm_button = QPushButton('+ Add alarm')
        self.configure_add_alarm_button()

        self.layout.addStretch()

    def configure_header_layout(self):
        self.header_layout = QHBoxLayout()
        self.layout.addLayout(self.header_layout)

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

    def configure_alarms_title(self):
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)

        self.add_alarm_title.setFont(title_font)
        self.add_alarm_title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.header_layout.addWidget(self.add_alarm_title,1)

    def configure_settings_button(self):
        button_font = QFont()
        button_font.setPointSize(20)

        self.settings_button.setFont(button_font)
        self.settings_button.setFixedSize(40,40)
        self.settings_button.setStyleSheet(
            'QPushButton { border: none; background: transparent; padding: 0px; }'
        )
        self.settings_button.setToolTip('Settings')
        self.settings_button.clicked.connect(self.open_settings_screen.emit)

        self.header_layout.addWidget(self.settings_button)

    def configure_add_alarm_button(self):
        button_font = QFont()
        button_font.setPointSize(14)

        self.add_alarm_button.setFont(button_font)
        self.add_alarm_button.setFixedHeight(50)

        self.add_alarm_button.setStyleSheet(
            'text-align: left; padding-left: 12px;'
        )

        self.add_alarm_button.clicked.connect(self.open_set_alarm_screen.emit)

        self.layout.addWidget(self.add_alarm_button)

    def create_saved_alarm_button(self, alarm):
        button = QPushButton()
        button.setFixedHeight(50)

        row = QHBoxLayout(button)
        row.setContentsMargins(12,0,12,0)

        time_label = QLabel(alarm['time'])
        time_font = QFont()
        time_font.setPointSize(22)
        time_label.setFont(time_font)

        name_label = QLabel(alarm['name'])

        row.addWidget(time_label)
        row.addStretch()
        row.addWidget(name_label)

        button.clicked.connect(
            lambda checked=False, selected_alarm=alarm:
                self.alarm_selected.emit(selected_alarm)
        )

        return button

    def display_alarms(self, alarms):
        for button in self.saved_alarm_buttons:
            self.layout.removeWidget(button)
            button.deleteLater()

        self.saved_alarm_buttons.clear()

        for alarm in sorted(alarms, key=seconds_until_alarm):
            button = self.create_saved_alarm_button(alarm)
            position = self.layout.indexOf(self.add_alarm_button)
            self.layout.insertWidget(position, button)
            self.saved_alarm_buttons.append(button)
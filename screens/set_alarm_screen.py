from pathlib import Path

from PyQt6.QtCore import Qt, QTime, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTimeEdit,
    QLineEdit,
    QComboBox,
    QCheckBox,
)

class SetAlarmScreen(QWidget):
    alarm_saved = pyqtSignal(dict)
    delete_request = pyqtSignal()
    back_requested = pyqtSignal()

    def __init__(self):
        super().__init__()

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(30, 10, 30, 30)

        self.configure_header_layout()

        self.back_button = QPushButton('←')
        self.configure_back_button()

        self.set_alarm_title = QLabel('SET ALARM')
        self.configure_set_alarm_title()

        self.layout.addSpacing(100)

        self.time_selector = QTimeEdit()
        self.configure_time_selector()

        self.layout.addSpacing(50)

        self.alarm_name = QLineEdit()
        self.configure_alarm_name()

        self.layout.addSpacing(30)

        self.ringtone_label = QLabel('Select ringtone')
        self.layout.addWidget(self.ringtone_label)

        self.ringtone_selector = QComboBox()
        self.configure_ringtone()

        self.layout.addSpacing(30)

        self.recurring_label = QLabel('Recurring')
        self.layout.addWidget(self.recurring_label)

        self.recurring_selector = QCheckBox()
        self.layout.addWidget(self.recurring_selector)

        self.layout.addStretch(1)

        self.configure_action_buttons_layout()

        self.save_alarm_button = QPushButton('Save alarm')
        self.configure_save_alarm_button()

        self.delete_alarm_button = QPushButton('Delete alarm')
        self.configure_delete_alarm_button()

    def configure_header_layout(self):
        self.header_layout = QHBoxLayout()
        self.layout.addLayout(self.header_layout)

    def configure_back_button(self):
        button_font = QFont()
        button_font.setPointSize(22)

        self.back_button.setFont(button_font)
        self.back_button.setFixedSize(40, 40)
        self.back_button.setStyleSheet(
            'QPushButton { border: none; background: transparent; padding: 0px; }'
        )
        self.back_button.setToolTip('Back')
        self.back_button.clicked.connect(self.back_requested.emit)

        self.header_layout.addWidget(self.back_button)

    def configure_set_alarm_title(self):
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)

        self.set_alarm_title.setFont(title_font)
        self.set_alarm_title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.header_layout.addWidget(self.set_alarm_title,1)
        self.header_layout.addSpacing(40)

    def configure_time_selector(self):
        self.time_selector.setTime(QTime.currentTime())
        self.time_selector.setDisplayFormat('HH:mm')
        self.time_selector.setButtonSymbols(QTimeEdit.ButtonSymbols.NoButtons)

        time_font = QFont()
        time_font.setPointSize(70)

        self.time_selector.setFont(time_font)
        self.time_selector.setStyleSheet('QTimeEdit { border: none; background: transparent; }')
        self.time_selector.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.layout.addWidget(self.time_selector)

    def configure_alarm_name(self):
        self.alarm_name.setPlaceholderText('Alarm name')

        self.layout.addWidget(self.alarm_name)

    def configure_ringtone(self):
        built_in_sounds = ['Default','Bell','Chime']

        for ringtone in built_in_sounds:
            self.ringtone_selector.addItem(ringtone, ringtone)

        self.layout.addWidget(self.ringtone_selector)

    def configure_save_alarm_button(self):
        self.save_alarm_button.setStyleSheet(
            """
            QPushButton {
                border: 2px solid #333333;
                border-radius: 16px;
                padding: 6px 16px;
            }
            """
        )

        button_font = QFont()
        button_font.setPointSize(12)

        self.save_alarm_button.setFont(button_font)

        self.save_alarm_button.clicked.connect(self.save_alarm)

        self.action_buttons_row.addWidget(self.save_alarm_button)
        self.action_buttons_row.addStretch()

    def configure_delete_alarm_button(self):
        self.delete_alarm_button.setStyleSheet('border: none;')

        button_font = QFont()
        button_font.setPointSize(12)
        self.delete_alarm_button.setFont(button_font)

        self.delete_alarm_button.clicked.connect(self.delete_request.emit)
        self.action_buttons_row.addWidget(self.delete_alarm_button)
        self.delete_alarm_button.hide()

    def configure_action_buttons_layout(self):
        self.action_buttons_row = QHBoxLayout()
        self.action_buttons_row.addStretch(1)
        self.layout.addLayout(self.action_buttons_row)

    def save_alarm(self):
        alarm = {
            'time': self.time_selector.time().toString('HH:mm'),
            'name': self.alarm_name.text().strip() or 'Alarm',
            'ringtone': self.ringtone_selector.currentData(),
            'recurring': self.recurring_selector.isChecked(),
        }

        self.alarm_saved.emit(alarm)

    def load_alarm(self, alarm):
        self.time_selector.setTime(QTime.fromString(alarm['time'], 'HH:mm'))
        self.alarm_name.setText(alarm['name'])
        index = self.ringtone_selector.findData(alarm['ringtone'])
        self.ringtone_selector.setCurrentIndex(index)
        self.recurring_selector.setChecked(alarm['recurring'])

        self.delete_alarm_button.show()
        self.action_buttons_row.setStretch(0, 0)
        self.action_buttons_row.setStretch(2, 1)

    def reset_form(self):
        self.time_selector.setTime(QTime.currentTime())
        self.alarm_name.clear()
        self.ringtone_selector.setCurrentIndex(0)
        self.recurring_selector.setChecked(False)

        self.delete_alarm_button.hide()
        self.action_buttons_row.setStretch(0, 1)
        self.action_buttons_row.setStretch(2, 1)

    def add_ringtone(self, ringtone_name):
        display_name = Path(ringtone_name).stem
        display_name = display_name[:1].upper() + display_name[1:]
        self.ringtone_selector.addItem(display_name ,ringtone_name)

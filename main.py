import sys
import json
from pathlib import Path
from uuid import uuid4

from PyQt6.QtCore import Qt,QTime,QTimer,pyqtSignal
from PyQt6.QtWidgets import (
    QApplication,
    QLabel,
    QMainWindow,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QPushButton,
    QStackedWidget,
    QTimeEdit,
    QLineEdit,
    QComboBox,
    QCheckBox,
)
from PyQt6.QtGui import QFont

ALARMS_FILE = Path(__file__).parent / 'alarms.json'

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.alarm_store = AlarmsStore(ALARMS_FILE)
        self.alarms = self.alarm_store.load_alarms()

        self.setWindowTitle('Alarm Clock')
        self.resize(400,700)

        self.screen_stack = QStackedWidget()
        self.setCentralWidget(self.screen_stack)

        self.main_screen = MainScreen()
        self.screen_stack.addWidget(self.main_screen)
        self.main_screen.open_add_alarm_screen.connect(self.open_add_alarm_screen)

        self.add_alarm_screen = AddAlarmScreen()
        self.add_alarm_screen.display_alarms(self.alarms)
        self.screen_stack.addWidget(self.add_alarm_screen)
        self.add_alarm_screen.open_set_alarm_screen.connect(self.open_set_alarm_screen)

        self.set_alarm_screen = SetAlarmScreen()
        self.screen_stack.addWidget(self.set_alarm_screen)
        self.set_alarm_screen.alarm_saved.connect(self.save_alarm)

    def open_add_alarm_screen(self):
        self.screen_stack.setCurrentWidget(self.add_alarm_screen)

    def open_set_alarm_screen(self):
        self.screen_stack.setCurrentWidget(self.set_alarm_screen)

    def save_alarm(self, alarm):
        alarm['id'] = str(uuid4())
        self.alarms.append(alarm)
        self.alarm_store.save_alarms(self.alarms)
        self.add_alarm_screen.display_alarms(self.alarms)
        self.screen_stack.setCurrentWidget(self.add_alarm_screen)


class MainScreen(QWidget):
    open_add_alarm_screen = pyqtSignal()

    def __init__(self):
        super().__init__()

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(30, 50, 30, 30)

        self.time_label = QLabel()
        self.configure_time_display()

        self.layout.addStretch(2)

        self.next_alarm_title = QLabel('NEXT ALARM')
        self.configure_next_alarm_title()

        self.next_alarm_label = QLabel('No alarms set')
        self.configure_next_alarm_display()

        self.layout.addStretch(1)

        self.add_alarm_button = QPushButton('Add alarm')
        self.configure_new_alarm_button()

        self.clock_timer = QTimer(self)
        self.setup_clock_timer()
        self.update_time()

    def configure_time_display(self):
        time_font = QFont()
        time_font.setPointSize(48)

        self.time_label.setFont(time_font)
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.layout.addWidget(self.time_label)

    def configure_next_alarm_title(self):
        next_alarm_title_font = QFont()
        next_alarm_title_font.setPointSize(12)

        self.next_alarm_title.setFont(next_alarm_title_font)
        self.next_alarm_title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.layout.addWidget(self.next_alarm_title)

    def configure_next_alarm_display(self):
        next_alarm_font = QFont()
        next_alarm_font.setPointSize(18)

        self.next_alarm_label.setFont(next_alarm_font)
        self.next_alarm_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.layout.addWidget(self.next_alarm_label)

    def configure_new_alarm_button(self):
        self.add_alarm_button.clicked.connect(self.open_add_alarm_screen.emit)

        self.add_alarm_button.setFixedHeight(30)
        self.add_alarm_button.setFixedWidth(140)

        add_alarm_button_font = QFont()
        add_alarm_button_font.setPointSize(12)

        self.add_alarm_button.setFont(add_alarm_button_font)

        self.layout.addWidget(self.add_alarm_button,0,Qt.AlignmentFlag.AlignHCenter)

    def setup_clock_timer(self):
        self.clock_timer.timeout.connect(self.update_time)
        self.clock_timer.start(1000)

    def update_time(self):
        current_time = QTime.currentTime().toString('HH:mm')
        self.time_label.setText(current_time)


class AddAlarmScreen(QWidget):
    open_set_alarm_screen = pyqtSignal()

    def __init__(self):
        super().__init__()

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(30, 10, 30, 30)

        self.add_alarm_title = QLabel('ALARMS')
        self.configure_alarms_title()

        self.layout.addSpacing(30)

        self.saved_alarm_buttons = []

        self.add_alarm_button = QPushButton('+ Add alarm')
        self.configure_add_alarm_button()

        self.layout.addStretch()

    def configure_alarms_title(self):
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)

        self.add_alarm_title.setFont(title_font)
        self.add_alarm_title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.layout.addWidget(self.add_alarm_title,0,Qt.AlignmentFlag.AlignTop)

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

        return button

    def display_alarms(self, alarms):
        for button in self.saved_alarm_buttons:
            self.layout.removeWidget(button)
            button.deleteLater()

        self.saved_alarm_buttons.clear()

        for alarm in sorted(alarms, key=self.seconds_until_alarm):
            button = self.create_saved_alarm_button(alarm)
            position = self.layout.indexOf(self.add_alarm_button)
            self.layout.insertWidget(position, button)
            self.saved_alarm_buttons.append(button)

    def seconds_until_alarm(self, alarm):
        now = QTime.currentTime()
        alarm_time = QTime.fromString(alarm['time'], 'HH:mm')

        seconds = now.secsTo(alarm_time)
        return seconds % (24 * 60 * 60)

class SetAlarmScreen(QWidget):
    alarm_saved = pyqtSignal(dict)

    def __init__(self):
        super().__init__()

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(30, 10, 30, 30)

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

        self.save_alarm_button = QPushButton('Save alarm')
        self.configure_save_alarm_button()

    def configure_set_alarm_title(self):
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)

        self.set_alarm_title.setFont(title_font)
        self.set_alarm_title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.layout.addWidget(self.set_alarm_title,0,Qt.AlignmentFlag.AlignTop)

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

        self.layout.addWidget(self.save_alarm_button,0,Qt.AlignmentFlag.AlignHCenter)

    def configure_alarm_name(self):
        self.alarm_name.setPlaceholderText('Alarm name')

        self.layout.addWidget(self.alarm_name)

    def configure_ringtone(self):
        self.ringtone_selector.addItems(['Default','Bell','Chime'])

        self.layout.addWidget(self.ringtone_selector)

    def save_alarm(self):
        alarm = {
            'time': self.time_selector.time().toString('HH:mm'),
            'name': self.alarm_name.text().strip() or 'Alarm',
            'ringtone': self.ringtone_selector.currentText(),
            'recurring': self.recurring_selector.isChecked(),
        }

        self.alarm_saved.emit(alarm)

class SettingsScreen(QWidget):
    pass


class AlarmsStore:
    def __init__(self, file_path):
        self.file_path = file_path

    def load_alarms(self):
        with self.file_path.open('r', encoding='utf-8') as file:
            return json.load(file)

    def save_alarms(self, alarms):
        with self.file_path.open('w', encoding='utf-8') as file:
            json.dump(alarms,file,indent=4)

app = QApplication(sys.argv)

window = MainWindow()
window.show()

sys.exit(app.exec())
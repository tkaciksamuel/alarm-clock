import sys
import json
from pathlib import Path
from uuid import uuid4

from PyQt6.QtCore import Qt,QTime,QTimer,pyqtSignal,QUrl,QDate
from PyQt6.QtMultimedia import QSoundEffect
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
    QMessageBox,
    QSlider

)
from PyQt6.QtGui import QFont

ALARMS_FILE = Path(__file__).parent / 'alarms.json'


def seconds_until_alarm(alarm):
    now = QTime.currentTime()
    alarm_time = QTime.fromString(alarm['time'], 'HH:mm')

    seconds = now.secsTo(alarm_time)
    return seconds % (24 * 60 * 60)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.alarm_store = AlarmsStore(ALARMS_FILE)
        self.alarms = self.alarm_store.load_alarms()
        self.editing_alarm_id = None
        self.triggered_alarm_ids = set()
        self.last_checked_minute = None
        self.ringing_alarm = None
        self.postponed_alarm_time = None

        self.setWindowTitle('Alarm Clock')
        self.resize(400,700)

        self.screen_stack = QStackedWidget()
        self.setCentralWidget(self.screen_stack)

        self.setup_main_screen()

        self.setup_add_alarm_screen()

        self.setup_set_alarm_screen()

        self.setup_ring_alarm_screen()

        self.setup_settings_screen()

        self.setup_postpone_message()

        self.setup_alarm_sound()

        self.main_screen.clock_timer.timeout.connect(self.update_next_alarm)
        self.main_screen.clock_timer.timeout.connect(self.check_alarms)
        self.update_next_alarm()

    def setup_main_screen(self):
        self.main_screen = MainScreen()
        self.screen_stack.addWidget(self.main_screen)
        self.main_screen.open_add_alarm_screen.connect(self.open_add_alarm_screen)

    def setup_add_alarm_screen(self):
        self.add_alarm_screen = AddAlarmScreen()
        self.add_alarm_screen.display_alarms(self.alarms)
        self.screen_stack.addWidget(self.add_alarm_screen)
        self.add_alarm_screen.open_set_alarm_screen.connect(self.open_set_alarm_screen)
        self.add_alarm_screen.alarm_selected.connect(self.open_edit_alarm_screen)
        self.add_alarm_screen.back_requested.connect(self.open_main_screen)

    def setup_set_alarm_screen(self):
        self.set_alarm_screen = SetAlarmScreen()
        self.screen_stack.addWidget(self.set_alarm_screen)
        self.set_alarm_screen.alarm_saved.connect(self.save_alarm)
        self.set_alarm_screen.delete_request.connect(self.delete_alarm)
        self.set_alarm_screen.back_requested.connect(self.open_add_alarm_screen)

    def setup_ring_alarm_screen(self):
        self.ring_alarm_screen = RingAlarmScreen()
        self.screen_stack.addWidget(self.ring_alarm_screen)
        self.ring_alarm_screen.close_alarm.connect(self.close_ring_alarm)
        self.ring_alarm_screen.postpone_alarm.connect(self.postpone_ring_alarm)

    def setup_settings_screen(self):
        self.settings_screen = SettingsScreen()
        self.screen_stack.addWidget(self.settings_screen)
        self.add_alarm_screen.open_settings_screen.connect(
            self.open_settings_screen
        )

        self.settings_screen.back_requested.connect(self.open_add_alarm_screen)
        self.settings_screen.time_format_selector.currentTextChanged.connect(
            self.change_time_format
        )
        self.settings_screen.date_format_selector.currentTextChanged.connect(
            self.change_date_format
        )
        self.settings_screen.alarm_volume_slider.valueChanged.connect(
            self.change_alarm_volume
        )
        self.settings_screen.alarm_volume_slider.sliderReleased.connect(
            self.play_volume_preview
        )

    def open_main_screen(self):
        self.editing_alarm_id = None
        self.screen_stack.setCurrentWidget(self.main_screen)

    def open_add_alarm_screen(self):
        self.screen_stack.setCurrentWidget(self.add_alarm_screen)

    def open_set_alarm_screen(self):
        self.editing_alarm_id = None
        self.set_alarm_screen.reset_form()
        self.screen_stack.setCurrentWidget(self.set_alarm_screen)

    def open_settings_screen(self):
        self.screen_stack.setCurrentWidget(self.settings_screen)

    def setup_postpone_message(self):
        self.postpone_message = QLabel()
        self.postpone_message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.statusBar().addWidget(self.postpone_message, 1)
        self.statusBar().setSizeGripEnabled(False)

    def setup_alarm_sound(self):
        self.alarm_sound = QSoundEffect(self)

        sound_path = Path(__file__).parent / 'sounds' / 'default.wav'
        self.alarm_sound.setSource(QUrl.fromLocalFile(str(sound_path)))

        self.volume_preview = QSoundEffect(self)
        self.volume_preview.setSource(QUrl.fromLocalFile(str(sound_path)))
        self.volume_preview.setLoopCount(1)
        self.volume_preview.setVolume(0.5)

        self.alarm_sound.setLoopCount(QSoundEffect.Loop.Infinite.value)
        self.alarm_sound.setVolume(0.5)

    def open_edit_alarm_screen(self, alarm):
        self.editing_alarm_id = alarm['id']
        self.set_alarm_screen.load_alarm(alarm)
        self.screen_stack.setCurrentWidget(self.set_alarm_screen)

    def open_ring_alarm_screen(self, alarm):
        self.ringing_alarm = alarm

        triggered_time = QTime.currentTime().toString('HH:mm')

        self.ring_alarm_screen.time_label.setText(triggered_time)
        self.screen_stack.setCurrentWidget(self.ring_alarm_screen)
        self.alarm_sound.play()

    def close_ring_alarm(self):
        self.alarm_sound.stop()

        if self.ringing_alarm is not None and not self.ringing_alarm['recurring']:
            self.alarms = [
                alarm for alarm in self.alarms
                if alarm['id'] != self.ringing_alarm['id']
            ]

            self.alarm_store.save_alarms(self.alarms)
            self.add_alarm_screen.display_alarms(self.alarms)
            self.update_next_alarm()

        self.ringing_alarm = None
        self.screen_stack.setCurrentWidget(self.main_screen)

    def postpone_ring_alarm(self):
        if self.ringing_alarm is None:
            return

        self.alarm_sound.stop()

        postpone_minutes = (
            self.settings_screen.postpone_duration_selector.currentData()
        )
        postpone_seconds = postpone_minutes * 60

        self.postponed_alarm_time = QTime.currentTime().addSecs(postpone_seconds)

        self.main_screen.postponed_alarm_display.setText(
            self.postponed_alarm_time.toString('HH:mm')
        )

        self.main_screen.postponed_alarm_title.show()
        self.main_screen.postponed_alarm_display.show()

        alarm = self.ringing_alarm

        QTimer.singleShot(
            postpone_seconds * 1000,
            lambda: self.ring_postponed_alarm(alarm)
        )

        self.ringing_alarm = None
        self.screen_stack.setCurrentWidget(self.main_screen)
        self.postpone_message.setText(
            f"Alarm was postponed {postpone_minutes} minutes"
        )
        QTimer.singleShot(3000, self.postpone_message.clear)

    def ring_postponed_alarm(self, alarm):
        self.postponed_alarm_time = None
        self.main_screen.postponed_alarm_title.hide()
        self.main_screen.postponed_alarm_display.hide()
        self.open_ring_alarm_screen(alarm)

    def save_alarm(self, alarm):
        if self.editing_alarm_id is None:
            alarm['id'] = str(uuid4())
            self.alarms.append(alarm)
        else:
            for saved_alarm in self.alarms:
                if saved_alarm['id'] == self.editing_alarm_id:
                    saved_alarm.update(alarm)
                    break
            self.editing_alarm_id = None

        self.alarm_store.save_alarms(self.alarms)
        self.add_alarm_screen.display_alarms(self.alarms)
        self.update_next_alarm()
        self.screen_stack.setCurrentWidget(self.add_alarm_screen)

    def update_next_alarm(self):
        next_alarm = min(
            self.alarms,
            key=seconds_until_alarm,
            default=None
        )

        self.main_screen.display_next_alarm(next_alarm)

    def delete_alarm(self):
        if self.editing_alarm_id is None:
            return

        answer = QMessageBox.question(
            self,
            'Delete alarm',
            'Are you sure you want to delete this alarm ?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if answer != QMessageBox.StandardButton.Yes:
            return

        self.alarms = [
            alarm for alarm in self.alarms
            if alarm['id'] != self.editing_alarm_id
        ]
        self.editing_alarm_id = None

        self.alarm_store.save_alarms(self.alarms)
        self.add_alarm_screen.display_alarms(self.alarms)
        self.update_next_alarm()
        self.screen_stack.setCurrentWidget(self.add_alarm_screen)

    def check_alarms(self):
        current_minute = QTime.currentTime().toString('HH:mm')

        if current_minute != self.last_checked_minute:
            self.triggered_alarm_ids.clear()
            self.last_checked_minute = current_minute

        for alarm in self.alarms:
            if alarm['time'] == current_minute:
                if alarm['id'] not in self.triggered_alarm_ids:
                    self.triggered_alarm_ids.add(alarm['id'])
                    self.open_ring_alarm_screen(alarm)

    def change_time_format(self, selected_format):
        if selected_format == '12-hour':
            self.main_screen.time_format = 'hh:mm AP'
        else:
            self.main_screen.time_format = 'HH:mm'

        self.main_screen.update_time()

    def change_date_format(self,selected_format):
        self.main_screen.date_format = selected_format
        self.main_screen.update_date()

    def change_alarm_volume(self, volume):
        volume_level = volume / 100.0

        self.alarm_sound.setVolume(volume_level)
        self.volume_preview.setVolume(volume_level)

    def play_volume_preview(self):
        self.volume_preview.stop()
        self.volume_preview.play()

class MainScreen(QWidget):
    open_add_alarm_screen = pyqtSignal()

    def __init__(self):
        super().__init__()

        self.time_format = 'HH:mm'
        self.date_format = 'dd.MM.yyyy'

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(30, 50, 30, 30)

        self.time_label = QLabel()
        self.configure_time_display()

        self.date_label = QLabel()
        self.configure_date_display()

        self.layout.addStretch(2)

        self.next_alarm_title = QLabel('NEXT ALARM')
        self.configure_next_alarm_title()

        self.next_alarm_display = QLabel('No alarms set')
        self.configure_next_alarm_display()

        self.postponed_alarm_title = QLabel('POSTPONED ALARM')
        self.configure_postponed_alarm_title()

        self.postponed_alarm_display = QLabel('No postponed alarm')
        self.configure_postponed_alarm_display()

        self.layout.addStretch(1)

        self.add_alarm_button = QPushButton('Add alarm')
        self.configure_new_alarm_button()

        self.clock_timer = QTimer(self)
        self.setup_clock_timer()
        self.update_time()
        self.update_date()

    def configure_time_display(self):
        time_font = QFont()
        time_font.setPointSize(48)

        self.time_label.setFont(time_font)
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.layout.addWidget(self.time_label)

    def configure_date_display(self):
        date_font = QFont()
        date_font.setPointSize(16)

        self.date_label.setFont(date_font)
        self.date_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.layout.addWidget(self.date_label)

    def configure_next_alarm_title(self):
        next_alarm_title_font = QFont()
        next_alarm_title_font.setPointSize(12)

        self.next_alarm_title.setFont(next_alarm_title_font)
        self.next_alarm_title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.layout.addWidget(self.next_alarm_title)

    def configure_next_alarm_display(self):
        next_alarm_font = QFont()
        next_alarm_font.setPointSize(28)

        self.next_alarm_display.setFont(next_alarm_font)
        self.next_alarm_display.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.layout.addWidget(self.next_alarm_display)

    def configure_postponed_alarm_title(self):
        self.postponed_alarm_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.postponed_alarm_title)
        self.postponed_alarm_title.hide()

    def configure_postponed_alarm_display(self):
        time_font = QFont()
        time_font.setPointSize(28)

        self.postponed_alarm_display.setFont(time_font)
        self.postponed_alarm_display.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.layout.addWidget(self.postponed_alarm_display)
        self.postponed_alarm_display.hide()

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

        self.clock_timer.timeout.connect(self.update_date)

    def update_time(self):
        current_time = QTime.currentTime().toString(self.time_format)
        self.time_label.setText(current_time)

    def update_date(self):
        current_date = QDate.currentDate().toString(self.date_format)
        self.date_label.setText(current_date)

    def display_next_alarm(self, alarm):
        if alarm is None:
            self.next_alarm_display.setText('No alarms set')
        else:
            self.next_alarm_display.setText(
                f"{alarm['time']}"
            )


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
        self.ringtone_selector.addItems(['Default','Bell','Chime'])

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
            'ringtone': self.ringtone_selector.currentText(),
            'recurring': self.recurring_selector.isChecked(),
        }

        self.alarm_saved.emit(alarm)

    def load_alarm(self, alarm):
        self.time_selector.setTime(QTime.fromString(alarm['time'], 'HH:mm'))
        self.alarm_name.setText(alarm['name'])
        self.ringtone_selector.setCurrentText(alarm['ringtone'])
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

class SettingsScreen(QWidget):
    back_requested = pyqtSignal()

    def __init__(self):
        super().__init__()

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(30,10,30,30)

        self.configure_header_layout()

        self.back_button = QPushButton('←')
        self.configure_back_button()

        self.settings_title = QLabel('SETTINGS')
        self.configure_settings_title()

        self.time_format_label = QLabel('Time format')
        self.layout.addWidget(self.time_format_label)

        self.time_format_selector = QComboBox()
        self.configure_time_format_selector()

        self.date_format_label = QLabel('Date format')
        self.layout.addWidget(self.date_format_label)

        self.date_format_selector = QComboBox()
        self.configure_date_format_selector()

        self.postpone_duration_label = QLabel('Postpone duration')
        self.layout.addWidget(self.postpone_duration_label)

        self.postpone_duration_selector = QComboBox()
        self.configure_postpone_duration_selector()

        self.alarm_volume_label = QLabel('Alarm volume')
        self.layout.addWidget(self.alarm_volume_label)

        self.alarm_volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.configure_alarm_volume_slider()


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

    def configure_settings_title(self):
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)

        self.settings_title.setFont(title_font)
        self.settings_title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.header_layout.addWidget(self.settings_title, 1)
        self.header_layout.addSpacing(40)

    def configure_time_format_selector(self):
        self.time_format_selector.addItems(['24-hour','12-hour'])
        self.layout.addWidget(self.time_format_selector)

    def configure_date_format_selector(self):
        self.date_format_selector.addItems(
            ['dd.MM.yyyy','d MMMM yyyy']
        )
        self.layout.addWidget(self.date_format_selector)

    def configure_postpone_duration_selector(self):
        self.postpone_duration_selector.addItem('3 minutes',3)
        self.postpone_duration_selector.addItem('5 minutes',5)
        self.postpone_duration_selector.addItem('10 minutes',10)
        self.postpone_duration_selector.addItem('15 minutes',15)

        self.postpone_duration_selector.setCurrentIndex(
            self.postpone_duration_selector.findData(5)
        )

        self.layout.addWidget(self.postpone_duration_selector)

    def configure_alarm_volume_slider(self):
        self.alarm_volume_slider.setRange(0, 100)
        self.alarm_volume_slider.setValue(50)
        self.alarm_volume_slider.valueChanged.connect(
            lambda volume: self.alarm_volume_label.setText(
            f'Alarm volume {volume}%'
            )
        )

        self.layout.addWidget(self.alarm_volume_slider)

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
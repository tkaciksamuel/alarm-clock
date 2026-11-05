import sys
import json
from pathlib import Path
from uuid import uuid4

from PyQt6.QtCore import Qt,QTime,QTimer,pyqtSignal,QUrl,QDate,QEvent
from PyQt6.QtMultimedia import QSoundEffect
from PyQt6.QtWidgets import (
    QApplication,
    QLabel,
    QMainWindow,
    QStackedWidget,
    QMessageBox,
)

from screens.background_screen import BackgroundScreen
from screens.ring_alarm_screen import RingAlarmScreen
from screens.settings_screen import SettingsScreen
from screens.main_screen import MainScreen
from screens.set_alarm_screen import SetAlarmScreen
from screens.add_alarm_screen import AddAlarmScreen
from screens.ringtone_screen import RingtoneScreen

from alarm_utils import seconds_until_alarm

ALARMS_FILE = Path(__file__).parent / 'alarms.json'

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
        self.applied_alarm_volume = 50
        self.applied_postpone_minutes = 5
        self.applied_ringtone = 'Default'

        self.setWindowTitle('Alarm Clock')
        self.resize(400,700)

        self.screen_stack = QStackedWidget()
        self.setCentralWidget(self.screen_stack)

        self.setup_main_screen()

        self.setup_add_alarm_screen()

        self.setup_set_alarm_screen()

        self.setup_ring_alarm_screen()

        self.setup_settings_screen()

        self.setup_ringtone_screen()

        self.setup_background_screen()

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
        self.settings_screen.alarm_volume_slider.setValue(
            self.applied_alarm_volume
        )

        self.add_alarm_screen.open_settings_screen.connect(
            self.open_settings_screen
        )

        self.settings_screen.back_requested.connect(self.open_add_alarm_screen)
        self.settings_screen.apply_requested.connect(self.apply_settings)
        self.settings_screen.volume_preview_requested.connect(
            self.play_volume_preview
        )

    def setup_ringtone_screen(self):
        self.ringtone_screen = RingtoneScreen()
        self.screen_stack.addWidget(self.ringtone_screen)

        self.settings_screen.open_ringtone_screen.connect(
            self.open_ringtone_screen
        )
        self.ringtone_screen.back_requested.connect(
            self.return_to_settings_screen
        )
        self.ringtone_screen.ringtone_imported.connect(
            self.set_alarm_screen.add_ringtone
        )

        for button in self.ringtone_screen.ringtone_group.buttons():
            ringtone_name = button.property('ringtone')
            if self.set_alarm_screen.ringtone_selector.findData(ringtone_name) == -1:
                self.set_alarm_screen.add_ringtone(ringtone_name)

    def setup_background_screen(self):
        self.background_screen = BackgroundScreen()
        self.screen_stack.addWidget(self.background_screen)

        self.settings_screen.open_background_screen.connect(
            self.open_background_screen
        )
        self.background_screen.back_requested.connect(
            self.return_to_settings_screen
        )

    def open_ringtone_screen(self):
        self.screen_stack.setCurrentWidget(self.ringtone_screen)

    def open_background_screen(self):
        self.screen_stack.setCurrentWidget(self.background_screen)

    def return_to_settings_screen(self):
        self.screen_stack.setCurrentWidget(self.settings_screen)

    def open_main_screen(self):
        self.editing_alarm_id = None
        self.screen_stack.setCurrentWidget(self.main_screen)

    def open_add_alarm_screen(self):
        self.screen_stack.setCurrentWidget(self.add_alarm_screen)

    def open_set_alarm_screen(self):
        self.editing_alarm_id = None
        self.set_alarm_screen.reset_form()
        self.set_alarm_screen.ringtone_selector.setCurrentText(self.applied_ringtone)
        self.screen_stack.setCurrentWidget(self.set_alarm_screen)

    def open_settings_screen(self):
        self.restore_applied_settings()
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

        sound_filename = {
            'Default': 'default.wav',
            'Bell': 'bell.wav',
            'Chime': 'chime.wav'
        }.get(alarm['ringtone'],'default.wav')

        sound_path = self.get_ringtone_path(alarm['ringtone'])
        self.alarm_sound.setSource(QUrl.fromLocalFile(str(sound_path)))

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

        postpone_minutes = self.applied_postpone_minutes
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
        ringtone = self.ringtone_screen.get_selected_ringtone()
        sound_path = self.get_ringtone_path(ringtone)
        volume = self.settings_screen.alarm_volume_slider.value()

        self.volume_preview.stop()
        self.volume_preview.setSource(
            QUrl.fromLocalFile(str(sound_path))
        )
        self.volume_preview.setVolume(volume / 100.0)
        self.volume_preview.play()

    def apply_settings(self):
        time_format = (
            self.settings_screen.time_format_selector.currentText()
        )
        date_format = (
            self.settings_screen.date_format_selector.currentText()
        )
        volume = self.settings_screen.alarm_volume_slider.value()

        self.applied_alarm_volume = volume
        self.applied_postpone_minutes = (
            self.settings_screen.postpone_duration_selector.currentData()
        )

        self.change_alarm_volume(volume)
        self.change_time_format(time_format)
        self.change_date_format(date_format)

        self.applied_ringtone = self.ringtone_screen.get_selected_ringtone()

        self.open_main_screen()

    def restore_applied_settings(self):
        time_format = (
            '12-hour'
            if self.main_screen.time_format == 'hh:mm AP'
            else '24-hour'
        )

        self.settings_screen.time_format_selector.setCurrentText(time_format)
        self.settings_screen.date_format_selector.setCurrentText(
            self.main_screen.date_format
        )
        self.settings_screen.alarm_volume_slider.setValue(
            self.applied_alarm_volume
        )
        self.settings_screen.postpone_duration_selector.setCurrentIndex(
            self.settings_screen.postpone_duration_selector.findData(
                self.applied_postpone_minutes
            )
        )
        self.ringtone_screen.set_selected_ringtone(self.applied_ringtone)

    def get_ringtone_path(self, ringtone):
        built_in_sounds = {
            'Default': 'default.wav',
            'Bell': 'bell.wav',
            'Chime': 'chime.wav'
        }

        filename = built_in_sounds.get(ringtone, ringtone)

        return Path(__file__).parent / 'sounds' / filename


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
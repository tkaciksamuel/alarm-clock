import sys

from PyQt6.QtCore import Qt,QTime,QTimer,pyqtSignal
from PyQt6.QtWidgets import (
    QApplication,
    QLabel,
    QMainWindow,
    QVBoxLayout,
    QWidget,
    QPushButton,
    QStackedWidget,
    QTimeEdit
)
from PyQt6.QtGui import QFont


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle('Alarm Clock')
        self.resize(400,700)

        self.screen_stack = QStackedWidget()
        self.setCentralWidget(self.screen_stack)

        self.main_screen = MainScreen()
        self.screen_stack.addWidget(self.main_screen)
        self.main_screen.open_add_alarm_screen.connect(self.open_add_alarm_screen)

        self.add_alarm_screen = QWidget()
        self.screen_stack.addWidget(self.add_alarm_screen)
        self.add_alarm_layout = QVBoxLayout(self.add_alarm_screen)
        self.add_alarm_layout.setContentsMargins(30,10,30,30)

        self.add_alarm_title = QLabel('ALARMS')
        self.configure_alarms_title()

        self.new_alarm_button = QPushButton('+ Add alarm')
        self.configure_new_alarm_button()

        self.add_alarm_layout.addStretch()

    def configure_alarms_title(self):
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)

        self.add_alarm_title.setFont(title_font)
        self.add_alarm_title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.add_alarm_layout.addWidget(self.add_alarm_title,0,Qt.AlignmentFlag.AlignTop)


    def configure_new_alarm_button(self):
        button_font = QFont()
        button_font.setPointSize(14)

        self.new_alarm_button.setFont(button_font)
        self.new_alarm_button.setFixedHeight(50)

        self.new_alarm_button.setStyleSheet(
            'text-align: left; padding-left: 12px;'
        )

        self.add_alarm_layout.addWidget(self.new_alarm_button)

    def open_add_alarm_screen(self):
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
        self.configure_add_alarm_button()

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

    def configure_add_alarm_button(self):
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
    pass

class SetAlarmScreen(QWidget):
    pass

class SettingsScreen(QWidget):
    pass

app = QApplication(sys.argv)

window = MainWindow()
window.show()

sys.exit(app.exec())
from PyQt6.QtCore import Qt, QTime, QDate, QTimer, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
)

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

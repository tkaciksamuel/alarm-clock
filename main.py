import sys

from PyQt6.QtCore import Qt,QTime,QTimer
from PyQt6.QtWidgets import (
    QApplication,
    QLabel,
    QMainWindow,
    QVBoxLayout,
    QWidget,
    QPushButton
)
from PyQt6.QtGui import QFont


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle('Alarm Clock')
        self.resize(400,700)

        self.screen = QWidget()
        self.setCentralWidget(self.screen)

        self.layout = QVBoxLayout()
        self.configure_layout()

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

    def configure_layout(self):
        self.layout.setContentsMargins(30,50,30,30)
        self.screen.setLayout(self.layout)

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
        self.add_alarm_button.clicked.connect(self.open_add_alarm_screen)

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

    def open_add_alarm_screen(self):
        print('Add alarm button clicked')

app = QApplication(sys.argv)

window = MainWindow()
window.show()

sys.exit(app.exec())
import sys

from PyQt6.QtCore import Qt,QTime,QTimer
from PyQt6.QtWidgets import (
    QApplication,
    QLabel,
    QMainWindow,
    QVBoxLayout,
    QWidget,
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
        self.layout.setContentsMargins(30,50,30,30)
        self.screen.setLayout(self.layout)

        self.time_label = QLabel()

        time_font = QFont()
        time_font.setPointSize(48)

        self.time_label.setFont(time_font)
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.layout.addWidget(self.time_label)

        self.update_time()

        self.clock_timer = QTimer()
        self.clock_timer.timeout.connect(self.update_time)
        self.clock_timer.start(1000)

    def update_time(self):
        current_time = QTime.currentTime().toString('HH:mm')
        self.time_label.setText(current_time)

app = QApplication(sys.argv)

window = MainWindow()
window.show()

sys.exit(app.exec())
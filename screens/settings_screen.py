from PyQt6.QtCore import Qt, QEvent, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QComboBox,
    QSlider,
)

class SettingsScreen(QWidget):
    back_requested = pyqtSignal()
    volume_preview_requested = pyqtSignal()
    apply_requested = pyqtSignal()
    open_ringtone_screen = pyqtSignal()
    open_background_screen = pyqtSignal()

    def __init__(self):
        super().__init__()

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(30,10,30,10)

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

        self.ringtone_button = QPushButton('Ringtone')
        self.configure_ringtone_button()

        self.background_button = QPushButton('Background')
        self.configure_backround_button()

        self.layout.addStretch()

        self.apply_button = QPushButton('Apply')
        self.configure_apply_button()

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
        self.alarm_volume_slider.installEventFilter(self)

        self.layout.addWidget(self.alarm_volume_slider)

    def eventFilter(self, watched, event):
        if watched is self.alarm_volume_slider:
            if event.type() == QEvent.Type.MouseButtonRelease:
                if event.button() == Qt.MouseButton.LeftButton:
                    self.volume_preview_requested.emit()

        return super().eventFilter(watched, event)

    def configure_ringtone_button(self):
        self.ringtone_button.setFixedHeight(35)
        self.ringtone_button.clicked.connect(self.open_ringtone_screen.emit)

        self.layout.addWidget(self.ringtone_button)

    def configure_backround_button(self):
        self.background_button.setFixedHeight(35)
        self.background_button.clicked.connect(self.open_background_screen.emit)

        self.layout.addWidget(self.background_button)

    def configure_apply_button(self):
        self.apply_button.setFixedSize(80,35)

        self.apply_button_layout = QHBoxLayout()
        self.apply_button_layout.addStretch()
        self.apply_button_layout.addWidget(self.apply_button)
        self.apply_button.clicked.connect(self.apply_requested.emit)

        self.layout.addLayout(self.apply_button_layout)

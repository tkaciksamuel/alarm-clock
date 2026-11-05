import shutil
from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QRadioButton,
    QButtonGroup,
    QFileDialog,
    QInputDialog,
    QMessageBox,
)


class RingtoneScreen(QWidget):
    back_requested = pyqtSignal()
    ringtone_imported = pyqtSignal(str)

    def __init__(self):
        super().__init__()

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(30, 10, 30, 30)

        self.header_layout = QHBoxLayout()
        self.layout.addLayout(self.header_layout)

        self.back_button = QPushButton('←')
        self.configure_back_button()

        self.screen_title = QLabel('RINGTONES')
        self.configure_screen_title()

        self.ringtone_group = QButtonGroup()
        self.configure_ringtone_choices()

        self.layout.addStretch()

        self.import_sound_button = QPushButton('+ Import')
        self.configure_import_sound_button()

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

    def configure_screen_title(self):
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)

        self.screen_title.setFont(title_font)
        self.screen_title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.header_layout.addWidget(self.screen_title, 1)
        self.header_layout.addSpacing(40)

    def configure_ringtone_choices(self):
        sounds_folder = Path(__file__).resolve().parent.parent / 'sounds'
        sounds_folder.mkdir(parents=True, exist_ok=True)

        for name in ['Default', 'Bell', 'Chime']:
            self.add_ringtone_choice(name)

        built_in_files = {'default.wav', 'bell.wav', 'chime.wav'}

        for sound_path in sorted(sounds_folder.iterdir()):
            if (
                    sound_path.is_file()
                    and sound_path.suffix.lower() == '.wav'
                    and sound_path.name.lower() not in built_in_files
            ):
                self.add_ringtone_choice(sound_path.name)

        self.set_selected_ringtone('Default')

    def add_ringtone_choice(self, name):
        display_name = Path(name).stem
        display_name = display_name[:1].upper() + display_name[1:]
        button = QRadioButton(display_name)
        button.setProperty('ringtone', name)

        button_font = QFont()
        button_font.setPointSize(18)

        button.setFont(button_font)
        button.setMaximumHeight(60)
        button.setStyleSheet(
            """
            QRadioButton {
                spacing: 16px;
            }

            QRadioButton::indicator {
                width: 26px;
                height: 26px;
            }
            """
        )
        self.ringtone_group.addButton(button)

        # Keeps ringtone choices together under the header
        self.layout.insertWidget(
            len(self.ringtone_group.buttons()),
            button
        )

    def configure_import_sound_button(self):
        self.import_sound_button.setMaximumHeight(45)

        button_font = QFont()
        button_font.setPointSize(12)
        self.import_sound_button.setFont(button_font)

        self.import_sound_button.clicked.connect(self.import_sound)
        self.layout.addWidget(self.import_sound_button)

    def import_sound(self):
        source = self.select_sound_file()

        if source is None:
            return

        sounds_folder = Path(__file__).resolve().parent.parent / 'sounds'

        try:
            sounds_folder.mkdir(parents=True, exist_ok=True)
        except OSError as error:
            QMessageBox.warning(
                self,
                'Import failed',
                f'Could not create the sounds folder:\n{error}'
            )
            return

        destination = self.request_sound_name(source, sounds_folder)

        if destination is None:
            return

        if not self.copy_sound_file(source, destination):
            return

        self.add_ringtone_choice(destination.name)
        self.set_selected_ringtone(destination.name)
        self.ringtone_imported.emit(destination.name)

        QMessageBox.information(
            self,
            'Sound imported',
            f'{destination.name} was imported successfully.'
        )

    def select_sound_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            'Import sound',
            '',
            'WAV files (*.wav)'
        )

        return Path(file_path) if file_path else None

    def request_sound_name(self, source, sounds_folder):
        suggested_name = source.stem

        while True:
            name, accepted = QInputDialog.getText(
                self,
                'Name your ringtone',
                'Ringtone name:',
                text=suggested_name
            )

            if not accepted:
                return None

            name = name.strip()

            if name.lower().endswith('.wav'):
                name = name[:-4].strip()

            suggested_name = name

            if not self.is_valid_sound_name(name):
                QMessageBox.warning(
                    self,
                    'Invalid name',
                    'Enter a valid name without special characters.'
                )
                continue

            destination = sounds_folder / f'{name}.wav'

            if self.sound_name_exists(destination):
                QMessageBox.information(
                    self,
                    'Sound already exists',
                    'A sound with this name already exists. Choose another name'
                )
                continue

            return destination

    def is_valid_sound_name(self, name):
        invalid_characters = '<>:"/\\|?*'
        reserved_names = {
            'CON', 'PRN', 'AUX', 'NUL',
            *(f'COM{number}' for number in range(1, 10)),
            *(f'LPT{number}' for number in range(1, 10))
        }

        return (
                bool(name)
                and not name.endswith('.')
                and name.split('.')[0].upper() not in reserved_names
                and not any(character in invalid_characters for character in name)
                and not any(ord(character) < 32 for character in name)
        )

    def sound_name_exists(self, destination):
        if destination.stem.lower() in {'default', 'bell', 'chime'}:
            return True

        return any(
            path.name.lower() == destination.name.lower()
            for path in destination.parent.iterdir()
        )

    def copy_sound_file(self, source, destination):
        try:
            shutil.copy2(source, destination)
        except OSError as error:
            QMessageBox.warning(
                self,
                'Import failed',
                f'Could not import the sound:\n{error}'
            )
            return False

        return True

    def get_selected_ringtone(self):
        return self.ringtone_group.checkedButton().property('ringtone')

    def set_selected_ringtone(self, ringtone):
        for button in self.ringtone_group.buttons():
            if button.property('ringtone') == ringtone:
                button.setChecked(True)
                break
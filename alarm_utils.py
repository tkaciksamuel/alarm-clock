from PyQt6.QtCore import QTime

def seconds_until_alarm(alarm):
    now = QTime.currentTime()
    alarm_time = QTime.fromString(alarm['time'], 'HH:mm')

    seconds = now.secsTo(alarm_time)
    return seconds % (24 * 60 * 60)
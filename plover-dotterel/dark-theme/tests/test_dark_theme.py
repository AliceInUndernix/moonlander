# Run with QT_QPA_PLATFORM=offscreen. Checks the extension turns the app dark
# from a non-GUI thread (as Plover's engine does) and restores it on stop.
import threading
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from plover_dotterel_dark import DarkTheme

app = QApplication([])
before = app.palette().window().color().name()
ext = DarkTheme(engine=None)
results = {}

def from_engine_thread(call):
    t = threading.Thread(target=call); t.start(); t.join()

from_engine_thread(ext.start)
def check_on():
    results['on'] = (app.style().name(), app.palette().window().color().name())
    from_engine_thread(ext.stop)
    QTimer.singleShot(50, check_off)
def check_off():
    results['off'] = (app.style().name(), app.palette().window().color().name())
    app.quit()
QTimer.singleShot(50, check_on)
app.exec()
print('before', before, 'on', results['on'], 'off', results['off'])
assert results['on'] == ('fusion', '#1e1f22')
assert results['off'][1] == before
print('dark theme ok')

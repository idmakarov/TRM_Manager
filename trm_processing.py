import sys
import traceback

from PyQt5.QtCore import QObject, QRunnable, pyqtSignal, pyqtSlot


class WorkerSignals(QObject):
    """
    The class is purposed to define signals accessable from working thread.
    Inherits from PyQt5.QtCore.QObject.
    """
    result = pyqtSignal(object)
    finish = pyqtSignal()
    error = pyqtSignal(tuple)


class Worker(QRunnable):
    """
    The class is purposed to implement multithreading tools.
    Inherits settings of processor working thread, signals and wrap-up from PyQt5.QtCore.QRunnable.

    Methods
    -------
    run()
        Launch new thread.
    """
    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

    @pyqtSlot()
    def run(self):
        try:
            result = self.fn(*self.args, **self.kwargs)
        except:
            traceback.print_exc()
            exc_type, value = sys.exc_info()[:2]
            self.signals.error.emit((exc_type, value, traceback.format_exc()))
        else:
            self.signals.result.emit(result)
        finally:
            self.signals.finish.emit()

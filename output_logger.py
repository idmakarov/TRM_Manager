from PyQt5.QtCore import QObject


class OutputLogger(QObject):
    """
    The class is purposed for redefine destination of standard output and error output.
    Thus, program output will be written into some GUI object corresponding to selected slot.

    Attributes
    ----------
    io_stream
        Standard output stream.
    severity
        Status of output (normal/error).

    Methods
    -------
    write(text)
        Writes text into an io stream.
    flush
        Forcibly cleans up an io stream.
    """

    class Severity:
        NORMAL = 0
        ERROR = 1

    def __init__(self, io_stream, severity):
        super().__init__()

        self.io_stream = io_stream
        self.severity = severity

    def write(self, text):
        self.io_stream.write(text)
        self.emit_write.emit(text, self.severity)

    def flush(self):
        self.io_stream.flush()

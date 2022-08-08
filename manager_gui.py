import datetime
import os
import sys
import time

from PyQt5 import QtGui
from PyQt5.QtCore import pyqtSlot, QCoreApplication, QDate, QThreadPool, QTimer
from PyQt5.QtWidgets import QFileDialog, QMainWindow, QMessageBox, QRadioButton
from pathlib import Path

import main_window  # Это наш конвертированный файл дизайна
from output_logger import OutputLogger
from print_progress_bar import PrintProgressBar
from trm_manager import TrmManager
from trm_processing import Worker

OUTPUT_LOGGER_STDOUT = OutputLogger(sys.stdout, OutputLogger.Severity.NORMAL)
OUTPUT_LOGGER_STDERR = OutputLogger(sys.stderr, OutputLogger.Severity.ERROR)
LOG_SEPARATOR = '-' * 40
BEGIN_LOG_WITH = 'Start of the session'
END_LOG_WITH = 'End of the session'

sys.stdout = OUTPUT_LOGGER_STDOUT
sys.stderr = OUTPUT_LOGGER_STDERR


class ManagerGui(QMainWindow, main_window.Ui_MainWindow):
    """
    The class is purposed for interaction of GUI with TrmManager logic.
    It uses PyQt5 features to implement the interaction.

    Attributes
    ----------
    browser_dict : dict
        Dictionary to store pointers to text editors in which paths are input.
    directories_dict : dict
        Dictionary to store paths to required files.
    dir_browser_match_dict : dict
        Dictionary to connect directories_dict and browser_dict.
    is_received : bool
        Flag to indicate whether transmittals is received or not.
    is_print : bool
        Flag to indicate whether printing is required or not.
    item_list : list
        List to store databases items.
    mgr : TrmManager
        Transmittal manager instance.
    send_date : str
        String to store sending date.
    timer : PyQt5.QtCore.QTimer
        Internal timer.
    threadpool : PyQt5.QtCore.QThreadPool
        Tool to launch threads.
    _translate : PyQt5.QtCore.QCoreApplication.translate
        Method to translate string if required.

    Methods
    -------
    add_items(item_list)
        Displays all accessable items of the database.
    append_log(text: str, severity: int)
        Append string to the console display with format corresponding to its severity.
    browse_folder()
        Opens a standard file dialog and save path choosen in directories dictionary.
    check_list_display()
        Checks left display whether it is empty or not.
    check_list_process()
        Checks right display whether it is empty or not and enable or disable "start processing" button.
    choose_option()
        Chooses further strategy of transmittals processing.
    clear_all()
        Drags all the elements listed in the right display and drops them to the left display.
    clear_radiobutton(radiobutton: QRadioButton)
        Clear radiobuttons if checked.
    define_slot()
        Defines to show or hide GUI elements at the first steps.
    drag_all()
        Drags all the elements listed in the left display and drops them to the right display.
    goto_start()
        Shows "goto start" button.
    init_and_update_trm_in_thread()
        Creates TrmManager instance and update database.
    init_connections()
        Initialize signals and slots.
    init_elements()
        Initialize GUI elements.
    process_item_in_thread(item_ids)
        Processes selected items of database.
    process_trm()
        Creates and launches thread to process selected items.
    show_btn_further()
        Shows "further" button.
    show_message(title, text)
        Show message box with title and text provided.
    set_send_date()
        Saves sending date to attribute and hides dock widget.
    start_program()
        Initializes all GUI elements required to complete preparation stage before processing.
    update_trm()
        Creates and launches thread to initialize and update database of TrmManager instance.
    """

    def __init__(self):
        # Это нужно для доступа к переменным, методам родительских классов
        super().__init__()
        self.setupUi(self)  # Это нужно для инициализации нашего дизайна
        OUTPUT_LOGGER_STDOUT.emit_write.connect(self.append_log)
        OUTPUT_LOGGER_STDERR.emit_write.connect(self.append_log)

        self.first_log_row = ''
        self.timer = QTimer()
        self.is_received = False
        self.is_print = False
        self.mgr = None
        self.directories_dict = {
            'trm': '',
            'vdr': '',
            'print': ''
        }
        self.dir_browser_match_dict = {
            'btnBrowse': 'trm',
            'btnBrowse_2': 'vdr',
            'btnBrowse_3': 'print'
        }
        self.browser_dict = {
            'btnBrowse': self.textBrowser,
            'btnBrowse_2': self.textBrowser_2,
            'btnBrowse_3': self.textBrowser_3
        }

        self.item_list = None
        self.send_date = None
        self._translate = QCoreApplication.translate

        self.init_elements()
        self.init_connections()
        self.threadpool = QThreadPool()

    @staticmethod
    def clear_radiobutton(radiobutton: QRadioButton):
        """
        Clear radiobuttons if checked.

        Parameters
        ----------
        radiobutton : PyQt5.QtWidgets.QRadioButton

        Returns
        -------
        None
        """
        if radiobutton.isChecked():
            radiobutton.setAutoExclusive(False)
            radiobutton.setChecked(False)
            radiobutton.setAutoExclusive(True)

    def init_elements(self):
        """
        Initialize GUI elements.

        Returns
        -------
        None
        """
        if self.btnBrowse.isHidden():
            self.btnBrowse.show()
            self.textBrowser.show()
            self.textBrowser.clear()

            self.btnBrowse_2.show()
            self.textBrowser_2.show()
            self.textBrowser_2.clear()

        self.clear_radiobutton(self.btnSendOps)
        self.clear_radiobutton(self.btnReceiveOps)
        self.clear_radiobutton(self.btnReceiveOpsProcess)
        self.clear_radiobutton(self.btnReceiveOpsPrint)

        if self.chkApplyDateToAll.isChecked():
            self.chkApplyDateToAll.setChecked(False)

        self.btnGotoStart.hide()
        self.btnFurther.hide()
        self.btnStart.hide()
        self.btnDragAll.hide()
        self.btnClearAll.hide()
        self.splitter.hide()
        self.splitter_2.hide()
        self.consoleOutput.hide()
        self.groupBox.hide()
        self.groupBox_2.hide()
        self.btnBrowse_3.hide()
        self.textBrowser_3.clear()
        self.textBrowser_3.hide()
        self.dockWidget.hide()

    def init_connections(self):
        """
        Initialize signals and slots.

        Returns
        -------
        None
        """
        self.btnBrowse.clicked.connect(self.browse_folder)
        self.btnBrowse_2.clicked.connect(self.browse_folder)
        self.btnBrowse_3.clicked.connect(self.browse_folder)
        self.timer.timeout.connect(self.check_list_process)
        self.btnFurther.pressed.connect(self.define_slot)
        self.btnStart.pressed.connect(self.process_trm)
        self.btnGotoStart.pressed.connect(self.init_elements)
        self.btnSendOps.pressed.connect(self.choose_option)
        self.btnReceiveOps.pressed.connect(self.choose_option)
        self.btnReceiveOpsProcess.pressed.connect(self.choose_option)
        self.btnReceiveOpsPrint.pressed.connect(self.choose_option)
        self.btnDragAll.pressed.connect(self.drag_all)
        self.btnClearAll.pressed.connect(self.clear_all)
        self.btnConfirm.pressed.connect(self.set_send_date)
        self.textBrowser.textChanged['QString'].connect(self.show_btn_further)
        self.textBrowser_2.textChanged['QString'].connect(self.show_btn_further)

    @pyqtSlot()
    def drag_all(self):
        """
        Drags all the elements listed in the left display and drops them to the right display.

        Returns
        -------
        None
        """
        list_len = self.listDisplay.count()
        for i in range(list_len):
            self.listProcess.addItem(self.listDisplay.item(i).text())
        self.listDisplay.clear()

    @pyqtSlot()
    def clear_all(self):
        """
        Drags all the elements listed in the right display and drops them to the left display.

        Returns
        -------
        None
        """
        list_len = self.listProcess.count()
        for i in range(list_len):
            self.listDisplay.addItem(self.listProcess.item(i).text())
        self.listProcess.clear()

    @pyqtSlot()
    def define_slot(self):
        """
        Defines to show or hide GUI elements at the first steps.

        Returns
        -------
        None
        """
        if not self.btnBrowse.isHidden():
            self.btnBrowse.hide()
            self.textBrowser.hide()
            self.btnBrowse_2.hide()
            self.textBrowser_2.hide()

            self.groupBox.show()
        else:
            self.groupBox.hide()
            self.groupBox_2.hide()
            self.btnBrowse_3.hide()
            self.textBrowser_3.hide()

            self.start_program()

    @staticmethod
    def show_message(title: str, text: str):
        """
        Show message box with title and text provided.

        Returns
        -------
        None
        """
        alert = QMessageBox()
        alert.setWindowTitle(title)
        alert.setText(text)
        alert.exec_()

    def goto_start(self):
        """
        Shows "goto start" button.

        Returns
        -------
        None
        """
        self.btnGotoStart.show()

    def append_log(self, text: str, severity: int):
        """
        Append string to the console display with format corresponding to its severity.

        Parameters
        ----------
        text : str
        severity : {0, 1}
            0 - normal state, 1 - error.

        Returns
        -------
        None
        """
        cursor = QtGui.QTextCursor()
        fmt = QtGui.QTextCharFormat()

        def get_selected_line():
            self.consoleOutput.moveCursor(cursor.End, cursor.MoveAnchor)
            self.consoleOutput.moveCursor(cursor.StartOfLine, cursor.MoveAnchor)
            self.consoleOutput.moveCursor(cursor.End, cursor.KeepAnchor)
            selected = self.consoleOutput.textCursor().selectedText()
            return selected

        def format_text():
            selected_line = get_selected_line()

            if severity == OutputLogger.Severity.ERROR:
                fmt.setFontWeight(QtGui.QFont.Bold)
                fmt.setForeground(QtGui.QColorConstants.Red)
                self.consoleOutput.textCursor().mergeCharFormat(fmt)
            else:
                fmt.setFontWeight(QtGui.QFont.Normal)
                fmt.setForeground(QtGui.QColorConstants.Black)
                self.consoleOutput.textCursor().mergeCharFormat(fmt)

        text = text.strip('\n')
        selected_line = get_selected_line()
        if 'Progress' in selected_line and r'%' in selected_line and 'Progress' in text and r'%' in text:
            self.consoleOutput.textCursor().removeSelectedText()
            self.consoleOutput.textCursor().deletePreviousChar()

        self.consoleOutput.append(text)
        format_text()

        selected_line = get_selected_line()
        if not selected_line:
            self.consoleOutput.textCursor().deletePreviousChar()
        self.consoleOutput.moveCursor(cursor.End, cursor.MoveAnchor)

    @pyqtSlot()
    def browse_folder(self):
        """
        Opens a standard file dialog and save path choosen in directories dictionary.

        Returns
        -------
        None
        """
        sender = self.sender()
        btn_name = sender.objectName()
        # открыть диалог выбора директории и установить значение переменной, равной пути к выбранной директории
        directory = QFileDialog.getExistingDirectory(self, "Выберите папку")

        if directory:  # не продолжать выполнение, если пользователь не выбрал директорию
            key = self.dir_browser_match_dict[btn_name]
            self.directories_dict[key] = directory

            text_browser = self.browser_dict[btn_name]
            text_browser.clear()  # На случай, если в поле уже была информация
            text_browser.setText(str(directory))

    @pyqtSlot()
    def choose_option(self):
        """
        Chooses further strategy of transmittals processing.

        Returns
        -------
        None
        """
        sender = self.sender()
        if sender.objectName() == 'btnSendOps':
            self.is_received = False
            self.is_print = False
            if not self.groupBox_2.isHidden():
                self.btnBrowse_3.hide()
                self.textBrowser_3.hide()
                self.clear_radiobutton(self.btnReceiveOpsProcess)
                self.clear_radiobutton(self.btnReceiveOpsPrint)
                self.groupBox_2.hide()
            self.btnFurther.show()
        elif sender.objectName() == 'btnReceiveOps':
            self.is_received = True
            self.btnFurther.hide()
            self.groupBox_2.show()
        elif sender.objectName() == 'btnReceiveOpsProcess':
            self.is_print = False
            self.btnBrowse_3.hide()
            self.textBrowser_3.hide()
            self.btnFurther.show()
        elif sender.objectName() == 'btnReceiveOpsPrint':
            self.btnFurther.hide()
            self.is_print = True
            self.btnBrowse_3.show()
            self.textBrowser_3.show()

    @pyqtSlot()
    def set_send_date(self):
        """
        Saves sending date to attribute and hides dock widget.

        Returns
        -------
        None
        """
        self.send_date = self.dateEdit.text()
        self.dockWidget.hide()

    @pyqtSlot()
    def show_btn_further(self):
        """
        Shows "further" button.

        Returns
        -------
        None
        """
        if self.textBrowser.text() and self.textBrowser_2.text():
            self.btnFurther.show()

    def start_program(self):
        """
        Initializes all GUI elements required to complete preparation stage before processing.

        Returns
        -------
        None
        """
        datetime_now = datetime.datetime.now()
        qdate_now = QDate(datetime_now)
        print(LOG_SEPARATOR)

        self.first_log_row = f"{datetime_now.strftime('%d.%m.%Y %H:%M:%S')} {BEGIN_LOG_WITH}"
        print(self.first_log_row)

        if self.is_print:
            self.label.setText(self._translate("MainWindow", "Список доступных VDR"))
            self.label_2.setText(self._translate("MainWindow", "Список VDR для обработки"))
            self.listProcess.setToolTip(
                self._translate("MainWindow", "Положите сюда VDR из списка доступных VDR")
            )
            self.listDisplay.setToolTip(
                self._translate("MainWindow", "Перетащите VDR в список VDR для обработки")
            )

        self.splitter.show()
        self.splitter_2.show()
        self.splitter.setEnabled(True)
        self.splitter_2.setEnabled(True)
        self.listDisplay.clear()
        self.listProcess.clear()
        self.consoleOutput.show()
        self.btnStart.show()
        self.btnStart.setEnabled(False)
        self.btnDragAll.show()
        self.btnClearAll.show()
        self.btnDragAll.setEnabled(True)
        self.btnClearAll.setEnabled(True)
        self.dateEdit.setDate(qdate_now)
        QTimer.singleShot(100, self.update_trm)

    def init_and_update_trm_in_thread(self):
        """
        Creates TrmManager instance and update database.

        Returns
        -------
        None
        """
        trm_path = self.directories_dict['trm']
        vdr_path = self.directories_dict['vdr']
        print_path = self.directories_dict['print']
        self.mgr = TrmManager(trm_path, vdr_path, print_path)
        self.mgr.update_db(self.is_received)
        self.item_list = self.mgr.db.get_item_names()

        if self.is_print:
            process_list = [item for item in self.item_list if 'TRM' not in item]
        else:
            process_list = [item for item in self.item_list if 'TRM' in item]

        return process_list

    def add_items(self, item_list):
        """
        Displays all accessable items of the database.

        Returns
        -------
        None
        """
        self.listDisplay.addItems(item_list)

    def check_list_display(self):
        """
        Checks left display whether it is empty or not.

        Returns
        -------
        None
        """
        if not self.listDisplay.count():
            self.goto_start()
            title = 'Сообщение об ошибке'
            text = 'Нет доступных трансмиттелов для обработки! Попробуйте заново.'
            self.show_message(title=title, text=text)

    def update_trm(self):
        """
        Creates and launches thread to initialize and update database of TrmManager instance.

        Returns
        -------
        None
        """
        trm_updater = Worker(self.init_and_update_trm_in_thread)
        trm_updater.signals.result.connect(self.add_items)
        trm_updater.signals.finish.connect(self.check_list_display)

        try:
            self.threadpool.start(trm_updater)
        except Exception as e:
            print(e, file=sys.stderr)

        self.timer.start(100)

    @pyqtSlot()
    def check_list_process(self):
        """
        Checks right display whether it is empty or not and enable or disable "start processing" button.

        Returns
        -------
        None
        """
        if self.listProcess.count():
            self.btnStart.setEnabled(True)
        elif self.btnStart.isEnabled():
            self.btnStart.setEnabled(False)

    def process_item_in_thread(self, item_ids: list):
        """
        Processes selected items of database.

        Parameters
        ----------
        item_ids : list
            Item indices.

        Returns
        -------
        None
        """
        if self.is_received:
            if self.is_print:
                for item_id in item_ids:
                    vdr = self.mgr.db.get_item(item_id)
                    print('Phase {} documents preparation for printing begins. '
                          'It will take some time...'.format(vdr.phase))
                    self.mgr.prepare_docs_for_printing(vdr)
            else:
                print('Received transmittals processing begins. It will take some time...')

                for item_id in item_ids:
                    trm = self.mgr.db.get_item(item_id)
                    self.mgr.process_received_transmittals(trm)
        else:
            for item_id in item_ids:
                trm = self.mgr.db.get_item(item_id)
                if not trm.documents:
                    print(f'WARNING: there are no documents in {trm.name}', file=sys.stderr)
                else:
                    print('{} processing begins. It will takes some time...'.format(trm.name))
                    if not self.chkApplyDateToAll.isChecked():
                        self.dockWidget.show()
                        while not self.dockWidget.isHidden():
                            time.sleep(0.1)
                    self.mgr.parse_trm_docs(trm, self.send_date)
                    self.mgr.create_crs(trm)
                    self.mgr.create_trm_inventory(trm, self.send_date)

    def get_all_logs(self):
        """
        Gets all logs from app terminal

        Returns
        -------
        str
        """
        text = self.first_log_row + self.consoleOutput.toPlainText().rsplit(sep=self.first_log_row, maxsplit=1)[-1]
        return text

    def export_logs_to_file(self):
        """
        Exports all logs from terminal to file.

        Returns
        -------
        None
        """
        date_str = datetime.datetime.now().strftime('%d%m%y_%H%M%S')
        filename = "LOGS_" + date_str + '.txt'
        path = os.path.join(os.path.abspath(os.getcwd()), 'LOGS')

        Path(path).mkdir(parents=True, exist_ok=True)

        text = self.get_all_logs()

        with open(file=f'LOGS/{filename}', mode='w', encoding="utf-8") as f:
            f.write(text)

    @pyqtSlot()
    def process_trm(self):
        """
        Creates and launches thread to process selected items.

        Returns
        -------
        None
        """
        def complete():
            title = 'Сообщение'
            if self.is_print:
                text = 'Документы подготовлены для печати.'
            elif self.is_received:
                text = 'Обработка полученных трансмиттелов успешно завершена!'
            else:
                text = 'Подготовка трансмиттелов к отправке успешно завершена!'
            self.show_message(title=title, text=text)

            datetime_now = datetime.datetime.now()
            end_str = f"{datetime_now.strftime('%d.%m.%Y %H:%M:%S')} {END_LOG_WITH}"
            print(end_str)

            self.export_logs_to_file()
            self.goto_start()

        self.timer.stop()
        self.btnStart.setEnabled(False)
        self.splitter.setEnabled(False)
        self.splitter_2.setEnabled(False)
        self.btnDragAll.setEnabled(False)
        self.btnClearAll.setEnabled(False)

        item_ids = []
        list_len = self.listProcess.count()
        for i in range(list_len):
            item_name = self.listProcess.item(i).text()
            item_ids.append(self.item_list.index(item_name))

        item_processor = Worker(self.process_item_in_thread, item_ids)
        try:
            self.threadpool.start(item_processor)
        except Exception as e:
            print(e, file=sys.stderr)

        item_processor.signals.finish.connect(complete)

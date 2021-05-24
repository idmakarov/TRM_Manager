import sys  # sys нужен для передачи argv в QApplication

from PyQt5.QtWidgets import QApplication

from manager_gui import ManagerGui


def main():
    app = QApplication(sys.argv)  # Новый экземпляр QApplication
    window = ManagerGui()  # Создаём объект класса ManagerGui
    window.show()  # Показываем окно
    app.exec_()  # и запускаем приложение


if __name__ == '__main__':  # Если мы запускаем файл напрямую, а не импортируем
    main()  # то запускаем функцию main()

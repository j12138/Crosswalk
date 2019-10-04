import sys
import os
import time
import logging
from PyQt5.QtWidgets import QMessageBox, QApplication, \
    QWidget, QDesktopWidget, QHBoxLayout, QVBoxLayout, QPushButton, QGroupBox, \
    QLabel, QStyle, QStyleFactory, \
    QFileDialog, QLineEdit, QProgressBar
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, pyqtSignal, QEventLoop, QTimer, QThread, QWaitCondition, QMutex
from labeling_tool import LabelingTool, DataSelector
from preprocess import PreprocessThread
import server

sys.path.append(os.path.join(os.path.dirname(sys.argv[0]), "lib"))

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

'''
logging.basicConfig(filename=os.path.join(BASE_DIR, 'error_log.log'),
                    level=logging.WARNING,
                    format='[%(asctime)s][%(levelname)s][%(filename)s:%(lineno)d] %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')
'''

# logger = logging.getLogger(__name__)


startTime = 0

print(os.environ.get('FROZEN'))

def put_window_on_center_of_screen(window):
    qr = window.frameGeometry()
    cp = QDesktopWidget().availableGeometry().center()
    qr.moveCenter(cp)
    window.move(qr.topLeft())


class MainWindow(QWidget):
    """
    PyQt UI widget for main window
    """
    window_switch_signal = pyqtSignal(str)

    def __init__(self):
        QWidget.__init__(self)
        self.setWindowTitle('Crosswalk Data Manager')
        self.initUI()

    def initUI(self):
        app_name = QLabel('Crosswalk Data Manager')
        test = QFont("Calibri", 24)
        test.setBold(10)
        app_name.setFont(test)
        app_name.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)

        btn_styleSheet = "QPushButton{font-size: 24px;font-family: Calibri;}"
        btn_preprocess = QPushButton('Preprocess')
        btn_preprocess.clicked.connect(self.__do_preprocess)
        btn_preprocess.setFixedHeight(40)
        btn_preprocess.setFixedWidth(200)
        btn_preprocess.setStyleSheet(btn_styleSheet)

        btn_labeling = QPushButton('Labeling')
        btn_labeling.clicked.connect(self.__do_labeling)
        btn_labeling.setFixedHeight(40)
        btn_labeling.setFixedWidth(200)
        btn_labeling.setStyleSheet(btn_styleSheet)

        btn_upload = QPushButton('Upload DB')
        btn_upload.clicked.connect(self.__do_upload_DB)
        btn_upload.setFixedHeight(40)
        btn_upload.setFixedWidth(200)
        btn_upload.setStyleSheet(btn_styleSheet)

        copyright = QLabel('ⓒ2019. Batoners Inc. All Rights Reserved')

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        main_layout.addStretch(2)
        main_layout.addWidget(app_name)
        main_layout.addStretch(5)

        main_layout.addWidget(btn_preprocess)
        main_layout.setAlignment(btn_preprocess, Qt.AlignHCenter)
        main_layout.addStretch(1)

        main_layout.addWidget(btn_labeling)
        main_layout.setAlignment(btn_labeling, Qt.AlignHCenter)
        main_layout.addStretch(1)

        main_layout.addWidget(btn_upload)
        main_layout.setAlignment(btn_upload, Qt.AlignHCenter)
        main_layout.addStretch(5)

        main_layout.addWidget(copyright)

        self.resize(470, 350)
        put_window_on_center_of_screen(self)

    def __do_preprocess(self):
        self.window_switch_signal.emit('preprocess')

    def __do_labeling(self):
        self.window_switch_signal.emit('labeling')

    def __do_upload_DB(self):
        self.window_switch_signal.emit('upload')


class PreprocessWindow(QWidget):
    window_switch_signal = pyqtSignal(str, str, int)

    def __init__(self):
        QWidget.__init__(self)
        self.setWindowTitle('Preprocess')
        self.data_dir = ''
        self.progress_bar = QProgressBar()
        self.initUI()

    def initUI(self):
        self.select_label = QLabel('Select data to preprocess :')
        self.btn_filedialog = QPushButton(' Browse.. ')
        self.textbox_datadir = QLineEdit()
        self.btn_filedialog.clicked.connect(self.select_directory)
        self.btn_filedialog.setFixedWidth(150)
        self.userID_label = QLabel('User ID :')
        self.textbox_userID = QLineEdit()
        self.textbox_userID.setFixedWidth(200)
        self.btn_start = QPushButton('Start Preprocess')
        self.btn_start.clicked.connect(self.start_preprocess)
        self.btn_start.setFixedHeight(50)
        self.btn_start.setFixedWidth(150)
        self.btn_start.setStyleSheet("background-color: skyblue")

        self.error_msg = QMessageBox()
        self.error_msg.setIcon(QMessageBox.Critical)
        self.error_msg.setWindowTitle('Error')
        self.error_msg.setStandardButtons(QMessageBox.Cancel)

        self.done_msg = QMessageBox()
        self.done_msg.setWindowTitle('Complete')
        self.done_msg.setStandardButtons(QMessageBox.Cancel)

        # More widgets here

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        browse_layout = QHBoxLayout()
        browse_layout.addWidget(self.textbox_datadir)
        browse_layout.addWidget(self.btn_filedialog)
        browse_layout.setSpacing(10)

        userID_layout = QHBoxLayout()
        userID_layout.addWidget(self.userID_label)
        userID_layout.addWidget(self.textbox_userID)
        userID_layout.addStretch(10)

        start_layout = QHBoxLayout()
        start_layout.addWidget(self.btn_start, Qt.AlignCenter)

        main_layout.addStretch(1)
        main_layout.addWidget(self.select_label)
        main_layout.addLayout(browse_layout)
        main_layout.addStretch(1)
        main_layout.addLayout(userID_layout)
        main_layout.addStretch(2)
        main_layout.addLayout(start_layout)
        main_layout.addStretch(2)
        main_layout.addWidget(self.progress_bar)
        main_layout.addStretch(15)
        # Organize layout here

        self.resize(600, 500)
        put_window_on_center_of_screen(self)

    def select_directory(self):
        picked_dir = str(QFileDialog.getExistingDirectory(self,
                         "Select Directory"))
        self.data_dir = picked_dir
        self.textbox_datadir.setText(self.data_dir)

    def start_preprocess(self):
        if self.textbox_userID.text() == '':
            self.error_msg.setText('Please write User ID  ')
            self.error_msg.exec_()
            print('userID: blank!')
        elif ' ' in self.textbox_userID.text():
            self.error_msg.setText('User ID cannot contain any space  ')
            self.error_msg.exec_()
            print('userID: space!')
        elif self.textbox_datadir.text() == '':
            self.error_msg.setText('Please choose data directory  ')
            self.error_msg.exec_()
            print('data_dir: blank!')
        else:
            self.btn_start.setDisabled(True)
            self.btn_start.setStyleSheet("background-color: grey")

            try:
                self.thread = PreprocessThread(self.textbox_datadir.text(),
                                               self.textbox_userID.text())

            except Exception as e:
                if '_getexif' in str(e):
                    self.error_msg.setText('Invalid data: can`t get embedded metadata(_getexif)')
                    self.error_msg.exec_()
                    self.btn_start.setEnabled(True)
                    self.btn_start.setStyleSheet("background-color: skyblue")
                else:
                    self.error_msg.setText('Unknown error: ' + str(e))
                    self.error_msg.exec_()
                    self.btn_start.setEnabled(True)
                    self.btn_start.setStyleSheet("background-color: skyblue")

            else:  
                self.thread.change_value.connect(self._change_progress_bar_value)
                self.thread.start()

            # self.window_switch_signal.emit(self.textbox_datadir.text(),
            #                                self.textbox_userID.text(), 1)
        pass
    
    def _change_progress_bar_value(self, int):
        self.progress_bar.setValue(int)
        if int >= 100:
            print('done!')
            self.btn_start.setEnabled(True)
            self.btn_start.setStyleSheet("background-color: skyblue")

            self.done_msg.setText('Complete preprocessing {} images!'.format(self.thread.numdata))
            self.done_msg.exec_()

    def closeEvent(self, event):
        self.window_switch_signal.emit(None,
                                       None, 2)


class UploadWindow(QWidget):
    window_switch_signal = pyqtSignal()

    def __init__(self):
        QWidget.__init__(self)
        self.setWindowTitle('Upload to Server')
        self.initUI()

    def initUI(self):
        self.select_label = QLabel('Data directory to upload :')
        self.btn_filedialog = QPushButton(' Browse.. ')
        self.btn_filedialog.clicked.connect(self.select_directory)
        self.textbox_datadir = QLineEdit()
        self.btn_filedialog.setFixedWidth(150)
        self.btn_upload = QPushButton('Upload all DB')
        self.btn_upload.clicked.connect(self.upload_all_db)
        self.btn_upload.setFixedHeight(50)
        self.btn_upload.setFixedWidth(150)
        self.btn_upload.setStyleSheet("background-color: skyblue")
        self.textbox_log = QLineEdit()
        self.textbox_log.setReadOnly(True)
        self.textbox_log.setFixedHeight(200)

        self.error_msg = QMessageBox()
        self.error_msg.setIcon(QMessageBox.Critical)
        self.error_msg.setWindowTitle('Error')
        self.error_msg.setStandardButtons(QMessageBox.Cancel)

        self.complete_msg = QMessageBox()
        self.complete_msg.setWindowTitle('Complete')
        self.error_msg.setStandardButtons(QMessageBox.Cancel)

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        browse_layout = QHBoxLayout()
        browse_layout.addWidget(self.textbox_datadir)
        browse_layout.addWidget(self.btn_filedialog)
        browse_layout.setSpacing(10)

        upload_layout = QHBoxLayout()
        upload_layout.addWidget(self.btn_upload, Qt.AlignCenter)

        # main_layout.addWidget(gbox_login)
        main_layout.addStretch(1)
        main_layout.addWidget(self.select_label)
        main_layout.addLayout(browse_layout)
        main_layout.addStretch(2)
        main_layout.addLayout(upload_layout)
        main_layout.addStretch(2)
        # main_layout.addWidget(self.textbox_log)
        main_layout.addStretch(2)

        self.resize(600, 500)
        put_window_on_center_of_screen(self)

    def select_directory(self):
        try:
            picked_dir = str(QFileDialog.getExistingDirectory(self,
                         "Select Directory"))
        except Exception as e:
            # logging.error(e)
            self.error_msg.setText('Unknown error: ' + str(e))
            self.error_msg.exec_()

        self.data_dir = picked_dir
        self.textbox_datadir.setText(self.data_dir)

    def upload_all_db(self):
        self.btn_upload.setDisabled(True)
        self.btn_upload.setStyleSheet("background-color: grey")

        if self.textbox_datadir.text() == '':
            self.error_msg.setText('Please choose data directory  ')
            self.error_msg.exec_()
            print('datadir: blank!')
        else:
            # Time for disabling button
            wait_loop = QEventLoop()
            QTimer.singleShot(1000, wait_loop.quit)
            wait_loop.exec_()

            try:
                server.main(True, None, None,
                            self.textbox_datadir.text(),
                            ui_callback=self.update_upload_log)

                self.complete_msg.setText('Complete uploading DB!')
                self.complete_msg.exec_()
                
            except Exception as e:
                print(e)
                if 'Authentication failed' in str(e):
                    self.error_msg.setText('Authentication faild.\nCheck your ID/PW.')
                    self.error_msg.exec_()
                elif 'Unable to connect' in str(e):
                    self.error_msg.setText('Unable to connect to server.\nCheck your networt or Try later.')
                    self.error_msg.exec_()
                else:
                    self.error_msg.setText('Failed to upload.\nCheck you network and try again, or contact developer.')
                    self.error_msg.exec_()
                    # logging.error(e)

        self.btn_upload.setStyleSheet("background-color: skyblue")
        self.btn_upload.setDisabled(False)

    def update_upload_log(self, img, location):
        if location == 1:  # in ./preprocessed
            print('why')
            self.textbox_log.setText(self.textbox_log.text() + '\n' + img)
            pass
        elif location == 2:
            self.textbox_log.setText(self.textbox_log.text() + '\n' + img)
            pass
        else:
            print('cant be reached!')

    def closeEvent(self, event):
        self.window_switch_signal.emit()


class Controller:
    """
    Controller class for switching windows
    """
    def __init__(self):
        # self.lc = LabelingController()
        self.main_window = MainWindow()
        self.selector = DataSelector()

    def show_main_window(self):
        self.__init__()
        self.main_window.window_switch_signal.connect(self.show_operation_window)
        self.main_window.show()
        print("test point reached!-!")
        return

    def show_operation_window(self, operation):
        if operation == 'preprocess':
            self.preprocess_window = PreprocessWindow()
            self.preprocess_window.window_switch_signal.connect(self.show_progress)
            self.main_window.close()
            self.preprocess_window.show()

        elif operation == 'labeling':
            file_dialog_result = 'Retry'
            while file_dialog_result == 'Retry':
                print('Retry loop')
                try:
                    file_dialog_result = self.selector.set_data_dir()
                except Exception as e:
                    print('error')
                    # logging.error(e)

            print('esacpe loop!')
            if file_dialog_result == 'Close':
                print('catch close!')
                return

            self.show_selector()
            self.selector.put_window_on_center_of_screen()

        elif operation == 'upload':
            self.upload_db_window = UploadWindow()
            self.upload_db_window.window_switch_signal.connect(self.show_main_window)
            self.main_window.close()
            self.upload_db_window.show()

        return

    def show_progress(self, chosen_dir, userid, sigint):
        if sigint == 2:
            self.show_main_window()
            return
        return

    def show_selector(self):
        self.selector.window_switch_signal.connect(self.show_tool)
        self.selector.show()
        self.main_window.close()

    def show_tool(self, dir_path, review):
        if dir_path == 'cancel':
            self.show_main_window()
            self.selector.close()
            return

        global startTime
        startTime = time.time()

        if review:
            print('hello!')
            self.tool = LabelingTool(os.path.join(dir_path, 'labeled'), startTime)
        else:
            self.tool = LabelingTool(os.path.join(dir_path, 'preprocessed'), startTime)
        self.tool.window_switch_signal.connect(self.show_main_window)
        self.selector.close()
        self.tool.launch()
        return


if __name__ == "__main__":
    
    app = QApplication(sys.argv)
    app.setStyle(QStyleFactory.create('Fusion'))
    app.setFont(QFont("Calibri", 10))

    controller = Controller()
    controller.show_main_window()

    sys.exit(app.exec())


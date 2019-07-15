# crosswalk labeling tool
# use preprocessed_data images
# input both side of crosswalk --> location / direction(angle)

import argparse
import cv2
import os, sys, glob
import json
import time
from PyQt5.QtWidgets import QMessageBox, QDialog, QApplication, \
    QWidget, QDesktopWidget, QHBoxLayout, QVBoxLayout, QPushButton, QGroupBox, \
    QGridLayout, QLabel, QCheckBox, QRadioButton, QStyle, QStyleFactory, \
    QTableWidget, QTableWidgetItem, QFileDialog
from PyQt5.QtGui import QImage, QPixmap, QFont
from PyQt5.QtCore import Qt, pyqtSignal

# sys.path.append(os.path.abspath(os.path.dirname(__file__)))
# sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
import compute_label_lib as cl
import crosswalk_data as cd

test_dir = os.path.abspath(os.path.dirname(__file__))
print(test_dir)

fixed_w = 400
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
startTime = 0


class LabelingTool(QWidget):
    """
    PyQt UI tool for labeling
    """
    switch_window = pyqtSignal()

    def __init__(self, img_dir, start_time):
        """
        :param img_dir: preprocessed img directory to label.
        """
        super().__init__()
        self.img_dir = img_dir
        self.img_files = glob.glob(self.img_dir + '/*')
        self.img_idx = 0
        self.start_time = start_time

        self.status = cd.LabelingStatus()

        # labeling status members
        self.is_input_finished = False
        self.current_point = [0, (0, 0)]
        self.all_points = [(0, 0)] * 6
        self.is_line_drawn = [False, False, False]

        self.img_to_display = None
        self.data = None
        self.done_img_idx = set()
        self.label_img = QLabel()
        self.widgets = {
            'cb_obscar': QCheckBox('obs_car'),
            'cb_obshuman': QCheckBox('obs_human'),
            'cb_shadow': QCheckBox('shadow'),
            'cb_old': QCheckBox('old'),
            # 'cb_outrange': QCheckBox('out_of_range'),
            'rb_1col': QRadioButton('1 Column'),
            'rb_2col': QRadioButton('2 Columns'),
            'rb_odd2col': QRadioButton('Odd 2 Columns'),
            # 'rb_ratio': [QRadioButton('20'), QRadioButton('40'),
            #              QRadioButton('60'), QRadioButton('80')]
        }
        self.initUI()

    def initUI(self):
        """ Initialize UI components. """

        # button setting
        but_done = QPushButton('Save')
        but_done.setToolTip('Save labeling on DB')
        but_done.setStyleSheet("background-color: skyblue")
        but_done.clicked.connect(self.__get_manual_meta)
        but_invalid = QPushButton('Invalid')
        but_invalid.setToolTip('press if you cannot draw dots')
        but_invalid.setStyleSheet("background-color: red")
        but_invalid.clicked.connect(self.__set_invalid)
        but_next = QPushButton('Next unlabeled')
        but_prev = QPushButton('Prev unlabeled')
        but_next.setToolTip('Move to next img to annotate')
        but_next.clicked.connect(self.__next_unlabeled_img)
        but_prev.clicked.connect(self.__prev_unlabeled_img)

        # Image show
        pixmap = QPixmap(os.path.join(BASE_DIR, 'qimage.png'))
        self.imgsize = pixmap.size()
        self.label_img.setPixmap(pixmap)

        # make metadata widgets
        self.widgets['rb_1col'].setChecked(True)

        # Layout setting
        grid = QGridLayout()
        self.setLayout(grid)

        self.gbox_image = QGroupBox(
            "Image ( 0 / {} ) {}".format(len(self.img_files), test_dir))

        vbox_image = QVBoxLayout()
        vbox_image.addWidget(self.label_img)
        self.gbox_image.setLayout(vbox_image)

        gbox_meta = QGroupBox("Metadata")
        vbox_meta = QVBoxLayout()
        gbox_ratio = QGroupBox("zebra_ratio (%)")
        hbox_ratio = QHBoxLayout()

        vbox_meta.addWidget(self.widgets['cb_obscar'])
        vbox_meta.addWidget(self.widgets['cb_obshuman'])
        vbox_meta.addWidget(self.widgets['cb_shadow'])
        vbox_meta.addWidget(self.widgets['cb_old'])
        vbox_meta.addStretch(2)
        vbox_meta.addWidget(self.widgets['rb_1col'])
        vbox_meta.addWidget(self.widgets['rb_2col'])
        vbox_meta.addWidget(self.widgets['rb_odd2col'])
        vbox_meta.addStretch(2)
        # vbox_meta.addWidget(label_ratio)
        # vbox_meta.addWidget(self.widgets['slider_ratio'])

        # for i in range(len(self.widgets['rb_ratio'])):
        #     hbox_ratio.addWidget(self.widgets['rb_ratio'][i])

        # gbox_ratio.setLayout(hbox_ratio)
        # gbox_ratio.setFont(QFont("calibri", 9))
        # vbox_meta.addWidget(gbox_ratio)

        # slider tick labels
        hbox_tick = QHBoxLayout()
        label_ticks = [QLabel('0'), QLabel('20'), QLabel('40'),
                       QLabel('60'), QLabel('80'), QLabel('100')]
        tick_font = QFont("calibri", 8)

        for i in range(len(label_ticks)):
            if i > 0:
                hbox_tick.addStretch(1)
            label_ticks[i].setFont(tick_font)
            hbox_tick.addWidget(label_ticks[i])

        # vbox_meta.addLayout(hbox_tick)

        vbox_meta.addStretch(1)
        # vbox_meta.addWidget(self.widgets['cb_outrange'])
        vbox_meta.addStretch(4)

        hbox_button1 = QHBoxLayout()
        hbox_button1.addWidget(but_prev)
        hbox_button1.addWidget(but_next)
        vbox_meta.addLayout(hbox_button1)
        vbox_meta.addStretch(1)

        hbox_button2 = QHBoxLayout()
        hbox_button2.addWidget(but_invalid)
        hbox_button2.addWidget(but_done)

        vbox_meta.addLayout(hbox_button2)
        gbox_meta.setLayout(vbox_meta)

        grid.addWidget(self.gbox_image, 0, 0)
        grid.addWidget(gbox_meta, 0, 1)

        self.setWindowTitle('Crosswalk labeling tool')
        self.resize(700, 500)
        self.put_window_on_center_of_screen()
        self.show()

    def launch(self):
        """ Renew the UI by current img to label. """

        # finished expoloring all imgs
        if self.img_idx >= len(self.img_files):
            self.close()
            return

        img_file = self.img_files[self.img_idx]
        self.data = cd.CrosswalkData(img_file)

        self.img_to_display = self.data.img.copy()
        img = self.img_to_display
        self.update_img(img)
        self.__update_screen()
        self.__draw_labeling_status()

        self.update_img(img)

    def put_window_on_center_of_screen(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            img_pos = self.abs2img_pos(event.pos(), self.gbox_image,
                                       self.imgsize)

            print(img_pos)

            if (img_pos[0] < 0) or (img_pos[0] >= self.imgsize.width()):
                return
            if (img_pos[1] < 0) or (img_pos[1] >= self.imgsize.height()):
                return

            if self.is_line_drawn[2]:
                self.is_input_finished = True
                return

            # self.__draw_dot(img_pos)
            # self.update_img(self.img_to_display)

            self.all_points[self.current_point[0]] = img_pos
            self.current_point[0] = self.current_point[0] + 1
            self.current_point[1] = img_pos

            self.__draw_labeling_status()

            # self.__draw_line_and_compute_label()

    def keyPressEvent(self, event):
        """An overridden method from QWidget class to handle event per each key
        press. press.

        :param event: An event object tells which key is pressed :param
        event: An event object tells which key is pressed

        """
        if event.key() == Qt.Key_A:
            # move to previous image (use A instead of <-)
            if self.img_idx > 0:
                self.save_labeling_status()
                self.img_idx = self.img_idx - 1
                self.launch()

        if event.key() == Qt.Key_D:
            # move to next image (use D instead of →)
            if self.img_idx < len(self.img_files) - 1:
                self.save_labeling_status()
                self.img_idx = self.img_idx + 1
                self.launch()

        if event.key() == Qt.Key_1:
            if not self.widgets['rb_1col'].isChecked():
                self.widgets['rb_1col'].setChecked(True)

        if event.key() == Qt.Key_2:
            if not self.widgets['rb_2col'].isChecked():
                self.widgets['rb_2col'].setChecked(True)

        if event.key() == Qt.Key_3:
            if not self.widgets['rb_odd2col'].isChecked():
                self.widgets['rb_odd2col'].setChecked(True)

        if event.key() == Qt.Key_Backspace:
            # print('KeyPress: Backspace (Undo)')
            self.__undo_labeling()

        if event.key() == Qt.Key_Return:
            self.__get_manual_meta()

    def __draw_dot(self, pos):
        ratio = float(self.imgsize.width()) / 300.0
        dot_size = int(3 * ratio)
        cv2.circle(self.img_to_display, pos, dot_size, (255, 0, 0), -1)

    def __draw_line_and_compute_label(self):
        ratio = float(self.imgsize.width()) / 300.0
        line_thickness = int(2 * ratio)

        if self.current_point[0] >= 2 and not self.is_line_drawn[0]:
            cv2.line(self.img_to_display, self.all_points[0],
                     self.all_points[1], (0, 0, 255), line_thickness)
            self.is_line_drawn[0] = True

        if self.current_point[0] >= 4 and not self.is_line_drawn[1]:
            cv2.line(self.img_to_display, self.all_points[2],
                     self.all_points[3], (0, 0, 255), line_thickness)
            self.is_line_drawn[1] = True

        if self.current_point[0] >= 6 and not self.is_line_drawn[2]:
            cv2.line(self.img_to_display, self.all_points[4],
                     self.all_points[5], (0, 255, 255), line_thickness)
            self.is_line_drawn[2] = True
            loc, ang, pit, roll = self.__compute_label()
            self.data.input_labels(loc, ang, pit, roll)
            self.__write_labels_on_screen(str(loc), str(ang), str(pit),
                                          str(roll))
            self.is_input_finished = True

    def __undo_labeling(self):
        if self.current_point[0] == 0:
            return

        idx = self.current_point[0]

        self.is_input_finished = False
        self.current_point = [idx - 1, self.all_points[idx - 1]]
        self.all_points[idx - 1] = (0, 0)
        self.is_line_drawn = [False, False, False]
        self.img_to_display = self.data.img.copy()
        self.__draw_labeling_status()

    def __draw_labeling_status(self):
        for i in range(self.current_point[0]):
            self.__draw_dot(self.all_points[i])

        try:
            self.__draw_line_and_compute_label()
        except Exception as e:
            print('Failed to compute labels :{}'.format(e))
            self.close()

        self.update_img(self.img_to_display)

    def __get_manual_meta(self):
        if not self.is_input_finished:
            print('Do labeling')
            return

        self.data.meta['obs_car'][2] = int(
            self.widgets['cb_obscar'].isChecked())
        self.data.meta['obs_human'][2] = int(
            self.widgets['cb_obshuman'].isChecked())
        self.data.meta['shadow'][2] = int(
            self.widgets['cb_shadow'].isChecked())
        # self.data.meta['out_of_range'][2] = int(
        #     self.widgets['cb_outrange'].isChecked())
        self.data.meta['old'][2] = int(
            self.widgets['cb_old'].isChecked())

        if self.widgets['rb_2col'].isChecked():
            self.data.meta['column'][2] = 2
        if self.widgets['rb_odd2col'].isChecked():
            self.data.meta['column'][2] = 2.5

        '''
        self.data.meta['zebra_ratio'][2] = int(
            self.widgets['slider_ratio'].value() * 2)
        '''
        # self.data.meta['zebra_ratio'][2] = self.__get_ratio_value()

        # self.data.display_manual_meta()
        self.data.write_on_db()
        self.save_labeling_status()
        self.done_img_idx.add(self.img_idx)
        self.img_idx = self.img_idx + 1
        self.launch()

    def __set_invalid(self):
        self.data.set_invalid()
        # self.data.display_labels()
        # self.data.display_manual_meta()

        self.data.write_on_db()
        self.done_img_idx.add(self.img_idx)
        self.save_labeling_status()
        self.img_idx = self.img_idx + 1
        self.launch()

    def __compute_label(self):
        # loc, ang (primary labels)
        h, w = self.img_to_display.shape[:2]

        loc, ang, pit, roll = cl.compute_all_labels(w, h, self.all_points,
                                                    self.widgets['rb_odd2col'].isChecked())

        return round(loc, 3), round(ang, 3), round(pit, 3), round(roll, 3)

    def __write_labels_on_screen(self, loc, ang, pit, roll):
        ratio = float(self.imgsize.width()) / 300.0
        font_size = 0.35 * ratio

        cv2.putText(self.img_to_display,
                    loc + '  ' + ang + '  ' +
                    pit + '  ' + roll, (15, 15),
                    cv2.FONT_HERSHEY_SIMPLEX, font_size, (
                        255, 255, 255),
                    round(3 * ratio))
        cv2.putText(self.img_to_display,
                    loc + '  ' + ang + '  ' +
                    pit + '  ' + roll, (15, 15),
                    cv2.FONT_HERSHEY_SIMPLEX, font_size, (255, 0, 0),
                    round(ratio))

    def abs2img_pos(self, absPos, gbox, imgsize):
        # ratio = fixed_w / float(imgsize.width())

        gw, gh = gbox.size().width(), gbox.size().height()
        iw, ih = imgsize.width(), imgsize.height()
        hb = int((gh - 25 - ih) / 2)
        wb = int((gw - iw) / 2)

        ix = absPos.x() - gbox.pos().x() - wb
        iy = absPos.y() - gbox.pos().y() - 25 - hb

        return int(ix), int(iy)

    def update_img(self, img):
        """ Update img component of UI to current img to display.
        """
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        qimage = QImage(img, img.shape[1], img.shape[0],
                        img.shape[1] * 3, QImage.Format_RGB888)
        pixmap = QPixmap(qimage)
        self.imgsize = pixmap.size()
        # pixmap = pixmap.scaled(400, 450, Qt.KeepAspectRatio)
        self.label_img.setPixmap(pixmap)
        self.gbox_image.setTitle(
            'Image ( {} / {} )'.format(self.img_idx + 1,
                                       len(self.img_files)))

    def save_labeling_status(self):
        """ save current labeling status at DB file.
        """
        self.status.is_input_finished = self.is_input_finished
        self.status.is_line_drawn = self.is_line_drawn
        self.status.current_point = self.current_point
        self.status.all_points = self.all_points

        self.status.widgets_status['cb_obscar'] = \
            self.widgets['cb_obscar'].isChecked()
        self.status.widgets_status['cb_obshuman'] = \
            self.widgets['cb_obshuman'].isChecked()
        self.status.widgets_status['cb_shadow'] = \
            self.widgets['cb_shadow'].isChecked()
        self.status.widgets_status['cb_old'] = \
            self.widgets['cb_old'].isChecked()
        # self.status.widgets_status['cb_outrange'] = \
        #     self.widgets['cb_outrange'].isChecked()

        if self.widgets['rb_1col'].isChecked():
            self.status.widgets_status['rb_1col'] = 1
        elif self.widgets['rb_2col'].isChecked():
            self.status.widgets_status['rb_1col'] = 2
        else:
            self.status.widgets_status['rb_1col'] = 2.5

        # self.status.widgets_status['slider_ratio'] = \
        #     self.__get_ratio_value()

        self.data.save_labeling_status(self.status)

    def __update_screen(self):
        self.status = self.data.load_labeling_status()
        self.current_point = self.status.current_point
        self.all_points = self.status.all_points
        self.is_line_drawn = [False, False, False]
        self.is_input_finished = self.status.is_input_finished

        # Set check widgets default value
        self.widgets['cb_obscar'].setChecked(
            self.status.widgets_status['cb_obscar'])
        self.widgets['cb_obshuman'].setChecked(
            self.status.widgets_status['cb_obshuman'])
        self.widgets['cb_shadow'].setChecked(
            self.status.widgets_status['cb_shadow'])
        self.widgets['cb_old'].setChecked(
            self.status.widgets_status['cb_old'])
        # self.widgets['cb_outrange'].setChecked(
        #     self.status.widgets_status['cb_outrange'])

        if self.status.widgets_status['rb_1col'] == 1:
            self.widgets['rb_1col'].setChecked(True)
        elif self.status.widgets_status['rb_1col'] == 2:
            self.widgets['rb_2col'].setChecked(True)
        else:
            self.widgets['rb_odd2col'].setChecked(True)

        # self.__set_ratio_buttons()

    def __get_ratio_value(self):
        for i in range(len(self.widgets['rb_ratio'])):
            rb = self.widgets['rb_ratio'][i]
            if rb.isChecked():
                return (i + 1) * 20

    def __set_ratio_buttons(self):
        val = self.status.widgets_status['slider_ratio']
        self.widgets['rb_ratio'][int(val / 20) - 1].setChecked(True)

    def __next_unlabeled_img(self):
        """ Go to next unlabeled img. """

        self.save_labeling_status()

        for i in range(len(self.img_files)):
            if (i > self.img_idx) and (i not in self.done_img_idx):
                self.img_idx = i
                self.launch()
                return
        temp = 0
        while(temp in self.done_img_idx):
            temp = temp + 1

        if (temp < len(self.img_files)):
            self.img_idx = temp
        self.launch()

    def __prev_unlabeled_img(self):
        """ Go to previous unlabeled img. """

        self.save_labeling_status()

        total = len(self.img_files)
        for i in range(total):
            j = total - i - 1
            if (j < self.img_idx) and (j not in self.done_img_idx):
                self.img_idx = j
                self.launch()
                return
        temp = total - 1
        while (temp in self.done_img_idx):
            temp = temp - 1
            print(total)

        if (temp > 0):
            self.img_idx = temp
        self.launch()

    def closeEvent(self, event):
        """ This method is called when the window gets 'close()' signal """

        process = 'Labeled img: {} / {}\n\n'.format(len(self.done_img_idx),
                                                    len(self.img_files))
        msg = process + 'Do you want to quit the tool?'
        done_msg = QMessageBox.question(self, 'Message', msg,
                                        QMessageBox.Yes | QMessageBox.No,
                                        QMessageBox.No)

        if done_msg == QMessageBox.No:
            self.img_idx = self.img_idx - 1
            event.ignore()
            return

        self.save_labeling_status()
        save_path = os.path.join(self.img_dir, '..', 'labeled')
        self.__move_done_imgs(save_path)

        print('{} images: {} m'.format(len(self.img_files),
                                       round((time.time() - self.start_time) / 60, 2)))
        self.switch_window.emit()

    def __move_done_imgs(self, save_path):
        """ move labeling done imgs from ./preprocess/ to ./labeled/
        :param save_path: labeled folder of current dataset directory
        """

        for idx in self.done_img_idx:
            img_file = self.img_files[idx]
            os.rename(img_file, os.path.join(save_path,
                                             os.path.split(img_file)[-1]))


class DataSelector(QWidget):
    """
    PyQt UI widget for data selector
    """
    switch_window = pyqtSignal(str)

    def __init__(self):
        QWidget.__init__(self)
        self.setWindowTitle('Data selector')
        self.initUI()

    def set_data_dir(self):
        self.data_dir = self.__get_preprocessed_data_dir()
        self.child_dirs = glob.glob(os.path.join(self.data_dir, '*'))
        self.tableWidget.setRowCount(len(self.child_dirs))
        self.set_TableWidgetData()

    def __get_preprocessed_data_dir(self):
        picked_dir = str(QFileDialog.getExistingDirectory(self,
                                                          "Select Directory"))
        return picked_dir

    def initUI(self):
        self.tableWidget = QTableWidget(self)
        self.tableWidget.resize(415, 400)
        self.tableWidget.setRowCount(1)
        self.tableWidget.setColumnCount(2)
        # self.set_TableWidgetData()

        self.startbutton = QPushButton('Select')
        self.startbutton.clicked.connect(self.start_labeling)
        self.toplabel = QLabel('Select dataset to label: ')

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        main_layout.addWidget(self.toplabel)
        main_layout.addWidget(self.tableWidget)
        main_layout.addWidget(self.startbutton)

        # set Error Message Box
        self.error_msg = QMessageBox()
        self.error_msg.setIcon(QMessageBox.Critical)
        self.error_msg.setWindowTitle('Error')
        self.error_msg.setStandardButtons(QMessageBox.Cancel | QMessageBox.Retry)

        self.resize(500, 500)
        self.put_window_on_center_of_screen()

    def start_labeling(self):
        current_row = self.tableWidget.currentItem().row()
        self.select_done(current_row)

    def set_TableWidgetData(self):
        self.tableWidget.setHorizontalHeaderLabels(['dirname',
                                                    'progress'])
        idx = 0
        total = 0
        labeled = 0

        for dir in self.child_dirs:
            db_file = os.path.join(dir, 'db.json')
            try:
                with open(db_file, 'r') as f:
                    loaded = json.load(f)
            except Exception as e:
                msg = '{}'.format(e)
                self.error_msg.setText(msg)
                print(msg)
                answer = self.error_msg.exec_()
                if answer == QMessageBox.Retry:
                    self.set_data_dir()
                elif answer == QMessageBox.Cancel:
                    self.switch_window.emit('cancel')
                    self.close()
                    print('??????')
                return

            else:
                idx = idx + 1
                tot, lab, dir_name = self.show_labeling_progress_for_each_dir(
                    loaded, dir, idx)
                total = total + tot
                labeled = labeled + lab

                item = QTableWidgetItem(dir_name)
                item.setFlags(Qt.ItemIsEnabled)
                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
                self.tableWidget.setItem(idx - 1, 0, item)

                item = QTableWidgetItem('[ {} / {} ]'.format(str(lab),
                                                             str(tot)))
                item.setFlags(Qt.ItemIsEnabled)
                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignHCenter)
                self.tableWidget.setItem(idx - 1, 1, item)

                self.tableWidget.setRowHeight(idx - 1, 30)

        self.tableWidget.setColumnWidth(0, 300)
        self.tableWidget.setColumnWidth(1, 100)

    def show_labeling_progress_for_each_dir(self, db, dir, idx):
        total = 0
        for name in db.values():
            total = total + 1

        labeled = len(os.listdir(os.path.join(dir, 'labeled')))
        dir_name = os.path.basename(dir)

        return total, labeled, dir_name

    def put_window_on_center_of_screen(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def select_done(self, picked_idx):
        self.switch_window.emit(self.child_dirs[picked_idx])


class LabelingController:
    """
    Controller class for switching windows
    """
    def __init__(self):
        print('labelingCont_init')
        self.selector = DataSelector()
        self.selector.set_data_dir()

    def show_selector(self):
        print('show_selector')
        self.selector.switch_window.connect(self.show_tool)
        self.selector.show()

    def show_tool(self, dir_path):
        print('show_tool')
        global startTime
        startTime = time.time()
        self.tool = LabelingTool(os.path.join(dir_path, 'preprocessed'), startTime)
        self.selector.close()
        self.tool.launch()


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--validate', action="store_true")
    parser.add_argument('data_path', help='Path of folder containing images',
                        default='', type=str)
    return parser.parse_args()


def launch_annotator():
    """ the actual 'main' function.
    Other modules that import this module shall call this as the entry
    point.
    """

    app = QApplication(sys.argv)
    app.setStyle(QStyleFactory.create('Fusion'))
    app.setFont(QFont("Calibri", 10))

    labeling_controller = LabelingController()
    labeling_controller.show_selector()

    sys.exit(app.exec_())


def main(args):
    if (args.validate):
        data_path = os.path.join(args.data_path, 'labeled')
        if len(glob.glob(data_path + '/*')) <= 0:
            print('There are no labeled img')
            return
    else:
        data_path = os.path.join(args.data_path, 'preprocessed')
    launch_annotator()


if __name__ == "__main__":
    if (len(sys.argv) < 2):
        launch_annotator()
        sys.exit(0)

    args = parse_args()
    main(args)

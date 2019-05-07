# crosswalk labeling tool
# use preprocessed_data images
# input both side of crosswalk --> location / direction(angle)

import argparse
import glob
import cv2
import os
import crosswalk_data as cd
import compute_label_lib as cl
from PyQt5.QtWidgets import QMessageBox, QSlider, QDialog, QApplication, \
    QWidget, QDesktopWidget, QHBoxLayout, QVBoxLayout, QPushButton, QGroupBox, \
    QGridLayout, QLabel, QCheckBox, QRadioButton, QStyle, QStyleFactory
from PyQt5.QtGui import QImage, QKeyEvent, QMouseEvent, QPixmap, QFont, \
    QPainter, QCursor, QPalette, QColor
from PyQt5.QtCore import Qt
import sys

fixed_w = 400

class LabelingStatus():
    def __init__(self):
        self.is_input_finished = False
        self.current_point = [0, (0, 0)]
        self.all_points = [(0, 0)] * 6
        self.is_line_drawn = [False, False, False]
        self.widgets_status = {
            'cb_obscar': False,
            'cb_obshuman': False,
            'cb_shadow': False,
            'cb_old': False,
            'cb_outrange': False,
            'rb_1col': True,
            'slider_ratio': 30
        }


class LabelingTool(QWidget):

    def __init__(self, img_dir):
        super().__init__()
        self.img_dir = img_dir
        self.img_files = glob.glob(self.img_dir + '/*')
        self.img_idx = 0
        self.labeling_status = []

        for i in range(len(self.img_files)):
            self.labeling_status.append(LabelingStatus())
        
        self.status = self.labeling_status[self.img_idx]

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
            'cb_outrange': QCheckBox('out_of_range'),
            'rb_1col': QRadioButton('1 Column'),
            'rb_2col': QRadioButton('2 Columns'),
            'slider_ratio': QSlider(Qt.Horizontal)
        }
        self.initUI()

    def initUI(self):
        but_done = QPushButton('Done')
        but_done.clicked.connect(self.__get_manual_meta)
        but_invalid = QPushButton('Invalid')
        but_invalid.setStyleSheet("background-color: red")
        but_invalid.clicked.connect(self.__set_invalid)

        # Image show
        pixmap = QPixmap('qimage.png')
        self.imgsize = pixmap.size()
        self.label_img.setPixmap(pixmap)

        # make metadata widgets
        self.widgets['rb_1col'].setChecked(True)

        label_ratio = QLabel('zebra_ratio')

        self.widgets['slider_ratio'].setRange(0, 50)
        self.widgets['slider_ratio'].setSingleStep(20)
        self.widgets['slider_ratio'].setTickInterval(10)
        self.widgets['slider_ratio'].setTickPosition(2)

        # Layout setting
        grid = QGridLayout()
        self.setLayout(grid)

        self.gbox_image = QGroupBox(
        "Image ( 0 / {} )".format(len(self.img_files)))

        vbox_image = QVBoxLayout()
        vbox_image.addWidget(self.label_img)
        self.gbox_image.setLayout(vbox_image)

        gbox_meta = QGroupBox("Metadata")
        vbox_meta = QVBoxLayout()

        vbox_meta.addWidget(self.widgets['cb_obscar'])
        vbox_meta.addWidget(self.widgets['cb_obshuman'])
        vbox_meta.addWidget(self.widgets['cb_shadow'])
        vbox_meta.addWidget(self.widgets['cb_old'])
        vbox_meta.addStretch(2)
        vbox_meta.addWidget(self.widgets['rb_1col'])
        vbox_meta.addWidget(self.widgets['rb_2col'])
        vbox_meta.addStretch(2)
        vbox_meta.addWidget(label_ratio)
        vbox_meta.addWidget(self.widgets['slider_ratio'])

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

        vbox_meta.addLayout(hbox_tick)

        vbox_meta.addStretch(2)
        vbox_meta.addWidget(self.widgets['cb_outrange'])
        vbox_meta.addStretch(5)

        hbox_button = QHBoxLayout()
        hbox_button.addWidget(but_invalid)
        hbox_button.addWidget(but_done)

        vbox_meta.addLayout(hbox_button)
        gbox_meta.setLayout(vbox_meta)

        grid.addWidget(self.gbox_image, 0, 0)
        grid.addWidget(gbox_meta, 0, 1)

        self.setWindowTitle('Crosswalk labeling tool')
        self.resize(700, 500)
        self.center()
        self.show()

    def launch(self):
        self.__update_screen()
        if self.img_idx >= len(self.img_files):
            msg = 'Labeling all done!\nDo you want to quit the tool?'
            done_msg = QMessageBox.question(self, 'Message', msg,
                                            QMessageBox.Yes | QMessageBox.No,
                                            QMessageBox.No)
            if done_msg == QMessageBox.Yes:
                self.close()
                return
            else:
                self.img_idx = self.img_idx - 1
                return

        img_file = self.img_files[self.img_idx]

        self.data = cd.CrosswalkData(img_file)
        self.img_to_display = self.data.img.copy()
        img = self.img_to_display
        self.__draw_labeling_status()

        self.update_img(img)
        

    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            img_pos = self.abs2img_pos(event.pos(), self.gbox_image,
                                       self.imgsize)

            if (img_pos[0] < 0) or (img_pos[0] >= self.imgsize.width()):
                return
            if (img_pos[1] < 0) or (img_pos[1] >= self.imgsize.height()):
                return

            if self.is_line_drawn[2]:
                self.is_input_finished = True
                return

            #self.__draw_dot(img_pos)
            #self.update_img(self.img_to_display)

            self.all_points[self.current_point[0]] = img_pos
            self.current_point[0] = self.current_point[0] + 1
            self.current_point[1] = img_pos

            self.__draw_labeling_status()

            #self.__draw_line_and_compute_label()
            #self.update_img(self.img_to_display)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_A:
            # move to previous image (use A instead of ←)
            print('KeyPress: A (←)')
            if self.img_idx > 0:
                self.save_labeling_status()
                self.img_idx = self.img_idx - 1
                self.launch()

        if event.key() == Qt.Key_D:
            # move to next image (use D instead of →)
            print('KeyPress: D (→)')
            if self.img_idx < len(self.img_files) - 1:
                self.save_labeling_status()
                self.img_idx = self.img_idx + 1
                self.launch()

        if event.key() == Qt.Key_Backspace:
            print('KeyPress: Backspace (Undo)')
            self.__undo_labeling()

        if event.key() == Qt.Key_T:
            print('하기싫다')
            print('아닙니다')

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
        return

    def __draw_labeling_status(self):
        for i in range(self.current_point[0]):
            self.__draw_dot(self.all_points[i])
        self.__draw_line_and_compute_label()
        self.update_img(self.img_to_display)

    def __get_manual_meta(self):
        if not self.is_input_finished:
            print('Do labeling')
            return

        self.data.meta['obs_car'][2] = int(
            self.widgets['cb_obscar'].isChecked())
        self.data.meta['obs_human'][2] = int(
            self.widgets['cb_obshuman'].isChecked())
        self.data.meta['shadow'][2] = int(self.widgets['cb_shadow'].isChecked())
        self.data.meta['out_of_range'][2] = int(
            self.widgets['cb_outrange'].isChecked())
        self.data.meta['old'][2] = int(self.widgets['cb_old'].isChecked())

        if self.widgets['rb_2col'].isChecked():
            self.data.meta['column'][2] = 2

        self.data.meta['zebra_ratio'][2] = int(
            self.widgets['slider_ratio'].value() * 2)

        self.data.write_on_db()
        self.save_labeling_status()
        self.done_img_idx.add(self.img_idx)
        self.img_idx = self.img_idx + 1
        self.launch()

    def __set_invalid(self):
        self.data.set_invalid()
        self.data.display_labels()
        self.data.display_manual_meta()

        self.data.write_on_db()
        self.done_img_idx.add(self.img_idx)
        self.save_labeling_status()
        self.img_idx = self.img_idx + 1
        self.launch()

    def __compute_label(self):
        # loc, ang (primary labels)
        h, w = self.img_to_display.shape[:2]
        p1 = self.all_points[0]
        p2 = self.all_points[1]
        p3 = self.all_points[2]
        p4 = self.all_points[3]

        left_line = cl.line(p1, p2)
        right_line = cl.line(p3, p4)
        mid_pt, bottom_width = cl.bottom_mid_point_and_width(h, left_line,
                                                             right_line)

        loc = cl.compute_loc(mid_pt, w, bottom_width)
        ang = cl.compute_ang(left_line, right_line, mid_pt, h)

        # pit(ch), roll
        p5 = self.all_points[4]
        p6 = self.all_points[5]

        mid = cl.mid_point(p5, p6)
        slope = cl.line(p5, p6)[0]

        pit = cl.compute_pitch(mid, h)
        roll = cl.compute_roll(slope)

        return round(loc, 3), round(ang, 3), round(pit, 3), round(roll, 3)

    def __write_labels_on_screen(self, loc, ang, pit, roll):
        ratio = float(self.imgsize.width()) / 300.0
        font_size = 0.35 * ratio

        cv2.putText(self.img_to_display,
                    loc + '  ' + ang + '  ' + pit + '  ' + roll, (15, 15),
                    cv2.FONT_HERSHEY_SIMPLEX, font_size, (255, 255, 255),
                    round(3 * ratio))
        cv2.putText(self.img_to_display,
                    loc + '  ' + ang + '  ' + pit + '  ' + roll, (15, 15),
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
        self.labeling_status[self.img_idx].is_input_finished = self.is_input_finished
        self.labeling_status[self.img_idx].is_line_drawn = self.is_line_drawn
        self.labeling_status[self.img_idx].current_point = self.current_point
        self.labeling_status[self.img_idx].all_points = self.all_points

        self.labeling_status[self.img_idx].widgets_status['cb_obscar'] = self.widgets['cb_obscar'].isChecked()
        self.labeling_status[self.img_idx].widgets_status['cb_obshuman'] = self.widgets['cb_obshuman'].isChecked()
        self.labeling_status[self.img_idx].widgets_status['cb_shadow'] = self.widgets['cb_shadow'].isChecked()
        self.labeling_status[self.img_idx].widgets_status['cb_old'] = self.widgets['cb_old'].isChecked()
        self.labeling_status[self.img_idx].widgets_status['cb_outrange'] = self.widgets['cb_outrange'].isChecked()
        self.labeling_status[self.img_idx].widgets_status['rb_1col'] = self.widgets['rb_1col'].isChecked()
        self.labeling_status[self.img_idx].widgets_status['slider_ratio'] = self.widgets['slider_ratio'].value()

    def __update_screen(self):
        self.status = self.labeling_status[self.img_idx]
        self.current_point = self.status.current_point
        self.all_points = self.status.all_points
        self.is_line_drawn = [False, False, False]
        self.is_input_finished = self.status.is_input_finished
        
        # Set check widgets default value
        self.widgets['cb_obscar'].setChecked(self.labeling_status[self.img_idx].widgets_status['cb_obscar'])
        self.widgets['cb_obshuman'].setChecked(self.labeling_status[self.img_idx].widgets_status['cb_obshuman'])
        self.widgets['cb_shadow'].setChecked(self.labeling_status[self.img_idx].widgets_status['cb_shadow'])
        self.widgets['cb_old'].setChecked(self.labeling_status[self.img_idx].widgets_status['cb_old'])
        self.widgets['cb_outrange'].setChecked(self.labeling_status[self.img_idx].widgets_status['cb_outrange'])
        self.widgets['rb_1col'].setChecked(self.labeling_status[self.img_idx].widgets_status['rb_1col'])
        self.widgets['slider_ratio'].setValue(self.labeling_status[self.img_idx].widgets_status['slider_ratio'])

    def closeEvent(self, event):
        save_path = './labeling_done/'

        for idx in self.done_img_idx:
            img_file = self.img_files[idx]
            os.rename(img_file, save_path + os.path.split(img_file)[-1])


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('data_path', help='Path of folder containing images',
                        default='', type=str)
    return parser.parse_args()


def launch_annotator(data_path):
    """ the actual 'main' function. Other modules that import this module shall
    call this as the entry point. """

    app = QApplication(sys.argv)
    app.setStyle(QStyleFactory.create('Fusion'))
    app.setFont(QFont("Calibri", 10))
    ex = LabelingTool(data_path)
    ex.launch()
    sys.exit(app.exec_())


def main(args):
    launch_annotator(args.data_path)


if __name__ == "__main__":
    args = parse_args()
    main(args)

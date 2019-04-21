# crosswalk labeling tool
# use preprocessed_data images
# input both side of crosswalk --> location / direction(angle)

import argparse
import glob
import cv2
import math
import csv
import crosswalk_data as cd
import compute_label_lib as cl
from PyQt5.QtWidgets import QSlider, QDialog, QApplication, QWidget, QDesktopWidget, QHBoxLayout, QVBoxLayout, QPushButton, QGroupBox, QGridLayout, QLabel, QCheckBox, QRadioButton, QStyle, QStyleFactory
from PyQt5.QtGui import QImage, QPaintEvent, QKeyEvent, QMouseEvent, QPainter, QPixmap, QFont, QPainter, QCursor
from PyQt5.QtCore import Qt
import sys

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('data_path', help = 'Path of folder containing images', default = '', type = str)
    return parser.parse_args()

#===================#
#       CLASS       # 
#===================#

class LabelingTool(QWidget):

    def __init__(self, img_dir):
        super().__init__()
        self.img_dir = img_dir
        self.img_files = glob.glob(self.img_dir + '/*')
        self.img_idx = 0
        self.is_input_finished = False
        self.current_point = [0, (0,0)]
        self.all_points = [(0, 0)]*4
        self.is_line_drawn = [False, False]
        self.img_to_display = None
        self.label_img = QLabel()
        self.data = None
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
        but = QPushButton('하기싫다')

        # Image show
        pixmap = QPixmap('qimage.png')
        pixmap = pixmap.scaled(400, 450, Qt.KeepAspectRatio)
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

        self.gbox_image = QGroupBox("Image")
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
        vbox_meta.addWidget(but_done)
        gbox_meta.setLayout(vbox_meta)
    
        grid.addWidget(self.gbox_image, 0, 0)
        grid.addWidget(gbox_meta, 0, 1)

        self.setWindowTitle('Crosswalk labeling tool')
        self.resize(700, 500)
        self.center()
        self.show()

        #print('gbox_image_pos:', gbox_image.pos())
        #print('gbox_image_size:', gbox_image.size())
        #print('image_size:', pixmap.size())
        #print(self.gbox_image.size().width())

    def launch(self):
        img_files = glob.glob(self.img_dir + '/*')
        img_file = img_files[self.img_idx]

        self.data = cd.CrosswalkData(img_file)
        self.img_to_display = self.data.img.copy()
        img = self.img_to_display

        self.update_img(img)
        
        
    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            img_pos = self.abs2img_pos(event.pos(), self.gbox_image, self.imgsize)
            print(img_pos)

            if self.is_line_drawn[1]:
                self.is_input_finished = True
                return

            cv2.circle(self.img_to_display, img_pos, 2, (255, 0, 0), -1)
            self.update_img(self.img_to_display)

            self.all_points[self.current_point[0]] = img_pos
            self.current_point[0] = self.current_point[0] + 1
            self.current_point[1] = img_pos

            self.__draw_line_and_compute_label()
            self.update_img(self.img_to_display)

    def __draw_line_and_compute_label(self):
        if self.current_point[0] == 2 and not self.is_line_drawn[0]:
            cv2.line(self.img_to_display, self.all_points[0],
                    self.all_points[1], (0, 0, 255), 2)
            self.is_line_drawn[0] = True

        if self.current_point[0] == 4 and not self.is_line_drawn[1]:
            cv2.line(self.img_to_display, self.all_points[2],
                    self.all_points[3], (0, 0, 255), 2)
            self.is_line_drawn[1] = True

            loc, ang = self.__compute_label()
            self.data.input_labels(loc, ang)
            self.__write_labels_on_screen(str(loc), str(ang))

    def __get_manual_meta(self):
        self.data.meta['obs_car'][2] = int(self.widgets['cb_obscar'].isChecked())
        self.data.meta['obs_human'][2] = int(self.widgets['cb_obshuman'].isChecked())
        self.data.meta['shadow'][2] = int(self.widgets['cb_shadow'].isChecked())
        self.data.meta['out_of_range'][2] = int(self.widgets['cb_outrange'].isChecked())
        self.data.meta['old'][2] = int(self.widgets['cb_old'].isChecked())

        if self.widgets['rb_2col'].isChecked() :
            self.data.meta['column'][2] = 2
        
        self.data.meta['zebra_ratio'][2] = int(self.widgets['slider_ratio'].value() * 2)
        self.data.display_manual_meta()
        #print(self.widgets['slider_ratio'].value())

        pass

    def __compute_label(self):
        h, w = self.img_to_display.shape[:2]
        p1 = self.all_points[0]
        p2 = self.all_points[1]
        p3 = self.all_points[2]
        p4 = self.all_points[3]

        left_line = cl.line(p1, p2)
        right_line = cl.line(p3, p4)
        mid_pt, bottom_width = cl.bottom_mid_point_and_width(h, left_line, right_line)

        loc = cl.compute_loc(mid_pt, w, bottom_width)
        ang = cl.compute_ang(left_line, right_line, mid_pt, h)

        return round(loc, 3), round(ang, 3)
            
    def __write_labels_on_screen(self, loc, ang):
        cv2.putText(self.img_to_display, loc + '  ' + ang, (15,15),
                cv2.FONT_HERSHEY_SIMPLEX, 0.35, (255,255,255), 3)
        cv2.putText(self.img_to_display, loc + '  ' + ang, (15,15),
                cv2.FONT_HERSHEY_SIMPLEX, 0.35, (255,0,0), 1)

    def abs2img_pos(self, absPos, gbox, imgsize):
        gw, gh = gbox.size().width(), gbox.size().height()
        iw, ih = imgsize.width(), imgsize.height()
        hb = int((gh - 25 - ih) / 2)
        wb = int((gw - iw) / 2)

        ix = absPos.x() - gbox.pos().x() - wb
        iy = absPos.y() - gbox.pos().y() - 25 - hb
        return int(ix * 0.375), int(iy * 0.375)

    def update_img(self, img):
        qimage = qimage =QImage(img, img.shape[1],img.shape[0], img.shape[1] * 3, QImage.Format_RGB888)
        pixmap = QPixmap(qimage)
        pixmap = pixmap.scaled(400, 450, Qt.KeepAspectRatio)
        self.label_img.setPixmap(pixmap)
        pass
    
    def __initialize_screen(self):
        self.current_point[0] = 0 
        for i in range(4):
            self.all_points[i] = (0, 0)
        self.is_line_drawn[0] = False
        self.is_line_drawn[1] = False
        self.is_input_finished = False



class Annotator(object):
    """ An Annotator displays input window for each image and lets user draw
    points (label) for each image data. """

    def __init__(self, img_dir):
        self.img_dir = img_dir
        self.is_input_finished = False
        self.current_point = [0, (0,0)]
        self.all_points = [(0, 0)]*4
        self.is_line_drawn = [False, False]
        self.img_to_display = None

    def launch(self):
        for img_file in glob.glob(self.img_dir + '/*'):
            data = cd.CrosswalkData(img_file)
            self.__initialize_screen()
            self.img_to_display = data.img.copy()
            self.__launch_window()
            data.make_trackbar('trackbar')


            while not self.is_input_finished:
                cv2.imshow('image', self.img_to_display)
                self.__draw_line_and_compute_label(data)


                '''
                if cv2.waitKey(1) == 32:
                    break # press 'spacebar' -> turn to next image
                '''
                
                if cv2.waitKey(1) == 120: # press 'x'
                    data.set_invalid()
                    data.write_on_db()
                    break
            
            if self.is_input_finished:
                data.input_manual_meta('trackbar')
                data.write_on_db()
                
    @staticmethod
    def mouse_callback(event, x, y, flags, annotator):
        annotator.draw_and_record_point(event, x, y, flags)
                                                
    def draw_and_record_point(self, event, x, y, flags):
        if event == cv2.EVENT_LBUTTONDOWN:
            if self.is_line_drawn[1]:
                self.is_input_finished = True
                return

            cv2.circle(self.img_to_display, (x,y), 2, (0, 0, 255), -1)

            self.all_points[self.current_point[0]] = (x, y)
            self.current_point[0] = self.current_point[0] + 1
            self.current_point[1] = (x, y)

    def __draw_line_and_compute_label(self, data):
        if self.current_point[0] == 2 and not self.is_line_drawn[0]:
            cv2.line(self.img_to_display, self.all_points[0],
                    self.all_points[1], (0, 0, 255), 2)
            self.is_line_drawn[0] = True

        if self.current_point[0] == 4 and not self.is_line_drawn[1]:
            cv2.line(self.img_to_display, self.all_points[2],
                    self.all_points[3], (0, 0, 255), 2)
            self.is_line_drawn[1] = True

            loc, ang = self.__compute_label(data)
            data.input_labels(loc, ang)
            self.__write_labels_on_screen(str(loc), str(ang))

    def __initialize_screen(self):
        self.current_point[0] = 0 
        for i in range(4):
            self.all_points[i] = (0, 0)
        self.is_line_drawn[0] = False
        self.is_line_drawn[1] = False
        self.is_input_finished = False

    def __launch_window(self):
    
        cv2.namedWindow('image', cv2.WINDOW_NORMAL)
        cv2.namedWindow('trackbar', cv2.WINDOW_NORMAL)
        
        cv2.resizeWindow('trackbar', 300,260)
        cv2.resizeWindow('image', 300,240)

        cv2.moveWindow('image', 100, 100)
        cv2.moveWindow('trackbar', 420, 100)

        cv2.setMouseCallback('image', Annotator.mouse_callback, self)
        pass

    def __compute_label(self, data):
        h, w = data.img.shape[:2]
        p1 = self.all_points[0]
        p2 = self.all_points[1]
        p3 = self.all_points[2]
        p4 = self.all_points[3]

        left_line = cl.line(p1, p2)
        right_line = cl.line(p3, p4)
        mid_pt, bottom_width = cl.bottom_mid_point_and_width(h, left_line, right_line)

        loc = cl.compute_loc(mid_pt, w, bottom_width)
        ang = cl.compute_ang(left_line, right_line, mid_pt, h)

        return round(loc, 3), round(ang, 3)

    def __write_labels_on_screen(self, loc, ang):
        cv2.putText(self.img_to_display, loc + '  ' + ang, (15,15),
                cv2.FONT_HERSHEY_SIMPLEX, 0.35, (255,255,255), 3)
        cv2.putText(self.img_to_display, loc + '  ' + ang, (15,15),
                cv2.FONT_HERSHEY_SIMPLEX, 0.35, (255,0,0), 1)


#==================#
#       MAIN       # 
#==================#

def launch_annotator(data_path):
    """ the actual 'main' function. Other modules that import this module shall
    call this as the entry point. """
    folder = args.data_path.split('\\')[-1]

    app = QApplication(sys.argv)
    app.setStyle(QStyleFactory.create('Fusion'))
    app.setFont(QFont("Calibri", 10))
    ex = LabelingTool(data_path)
    ex.launch()
    sys.exit(app.exec_())   

    annotator = Annotator(data_path)
    annotator.launch()
    cv2.destroyAllWindows()

def main(args):
    launch_annotator(args.data_path)
        
if __name__ == "__main__":
    args = parse_args()
    main(args)

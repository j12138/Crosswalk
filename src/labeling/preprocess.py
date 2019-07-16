from PyQt5.QtWidgets import QDesktopWidget, QListView, QTreeView, QFileSystemModel, QAbstractItemView, QFileDialog, QWidget, QApplication, QLabel, QPushButton, QProgressBar
from PyQt5 import QtWidgets
from PyQt5.QtGui import QIcon, QColor
from PyQt5.QtCore import QCoreApplication, QBasicTimer, pyqtSignal
from PIL import Image
from PIL.ExifTags import TAGS
from tqdm import tqdm
from joblib import Parallel, delayed
import shutil
import datetime
import math
import cv2
import os
import sys
import hashlib
import json
import yaml

preprocessed_folder = 'dataset'
labeled_folder = 'labeled'
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.join(BASE_DIR, "..", "..")
config_file = os.path.join(BASE_DIR, 'config.yaml')
total_pixels = 250000 #total pixels of a resized image
NUM_FILES = 0 # Number of pictures that are being preprocessed
SUPPORTED_TYPES = [".bmp", ".pbm", ".pgm", ".ppm", ".sr", ".ras", ".jpeg", ".jpg", ".jpe", ".jp2", ".tiff", ".tif", ".png"]
#userid = "kris"

def load_yaml():
    with open(config_file, 'r') as stream:
        options = yaml.load(stream)
    return options


def get_hash_name(name):
    """ Hash the given filename to create a unique key
    :param name: file name
    :return: hashed value
    """
    return str(hashlib.md5(name.encode()).hexdigest())


def resize_and_save(input_dir, output_dir, img_path):
    """ A worker function for `preprocess_images`, which implements a
    Joblib-based parallelism. Re-sizes and saves each image.
    :param input_dir: original image directory
    :param output_dir: output base directory
    :param img_path: Path to an image to process
    :return: None
    """

    # Check if the extension is supported by cv2. If not, return.
    ext = os.path.splitext(img_path)[-1].lower()
    if ext not in SUPPORTED_TYPES:
        return

    # Bypass DS_Store for MacOS
    if ".DS_Store" in img_path:
        return

    img = cv2.imread(os.path.join(input_dir, img_path))
    # compress the image size by .15 for saving the storage by 1/4
    # EDITED: compress image so that the width*height is no greater than 250000.
    # the resizing process skips if the image size does not exceed the limit.
    # the number 250000 was implemented by trial and error: can be changed if needed
    height, width = img.shape[:2]
    if (height*width) < total_pixels:
        ratio = 1
    else:
        ratio = math.sqrt(total_pixels/(height*width))
    img = cv2.imread(os.path.join(input_dir, img_path))

    resized = cv2.resize(img, None, fx=ratio, fy=ratio,
                         interpolation=cv2.INTER_AREA)
    # cv2.imwrite determines the format by the extension in the path
    save_path = os.path.join(output_dir, get_hash_name(img_path) + ".png")
    cv2.imwrite(save_path, resized)
    # remove the extension
    os.rename(save_path, save_path[:-4])
    # os.remove(os.path.join(input_dir, img_path))


def preprocess_images(input_dir: str, save_dir: str):
    """ Preprocess all the images
    :param input_dir: original image file directory
    :param save_dir: output directory to which the re-sized images are saved
    """

    #files = os.listdir(input_dir)

    #TODO implement exception for unsupported types
    '''
    print(str(len(files))+" and ")
    print(files)

    #for i in range(0, len(files)-1):
    #    print(files[i])
    #    ext = os.path.splitext(files[i])[-1].lower()
        #if (ext == "") or (ext not in SUPPORTED_TYPES) or (os.path.isdir(os.path.join(input_dir, files[i]))):
        #    files.remove(files[i])

    '''
    '''
    for each in files:
        print(each+"'s ext: "+os.path.splitext(each)[-1].lower())
        if (os.path.splitext(each)[-1].lower() not in SUPPORTED_TYPES) or (os.path.isdir(os.path.join(input_dir, each))):
            files.remove(each)
    '''

    # print("Resizing {} images".format(len(files)))
    # output_dir = os.path.join(save_dir, 'preprocessed')
    #
    # if not os.path.exists(output_dir):
    #     os.mkdir(output_dir)
    #
    # return files

    Parallel(n_jobs=-1)(
        delayed(resize_and_save)(input_dir, output_dir, img)
        for img in tqdm(files))
    with Parallel(n_jobs=-1) as parallel:
        with tqdm(files) as t:
            for image in t:
                result += 1
                print(result)
                return result

def extract_metadata(input_dir: str, exifmeta_to_extract: list, widgets):
    """ For each image in the given directory, extract image metadata of
    interest.
    :param input_dir: A directory where image are stored
    :param exifmeta_to_extract: A list of exif metadata to extract
    :return: A dictionary (indexed by hashed key) of dictionary (metadata
             name: value)
    """
    metadata_all = {}

    for img_name in os.listdir(input_dir):

        # Check the extension of the file and if it's not image file, skip the process
        ext = os.path.splitext(img_name)[-1].lower()
        if ext not in SUPPORTED_TYPES:
            continue

        # Exception for MacOS
        if img_name == ".DS_Store":
            continue

        metadata_per_each = {}
        img = Image.open(os.path.join(input_dir, img_name))
        height, width = img.size
        assert width != height, "The image (unexpectedly) square!"
        metadata_per_each["is_horizontal"] = True if width > height else False

        for tag, value in img._getexif().items():
            # e.g. 'ImageWidth'
            exif_meta_name = TAGS.get(tag, tag)
            if exif_meta_name in exifmeta_to_extract:
                metadata_per_each[exif_meta_name] = str(value)

        # Hash the image name
        hashed = get_hash_name(img_name)
        # TODO: Please take a look, Dain. is it necessary to keep the original
        #   name ? --TJ
        # img_name = img_name + '.png'
        # meta['originalname'] = str(img_name)
        metadata_per_each['filehash'] = hashed

        init_labeling_status(metadata_per_each, widgets)

        metadata_all[hashed] = metadata_per_each

    return metadata_all


def init_labeling_status(metadata_per_each, widgets):
    """ initialize labeling status items for DB
    :param metadata_per_each: dictionary item for each data
    :param widgets: set of metadata widgets from labeling tool
    :return:
    """

    metadata_per_each['is_input_finished'] = False
    metadata_per_each['current_point'] = [0, [0, 0]]
    metadata_per_each['all_points'] = [(0, 0)] * 6
    metadata_per_each['is_line_drawn'] = [False, False, False]
    for name in widgets:
        metadata_per_each[name] = widgets[name]


def update_database(metadata, save_dir):
    # create an empty README.md file
    readme_file = os.path.join(save_dir, 'README.txt')
    with open(readme_file, 'w') as f:
        f.write("#_data: " + str(len(metadata)))

    # create an empty JSON file
    db_file = os.path.join(save_dir, 'db.json')
    with open(db_file, 'w') as f:
        f.write("{}")

    try:
        with open(db_file, 'r') as f:
            loaded = json.load(f)
    except Exception as e:
        print('Failed to open database file {}: {}'.format(db_file, e))
    else:
        load = {**loaded, **metadata}
        with open(db_file, "w") as f:
            json.dump(load, f)
        print('Successfully updated!')

def get_save_dir_path(original, prefix, userid):
    """ return name of save directory follows convention.
    [current date] _ [user id] _ [original name] _ [index]
    :param original: original data directory name
    :param prefix: path to save preprocessed data
    :return: save path follows the convention
    """

    now = datetime.datetime.now()
    nowDatetime = now.strftime('%Y-%m-%d')

    #userid = input('Your ID: ')
    save_dir_name = nowDatetime + '_' + userid + '_' + original
    save_path = os.path.join(prefix, save_dir_name)

    #Already implemented in another part for checking redundency
    '''
    idx = 0
    save_path
    while os.path.exists(save_path):
        idx = idx + 1
        if idx == 1:
            save_path = save_path + '_1'
            continue
        save_path = save_path[:-2] + '_' + str(idx)
    '''

    return save_path

def process_dir(args, options, userid):
    # This function deals with directory related process such as
    # processing names and creating directories

    ow_flag = 0 # flag for overwriting dataset already in existence

    folder_name = os.path.basename(args.strip('/\\'))
    save_dir_prefix = os.path.join(BASE_DIR, preprocessed_folder)
    save_dir = get_save_dir_path(folder_name, save_dir_prefix, userid)

    print(save_dir_prefix)

    # create dataset directory if not in existence
    if not os.path.exists(save_dir_prefix):
        os.mkdir(save_dir_prefix)

    # check whether save_dir already exists
    if os.path.exists(save_dir):
        print('Already preprocessed data. Want to overlap?')
        print('Y: overlap, initialize current DB')
        print('N: quit preprocsessing')

        # Temporarily, ow_flag will always be 1. Exceptions to be implemented
        ow_flag = 1
        if (ow_flag == 1):
            # remove existing dir
            shutil.rmtree(save_dir)
            os.mkdir(save_dir)
    else:
        os.mkdir(save_dir)
        print(save_dir+" folder has been successfully created.")


    files = os.listdir(args)

    print("Resizing {} images".format(len(files)))
    output_dir = os.path.join(save_dir, 'preprocessed')
    labeled_dir = os.path.join(save_dir, labeled_folder)
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)
    if not os.path.exists(labeled_dir):
        os.mkdir(os.path.join(labeled_dir))

    return save_dir_prefix, save_dir, files, output_dir


def preprocess_img(args, options, save_dir):
    """ the actual 'main' function. Other modules that import this module shall
    call this as the entry point. """

    # e.g. exifmeta: {'ImageWidth', 'ImageLength', 'Make', 'Model', 'GPSInfo',
    #                 'DateTimeOriginal', 'BrightnessValue'}
    #
    # folder_name = os.path.basename(args.strip('/\\'))
    # save_dir_prefix = os.path.join(BASE_DIR, preprocessed_folder)
    # save_dir = get_save_dir_path(folder_name, save_dir_prefix, userid)
    # print('save_dir: ', save_dir)
    #
    # # create dataset directory if not in existence
    # if not os.path.exists(save_dir_prefix):
    #     os.mkdir(save_dir_prefix)

    # 20190712: For the beta version, dataset will always be overwritten in case of overlap
    # check whether save_dir already exists
    '''
    if os.path.exists(save_dir):
        print('Already preprocessed data. Want to overlap?')
        print('Y: overlap, initialize current DB')
        print('N: quit preprocsessing')
        #ans = input('Select: ')

        # overlap flag set temporarily
        ans = 'Y'

        if ans == 'Y':
            # remove existing dir
            shutil.rmtree(save_dir)
        elif ans == 'N':
            return
        else:
            print('Wrong input!')
            return
    '''

    metadata = extract_metadata(args, list(options['exifmeta']),
                                options['widgets'])

    preprocess_images(args, save_dir)
    update_database(metadata, save_dir)

    os.mkdir(os.path.join(save_dir, labeled_folder))

def preprocess_main(args, userid):
    options = load_yaml()
    preprocess_img(args, options, userid)

def choose_dir(QWidget):
    file = str(QFileDialog.getExistingDirectory(QWidget, "Select Directory"))
    return file

class App(QWidget):
    def __init__(self):
        super().__init__()

# Class that allows to choose multiple directories
# Currently not used 
class FileDialog(QtWidgets.QFileDialog):
    def __init__(self, *args):
        QtWidgets.QFileDialog.__init__(self, *args)
        self.setOption(self.DontUseNativeDialog, True)
        self.setFileMode(self.DirectoryOnly)

        for view in self.findChildren((QtWidgets.QListView, QtWidgets.QTreeView)):
            if isinstance(view.model(), QtWidgets.QFileSystemModel):
                view.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)

class ProgressBar(QWidget):

    switch_window = pyqtSignal()

    def __init__(self, chosen_dir, userid):
        super().__init__()

        # print("test :" + chosen_dir, userid)

        # self.chosen_dir = str(QFileDialog.getExistingDirectory(self, "Select Directory"))
        # self.chosen_dir = "/Users/krislee/Documents/batoners/test_pics"
        self.options = load_yaml()
        self.metadata = extract_metadata(chosen_dir, list(self.options['exifmeta']),
                                    self.options['widgets'])

        self.save_dir_prefix, self.save_dir, self.files, self.output_dir = process_dir(chosen_dir, self.options, userid)

        # self.label_title = QLabel()
        # self.label_title.setText("Processing Images...")
        # self.label_title.setGeometry(190,50,100,50)

        self.num_files = len(self.files)
        self.progressBar = QProgressBar(self)
        self.setGeometry(100,100,480,320)
        self.progressBar.setGeometry(80,100,320,60)
        self.progressBar.setMaximum(100)
        self.btnStart = QPushButton("Start",self)
        self.btnStart.setGeometry(190,160,100,50)

        # self.setGeometry(self.left, self.top, self.width, self.height)

        # self.btnStart.move(240,160)
        self.btnStart.clicked.connect(self.startProgress)
        self.timer = QBasicTimer()
        self.step = 0
        self.result = 0
        self.show()
        self.put_window_on_center_of_screen()

        print('test point 1')
        self.btnStart.click()


    def startProgress(self):
        print('test point 3')
        update_database(self.metadata, self.save_dir)

        while self.step < 100:
            with Parallel(n_jobs=-1) as parallel:
                with tqdm(self.files) as t:
                    for image in t:
                        resize_and_save(chosen_dir, self.output_dir, image)
                        self.result += 1
                        # print(self.result)
                        self.step += ((self.result+1)*math.ceil(100/self.num_files))
                        self.progressBar.setValue(self.step)
        if self.step >= 100:
            self.progressBar.setValue(100)
            self.timer.stop()
            self.btnStart.setText("Finished")
            self.btnStart.clicked.connect(self.switch)

            # self.switch_window.emit()
            return

        # if self.timer.isActive():
        #     self.timer.stop()
        #     self.btnStart.setText("Start")
        # else:
        #     print('test point 2')
        #     # process_dir(self.chosen_dir, self.options, userid)
        #     # print("test point")
        #     # print(os.listdir(self.save_dir))
        #     #preprocess_images(self.chosen_dir, self.save_dir)
        #     update_database(self.metadata, self.save_dir)
        #     self.timer.start(100, self)
        #     self.btnStart.setText("Stop")

    # def timerEvent(self, event):
    #     print('test point 3')
    #     if self.step >= 100:
    #         self.progressBar.setValue(100)
    #         self.timer.stop()
    #         self.btnStart.setText("Finished")
    #         self.btnStart.clicked.connect(self.switch)
    #
    #         # self.switch_window.emit()
    #         return
    #     with Parallel(n_jobs=-1) as parallel:
    #         with tqdm(self.files) as t:
    #             for image in t:
    #                 self.result += 1
    #                 # print(self.result)
    #                 self.step += ((self.result+1)*math.ceil(100/self.num_files))
    #                 self.progressBar.setValue(self.step)

    def switch(self):
        self.switch_window.emit()

    def put_window_on_center_of_screen(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

class Complete_Screen(QWidget):

    switch_window = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.title = "Image Preprocess"
        self.left = 100
        self.top = 100
        self.width = 480
        self.height = 320
        print("test point reached")
        self.initUI()
        self.put_window_on_center_of_screen()

    def put_window_on_center_of_screen(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

class Controller():
    """
    Controller class for switching windows
    """
    def __init__(self, chosen_dir, userid):
        self.chosen_dir = chosen_dir
        self.userid = userid

    def show_progrees(self):
        self.selector = ProgressBar(self.chosen_dir, self.userid)
        self.selector.switch_window.connect(self.show_complete)
        self.selector.show()

    def show_complete(self):
        #self.tool = LabelingTool(os.path.join(dir_path, 'preprocessed'))
        self.tool = Complete_Screen()
        self.selector.close()
        #global startTime
        #startTime = time.time()
        self.tool.show()


def preprocess_main(chosen_dir, userid):

    # options = load_yaml()
    # pr = Preprocess()
    # app = QApplication(sys.argv)
    # test = App()
    # chosen_dir = choose_dir(test)

    controller = Controller(chosen_dir, userid)
    controller.show_progrees()
    #ex = ProgressBar(len(metadata))
    #ex.show()
    # sys.exit(app.exec())

if __name__ == '__main__':
    options = load_yaml()
    # pr = Preprocess()
    app = QApplication(sys.argv)
    test = App()
    chosen_dir = choose_dir(test)

    controller = Controller(chosen_dir, "krise")
    controller.show_progrees()
    #ex = ProgressBar(len(metadata))
    #ex.show()
    sys.exit(app.exec())

    # multiple directory selector
'''
    ex = FileDialog()
    ex.show()
    ex.exec_()
    print(ex.selectedFiles())

'''

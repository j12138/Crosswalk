from PyQt5.QtWidgets import QListView, QTreeView, QFileSystemModel, QAbstractItemView, QFileDialog, QWidget, QApplication, QLabel, QPushButton, QProgressBar
from PyQt5 import QtWidgets
from PyQt5.QtGui import QIcon, QColor
from PyQt5.QtCore import QCoreApplication, QBasicTimer
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
NUM_FILES = 1 # Number of pictures that are being preprocessed
SUPPORTED_TYPES = [".bmp", ".pbm", ".pgm", ".ppm", ".sr", ".ras", ".jpeg", ".jpg", ".jpe", ".jp2", ".tiff", ".tif", ".png"]

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
    files = os.listdir(input_dir)
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

    print("Resizing {} images".format(len(files)))
    NUM_FILES = len(files)
    #print(files)
    os.mkdir(save_dir)
    output_dir = os.path.join(save_dir, 'preprocessed')
    os.mkdir(output_dir)

    Parallel(n_jobs=-1)(
        delayed(resize_and_save)(input_dir, output_dir, img)
        for img in tqdm(files))


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


def preprocess_img(args, options, userid):
    """ the actual 'main' function. Other modules that import this module shall
    call this as the entry point. """

    # e.g. exifmeta: {'ImageWidth', 'ImageLength', 'Make', 'Model', 'GPSInfo',
    #                 'DateTimeOriginal', 'BrightnessValue'}

    folder_name = os.path.basename(args.strip('/\\'))
    save_dir_prefix = os.path.join(BASE_DIR, preprocessed_folder)
    save_dir = get_save_dir_path(folder_name, save_dir_prefix, userid)
    print('save_dir: ', save_dir)
    # create dataset directory if not in existence
    if not os.path.exists(save_dir_prefix):
        os.mkdir(save_dir_prefix)

    # check whether save_dir already exists
    if os.path.exists(save_dir):
        print('Already preprocessed data. Want to overlap?')
        print('Y: overlap, initialize current DB')
        print('N: quit preprocsessing')
        ans = input('Select: ')

        if ans == 'Y':
            # remove existing dir
            shutil.rmtree(save_dir)
        elif ans == 'N':
            return
        else:
            print('Wrong input!')
            return
    metadata = extract_metadata(args, list(options['exifmeta']),
                                options['widgets'])
    #preprocess_images(args, save_dir)
    #update_database(metadata, save_dir)

    #os.mkdir(os.path.join(save_dir, labeled_folder))

    return metadata, save_dir

def preprocess_main(args, userid):
    options = load_yaml()
    preprocess_img(args, options, userid)

def choose_dir(QWidget):
    file = str(QFileDialog.getExistingDirectory(QWidget, "Select Directory"))
    return file

class App(QWidget):

    '''
    This class generates the GUI for preprocess.py
    '''

    def __init__(self):
        super().__init__()
        self.title = "Preprocess.py Test PyQt"
        self.left = 100
        self.top = 100
        self.width = 640
        self.height = 480
        self.initUI()

    def initUI(self):

        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        '''
        self.model = QFileSystemModel()
        self.model.setRootPath(cwd)
        #self.model.setRootIndex(model.index(cwd))
        #self.model.setRootPath(self, self.model.rootDirectory())
        self.tree = QTreeView()
        self.tree.setModel(self.model)
        #self.tree.setRootIndex(self.model.index(cwd))
        self.tree.setAnimated(False)
        self.tree.setIndentation(20)
        self.tree.setSortingEnabled(True)

        self.tree.setWindowTitle(self.title)
        self.tree.resize(self.width, self.height)

        windowLayout = QVBoxLayout()
        windowLayout.addWidget(self.tree)
        self.setLayout(windowLayout)
        '''

        #file = choose_dir(self)
        #file = str(QFileDialog.getExistingDirectory(self, "Select Directory"))
        #self.label = QLabel("Your current directory is "+file)
        #self.label.show()
        #print(file)
        #userid = ""
        #preprocess_main(file, userid)

        #tutorial = ProgressBar_tutorial(num_files)
        #tutorial.show()


# Class that allows to choose multiple directories
class FileDialog(QtWidgets.QFileDialog):
    def __init__(self, *args):
        QtWidgets.QFileDialog.__init__(self, *args)
        self.setOption(self.DontUseNativeDialog, True)
        self.setFileMode(self.DirectoryOnly)

        for view in self.findChildren((QtWidgets.QListView, QtWidgets.QTreeView)):
            if isinstance(view.model(), QtWidgets.QFileSystemModel):
                view.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)

class ProgressBar(QWidget):
    def __init__(self, num_files):
        super().__init__()
        self.progressBar = QProgressBar(self)
        self.progressBar.setGeometry(30,40,200,25)
        self.num_files = num_files
        self.btnStart = QPushButton("Start",self)
        self.btnStart.move(40,80)
        self.btnStart.clicked.connect(self.startProgress)

        self.timer = QBasicTimer()
        self.step = 0

    def startProgress(self):
        if self.timer.isActive():
            self.timer.stop()
            self.btnStart.setText("Start")
        else:
            self.timer.start(100, self)
            self.btnStart.setText("Stop")

    def timerEvent(self, event):
        if self.step >= 100:
            self.progressBar.setValue(100)
            self.timer.stop()
            self.btnStart.setText("Finished")
            return
        self.step += (1*self.num_files)
        self.progressBar.setValue(self.step)

class Complete_Screen(QWidget):
    def __init__(self):
        super().__init__()
        self.test = 0
        print("test point reached")
        return


if __name__ == '__main__':
    options = load_yaml()

    app = QApplication(sys.argv)
    test = App()
    chosen_dir = choose_dir(test)
    options = load_yaml()

    metadata, save_dir = preprocess_img(chosen_dir, options, "kris")
    ex = ProgressBar(len(metadata))
    ex.show()
    sys.exit(app.exec())

    '''
    # multiple directory selector

    ex = FileDialog()
    ex.show()
    ex.exec_()
    print(ex.selectedFiles())
    '''


import Augmentor as aug
import os, glob
from PIL import Image
import numpy as np


test_dataset = './test_dataset/data_array/'
test_img = Image.open(test_dataset + '5a9dcdb4f1a81435985bf73deb0160f9.jpg')
test_img = np.asarray(test_img, dtype=np.uint8)
# print(test_img)


def make_imgs_array(img_dir):
    test_imgs = []

    images = glob.glob(os.path.join(img_dir, '*.jpg'))
    for img in images:
        # print(img)
        im = np.asarray(Image.open(img))
        test_imgs.append(im)

    return test_imgs


def convert_none2jpg(img_dir):
    images = glob.glob(os.path.join(img_dir, '*'))

    for img in images:
        im = Image.open(img)
        im.save(img + '.jpg')
        os.remove(img)


# convert_none2jpg(test_dataset)
# img_array = make_imgs_array(test_dataset)
p = aug.Pipeline()

# p.random_distortion(probability=1.0, grid_width=10,
#                     grid_height=10, magnitude=1)

p.rotate(probability=0.7, max_left_rotation=10, max_right_rotation=10)
p.skew_tilt(probability=0.5, magnitude=0.3)
p.shear(probability=0.5, max_shear_left=3, max_shear_right=3)
p.flip_left_right(probability=0.5)
p.zoom(probability=0.3, min_factor=1.1, max_factor=1.5)


test_array = make_imgs_array('./test_dataset/data_array/')

# print(test_img)
print(np.asarray([test_img]))
p.sample_with_array(np.asarray([test_img]))

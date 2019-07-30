import Augmentor as aug
import os, glob
from PIL import Image


test_dataset = 'test_dataset/data2_1/'


def convert_none2jpg(img_dir):
    images = glob.glob(os.path.join(img_dir, '*'))

    for img in images:
        im = Image.open(img)
        im.save(img + '.jpg')
        os.remove(img)


# convert_none2jpg(test_dataset)
p = aug.Pipeline(test_dataset)

# p.random_distortion(probability=1.0, grid_width=10,
#                     grid_height=10, magnitude=1)

p.rotate(probability=0.7, max_left_rotation=10, max_right_rotation=10)
p.skew_tilt(probability=0.5, magnitude=0.3)
p.shear(probability=0.5, max_shear_left=3, max_shear_right=3)
p.flip_left_right(probability=0.5)
p.zoom(probability=0.3, min_factor=1.1, max_factor=1.5)

p.sample(30)

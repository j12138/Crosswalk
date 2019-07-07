import pytest
from labeling.compute_label_lib import compute_all_labels
from collections import namedtuple
import os


def test_trivial():
    assert True, "You passed a trivial test :)"


def test_compute_ang():
    imgW = [433, 433, 433, 433]
    imgH = [577, 577, 577, 577]
    all_points = [[(204, 327), (3, 384), (375, 337),
                   (385, 487), (24, 291), (416, 270)],
                  [(171, 289), (6, 436), (384, 285),
                   (431, 299), (4, 246), (425, 244)],
                  [(3, 439), (47, 536), (270, 291),
                   (431, 329), (2, 241), (426, 231)],
                  [(97, 338), (1, 366), (345, 385),
                   (173, 570), (6, 227), (420, 223)]]
    is_odd2col = [False, False, False, True]

    ang = []
    ang_expect = [-30, -5, 40, -35]
    case_num = len(imgW)
    pass_check = True

    for i in range(case_num):
        ang = compute_all_labels(imgW[i], imgH[i],
                                 all_points[i], is_odd2col[i])[1]
        pass_check = pass_check and (abs(ang - ang_expect[i]) <= 5)

    assert pass_check

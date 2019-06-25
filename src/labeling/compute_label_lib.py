import math


def line(p1, p2):
    # 점 p1과 p2를 지나는 직선 구하기. [기울기, y절편] 의 리스트로 반환
    slope = (p1[1] - p2[1]) / (p1[0] - p2[0])
    intercept = p1[1] - slope * p1[0]

    return [slope, intercept]


def intersection(l1, l2):
    # 두 직선 l1, l2의 교차점 구하기. 직선은 [기울기, y절편]의 리스트로 입력되어야 함.
    x = (l2[1] - l1[1]) / (l1[0] - l2[0])
    y = l1[0] * x + l1[1]

    return x, y


def mid_point(p1, p2):
    # compute middel point of given two points
    x = (p1[0] + p2[0]) / 2.0
    y = (p1[1] + p2[1]) / 2.0

    return x, y


def compute_pitch(mid, h):
    # compute vertical pitch label from middle point and height of the image
    return mid[1] / float(h)


def compute_roll(slope):
    # compute horizontal roll label from slope
    return -math.atan(slope) * 180 / math.pi


def bottom_mid_point_and_width(H, l1, l2):
    # 횡단보도 밑변의 중점과 밑변 길이 구하기. H는 preprocessed img의 세로길이 (240?)
    b_line = [0, H]
    left_end = intersection(b_line, l1)
    right_end = intersection(b_line, l2)
    mid_pt = (right_end[0] + left_end[0]) / 2.0, H
    bottom_width = right_end[0] - left_end[0]

    return mid_pt, bottom_width


def compute_loc(mid, W, bottom_width):
    # loc label 계산
    loc = W / 2.0 - mid[0]
    scaled_loc = (loc / bottom_width) * 2

    return scaled_loc


def compute_included_ang(l1, l2):
    # 직선 l1과 l2의 사잇각 구하기
    v1 = (1, l1[0])
    v2 = (1, l2[0])

    dot_product = v1[0] * v2[0] + v1[1] * v2[1]
    v1_len = math.sqrt(v1[0] ** 2 + v1[1] ** 2)
    v2_len = math.sqrt(v2[0] ** 2 + v2[1] ** 2)

    cosine = dot_product / (v1_len * v2_len)
    theta = math.acos(cosine)
    ang = math.degrees(theta)

    return ang


def compute_ang(l1, l2, mid, H):
    vanishing_pt = intersection(l1, l2)
    right_direction = line(mid, vanishing_pt)
    horizontal_line = [0, H]

    ang = compute_included_ang(right_direction, horizontal_line)
    ang = 90 - ang

    if right_direction[0] < 0:
        ang = ang * (-1.0)

    return ang


def find_side_point(p1, p2, p3, p4, image_width, image_height):
    """
    To solve 2 column exception
    Using one-side line points and middle line points
    :param p1:ons-side line point 1 (crosswalk end_line point)
    :param p2:one-side line point 2
    :param p3:middle-side line point 1 (crosswalk end_line point)
    :param p4:middle-side line point 2
    :param image_width : image_width
    :param image_height : image_height
    :return: other side line point (crosswalk end_line point)
    """
    end_line = line(p1, p2)
    new_p1y = (image_height - p1[1]) * 24 / 38 * image_height / (p1[1])
    new_p3y = (image_height - p3[1]) * 24 / 38 * image_height / p3[1]
    a = end_line[0]
    b = end_line[1]
    H = image_height
    line1 = [12 * a * math.pow(H, 2) / (-19 * math.pow(a * p3[0] + b, 2)),
             (12 * a * math.pow(H, 2) / (19 * math.pow(a * p3[0] + b, 2))) * p1[0] + new_p1y]
    line2 = [(19 * math.pow(a * p3[0] + b, 2)) / (12 * a * math.pow(H, 2)),
             -p3[0] * (19 * math.pow(a * p3[0] + b, 2)) / (12 * a * math.pow(H, 2)) + new_p3y]
    c, d = intersection(line1, line2)
    return [2 * c - p1[0], a * (2 * c - p1[0]) + b]


def find_otherside_line(p1, p2, p3, p4, image_width, image_height):
    """
    Using find_side_point function, get otherside line.
    :param p1:ons-side line point 1 (crosswalk end_line point)
    :param p2:one-side line point 2
    :param p3:middle-side line point 1 (crosswalk end_line point)
    :param p4:middle-side line point 2
    :param image_width : image_width
    :param image_height : image_height
    :return: other side line
    """
    sideline1 = line(p1, p2)
    midline = line(p3, p4)
    view_point = intersection(sideline1, midline)
    one_point = find_side_point(p1, p2, p3, p4, image_width, image_height)
    sideline2 = line(view_point,one_point)
    return sideline2

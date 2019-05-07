import math

def line(p1,p2):
    # 점 p1과 p2를 지나는 직선 구하기. [기울기, y절펀] 의 리스트로 반환
    slope = (p1[1] - p2[1]) / (p1[0] - p2[0])
    intercept = p1[1] - slope * p1[0]

    return [slope, intercept]

def intersection(l1, l2):
    # 두 직선 l1, l2의 교차점 구하기. 직선은 [기울기, y절편]의 리스트로 입력되어야 함.
    x = (l2[1] - l1[1]) / (l1[0] - l2[0])
    y = l1[0] * x + l1[1]

    return x, y

def mid_pt(p1, p2):
    x = (p1[0] + p2[0]) / 2.0
    y = (p1[1] + p2[1]) / 2.0

    return x, y

def compute_pit(mid, h):
    return mid[1] / float(h)

def compute_roll(slope):
    return -math.atan(slope) * 2 / math.pi 

def bottom_mid_point_and_width(H, l1, l2):
    # 횡단보도 밑변의 중점과 밑변 길이 구하기. H는 preprocessed img의 세로길이 (240?)
    b_line = [0, H]
    left_end = intersection(b_line, l1)
    right_end = intersection(b_line, l2)
    mid_pt = (right_end[0] + left_end[0])/2.0, H
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

    dot_product = v1[0]*v2[0] + v1[1]*v2[1]
    v1_len = math.sqrt(v1[0]**2 + v1[1]**2)
    v2_len = math.sqrt(v2[0]**2 + v2[1]**2)

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


import pytest
from labeling.database import DBMS

test_datadir = 'test_dataset'


def test_trivial():
    assert True, "You passed a trivial test :)"


def test_correct_labeling_order():
    test_data = {"09b91da24637638fe1acbe0c1cb3ca86": {
        "is_horizontal": False,
        "GPSInfo": "{1: 'N', 2: ((36, 1), (20, 1), (5578, 100)), 3: 'E', 4: ((127, 1), (22, 1), (5914, 100)), 5: b'\\x00', 6: (511727, 8026), 7: ((1, 1), (57, 1), (55, 1)), 12: 'K', 13: (10559, 81828), 16: 'T', 17: (462784, 1433), 23: 'T', 24: (462784, 1433), 29: '2019:08:09', 31: (13244, 2207)}",
        "Make": "Apple", "Model": "iPhone 7",
        "DateTimeOriginal": "2019:08:09 10:57:55",
        "BrightnessValue": "(9303, 839)",
        "filehash": "09b91da24637638fe1acbe0c1cb3ca86",
        "is_input_finished": True,
        "current_point": [6, [409, 200]],
        "all_points": [[145, 248], [421, 285], [8, 269], [146, 470], [4, 236], [409, 200]],
        "is_line_drawn": [True, True, True],
        "cb_obscar": False, "cb_obshuman": False, "cb_shadow": True,
        "cb_old": False, "cb_outrange": False, "rb_1col": 2,
        "slider_ratio": 60, "remarks": "",
        "obs_car": 0, "obs_human": 0, "shadow": 1, "column": 2,
        "zebra_ratio": 60, "out_of_range": 0,
        "old": 0, "invalid": 0, "loc": -1.0, "ang": 34.628, "pit": 0.389,
        "roll": 2.045, "cb_corner": False
    }}
    test_db = DBMS(test_datadir)
    DBMS.__correct_points_order(test_data["09b91da24637638fe1acbe0c1cb3ca86"])
    pass
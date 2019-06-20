"""
이 모듈은 여러개의 폴더에 담겨있는 db 와 labeled image 파일을
하나의 db와 labeled image 파일로 합치기 위한 모듈이다.
저자 : 황승현
"""
import shutil
import os
import json

current_path = os.getcwd()
os.mkdir(os.path.join(current_path, "labeled_image"))  # make empty labeled_image directory
labeled_folder_path = os.path.join(current_path, "labeled_image")   # set path to labeled_image directory
with open(os.path.join(current_path, "db.json"), "w"):  # make empty db.json file
    pass


def data_dir_path():
    """find data file
    :return data+path : /data/ path
    """
    data_path = os.path.join(current_path, "data")

    return data_path


def merge_data(data_path, imagepath):
    """
    merge database file and labeled image
    :param data_path: merge/data/ path
    :param imagepath: merge/labeled_image/ path
    :return: jstring : json file for total database
    """
    datalist = os.listdir(data_path)
    with open(os.path.join(data_path, datalist[0], "db.json")) as json_file:
        json_data2 = json.load(json_file)
    for datafile in datalist[1:]:
        with open(os.path.join(data_path, datafile, "db.json")) as json_file:
            json_data1 = json.load(json_file)
        json_data2.update(json_data1)
    for datafile in datalist:
        label_f_path = os.path.join(data_path, datafile, "labeled")
        sublist = os.listdir(label_f_path)
        for subdata in sublist:
            shutil.copy(os.path.join(label_f_path, subdata), imagepath)
    jstring = json.dumps(json_data2)
    return jstring


def main():
    data_path = data_dir_path()
    json1 = merge_data(data_path, labeled_folder_path)   # json1 = merge db file
    with open("db.json", "w") as dbfile:  # write json1 in db.json file
        dbfile.write(json1)
        dbfile.close()


if __name__ == '__main__':
    main()

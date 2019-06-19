import shutil
import os
import json


def locate():
    """find data file
    :return data+path : /data/ path
    """
    current_path = os.getcwd()
    data_path = current_path + "\data"

    return data_path


def merge(data_path, imagepath):
    """
    merge database file and labeled image
    :param data_path: merge/data/ path
    :param imagepath: merge/labeled_image/ path
    :return: jstring : json file for total database
    """
    datalist = os.listdir(data_path)
    with open(data_path + "\\" + datalist[0] + "\\db.json") as json_file:
        json_data2 = json.load(json_file)
    for datafile in datalist[1:]:
        with open(data_path + "\\" + datafile + "\\db.json") as json_file:
            json_data1 = json.load(json_file)
        json_data2.update(json_data1)
    for datafile in datalist:
        subpath = data_path + "\\" + datafile + "\\labeled"
        sublist = os.listdir(subpath)
        for subdata in sublist:
            shutil.copy(subpath + "\\" + subdata, imagepath)
    jstring = json.dumps(json_data2)
    return jstring


def main():
    data_path = locate()
    current_path = os.getcwd()
    with open(os.path.join(current_path, "db.json"), "w"):  # make empty db.json file
        pass
    os.mkdir(current_path + "\\labeled_image\\")  # make empty labeled_image directory
    movepath = current_path + "\\labeled_image"   # set path to labeled_image directory
    json1 = merge(data_path, movepath)   # json1 = merge db file
    f = open("db.json", "w")  # write json1 in db.json file
    f.write(json1)
    f.close()


if __name__ == '__main__':
    main()

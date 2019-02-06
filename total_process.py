import argparse
import os
import preprocess
import labeling_tool
import makenpy
import train

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('data_path', help = 'Path of folder containing images', type = str)
    parser.add_argument('-W', '--width', dest = 'width', default = 300, type = int)
    parser.add_argument('-H', '--height', dest = 'height', default = 240, type = int)
    parser.add_argument('-c', '--color', dest = 'color', default = False, type = bool)
    return parser.parse_args()


def pre_process(data_path):
    print('prepreoceesing..')
    os.system("python preprocess.py " + data_path)

def launch_labeling_tool(data_path):
    print('launch labeling tool..')
    os.system("python labeling_tool.py " + data_path)

def make_npy_sets():
    pass

def execute_training():
    pass


def main():
    args = parse_args()

    pre_process(args.data_path)
    #launch_labeling_tool(args.data_path)
    #make_npy_sets()
    #execute_training()


if __name__ == '__main__':
    main()
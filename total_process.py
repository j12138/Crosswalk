import argparse
import os
import preprocess
import labeling_tool
import makenp
import train
import yaml

def parse_args(options):
    parser = argparse.ArgumentParser()
    parser.add_argument('data_path', help = 'Path of folder containing images', type = str)
    parser.add_argument('-W', '--width', dest = 'width', default = options['preprocess_width'], type = int)
    parser.add_argument('-H', '--height', dest = 'height', default = options['preprocess_height'], type = int)
    parser.add_argument('-c', '--color', dest = 'color', default = False, type = bool)
    parser.add_argument('-d', '--db_file', dest = 'db_file', default = options['db_file'], type = str)

    return parser.parse_args()

def loadyaml():
    with open('./config.yaml', 'r') as stream: 
        options = yaml.load(stream)
    return options

def main():
    options = loadyaml()
    args = parse_args(options)

    preprocess.preprocess_img(args, options)
    labeling_tool.launch_annotator(args.data_path)
    #makenp.make_npy_file(options) 
    # 알바에게 필오없다


if __name__ == '__main__':
    main()
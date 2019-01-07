# -*- coding: utf-8 -*-

import json
import random
from pprint import pprint


if __name__ == '__main__':
    # load the json file
    with open('output.json', 'r') as fin:
        airports = json.load(fin)
    
    # Show runway 4-22 at KMWH
    print('Runway 4-22 at KMWH:')
    pprint(airports['KMWH']['land_runways'][1])     
    

    

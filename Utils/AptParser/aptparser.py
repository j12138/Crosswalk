from sys import argv
import json


LINE_CODES = {'land_airport': '1',
              'land_runway': '100',
              'file_end': '99',
              }

TEMPLATES = { '1': [ # Land airport
                    (1, 'elevation_amsl', int), # format: line_index, key, type 
                    (4, 'icao', str),
                    (5, 'name', str)
                   ],
              '100': [ # Land runway
                    (1, 'width', float), # in meters
                    (2, 'surface_type', int),
                    (3, 'shoulder_surface_type', int),
                    (4, 'runway_smoothness', float),
                    (5, 'center_line_lights', int),
                    (6, 'edge_lighting', int),
                    (7, 'auto_generate_signs', int),
                    (8, 'rw_start_number', str),
                    (9, 'rw_start_lat', float),
                    (10, 'rw_start_lon', float),
                    (11, 'rw_start_displaced_threshold', float), # in meters
                    (12, 'rw_start_overrun_length', float), # in meters
                    (13, 'rw_start_markings', int),
                    (14, 'rw_start_approach_lighting', int),
                    (15, 'rw_start_tdz_lighting', int),
                    (16, 're_start_rei_lighting', int), # runway end identifier
                    (17, 'rw_end_number', str),
                    (18, 'rw_end_lat', float),
                    (19, 'rw_end_lon', float),
                    (20, 'rw_end_displaced_threshold', float), # in meters
                    (21, 'rw_end_overrun_length', float), # in meters
                    (22, 'rw_end_markings', int),
                    (23, 'rw_end_approach_lighting', int),
                    (24, 'rw_end_tdz_lighting', int),
                    (25, 're_end_rei_lighting', int), # runway end identifier
                   ]
            }

def parse_file(infile, limit=None):
    airports = {}
    current_airport = None

    with open(infile, 'r') as fin:
        # skip file headers
        fin.readline()
        fin.readline()
        for line in fin:
            line = line.strip()

            if not line or line.startswith('#'):
                continue

            line = line.split()
            if line[0] == LINE_CODES['land_airport']:
                # new airport encountered
                if current_airport is not None:
                    # save previous airport
                    airports[current_airport['icao']] = current_airport
                    if limit and len(airports) == limit:
                        break
                # parse the airport
                current_airport = dict([(key, typ(line[idx])) for idx, key, typ in TEMPLATES[LINE_CODES['land_airport']]])
                current_airport['land_runways'] = []
            
            if line[0] == LINE_CODES['land_runway']:
                # new land runway encountered, add it to the current airport
                current_airport['land_runways'].append(dict([(key, typ(line[idx])) for idx, key, typ in TEMPLATES[LINE_CODES['land_runway']]]))
            
            if line[0] == LINE_CODES['file_end']:
                # save the last airport
                airports[current_airport['icao']] = current_airport
    return airports


if __name__ == '__main__':
    if len(argv) < 3:
        print 'Usage: aptparse.py path/to/apt.dat path/to/output.json [n_airports]'
    infile = argv[1]
    outfile = argv[2]
    limit = None if len(argv) < 4 else int(argv[3])
    
    airports = parse_file(infile, limit)
    with open(outfile, 'w') as fout:
        json.dump(airports, fout)
    print 'Parsed %d airports' % len(airports)
    

    
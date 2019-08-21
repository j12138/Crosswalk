import os
import json
from PIL import Image
from compute_label_lib import compute_all_labels

data_dir = './dataset/'

for dir in os.listdir(data_dir):
    print(dir)

    db_file = open(os.path.join(data_dir, dir, 'db.json'))
    db = json.load(db_file)
    db_val = db.values()

    for name in db_val:
        hashname = name['filehash']

        img_file = os.path.join(data_dir, dir, 'labeled', hashname)

        if os.path.exists(img_file):
            if name['is_input_finished']:
                im = Image.open(img_file)
                width, height = im.size

                # print(name['loc'], name['ang'])

                odd2col = name['rb_1col'] == 2.5
                try:
                    '''
                    if not odd2col:
                        all_p = name["all_points"]

                        if all_p[0][0] > all_p[2][0]:
                            print('@@@@CATCH!')
                            temp = all_p[0]
                            all_p[0] = all_p[2]
                            all_p[2] = temp
                            temp = all_p[1]
                            all_p[1] = all_p[3]
                            all_p[3] = temp

                            db[hashname]['all_points'] = all_p
                            name['all_points'] = all_p
                    '''

                    
                    loc, ang, pit, roll = compute_all_labels(width, height,
                                                            name['all_points'],
                                                            odd2col)

                    # print(loc, ang)
                    db[hashname]['loc'] = loc
                    db[hashname]['ang'] = ang
                    db[hashname]['pit'] = pit
                    db[hashname]['roll'] = roll

                    


                    with open(os.path.join(data_dir, dir, 'db.json'), "w") as f:
                        json.dump(db, f)

                except Exception as e:
                    print(e)

                
                

                

            

        else:
            print('No')
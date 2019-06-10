# Crosswalk
Crosswalk guide application

TODO: 문서화. 한글로. 

`>> python preprocess.py ./(data_folder)`
-- preprocessing (resize, grayscale, exifmeta)
-- will be saved at `./preprocessed_data/_(data_folder)_`

`>> python labeling_tool.py ./preprocessed_data/_(data_folder)_`
-- labeling manual metadata
-- transfer preprocessed img at `./labeling_done` as hashed name(no extension)
-- store metadata at DB (`Crosswalk_Database.json`)

`>> python makenp.py`
-- make filtered npy file for training (follow instruction)
-- npy will be saved at `./npy`
-- packing log at `makenp_log.txt`

`>> python train.py`
-- machine learning using npy files
-- (TODO) user can choose pre-made npy files (not yet implemented)

`>> python validate.py`

`>> python db_statistics.py`
-- show visual statistics of DB
-- # of valid data, stats of metadata

## 설치

TODO

## 레이블링 방법

## 데이터가 어떻게 저장되는지..?

## 데이터셋 생성 방법

## 시각화

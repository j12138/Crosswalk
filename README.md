# Crosswalk
Crosswalk guide application

횡단보도 보행 가이드 서비스 개발 프로젝트입니다.

스마트폰 카메라로 횡단보도를 촬영하면 보행자의 횡단보도 상의 위치와 향하고 있는 방향 등을 고려하여 직선 방향으로 바르게 보행할 수 있도록 안내(진동 및 음성)하는 기능을 목표로 하고 있습니다.

## 설치
Python 3.6

필요한 패키지 리스트는 `.\requirements.txt`에 나열되어 있습니다.

`pip install -r requirements.txt`입력으로 한 번에 설치할 수 있습니다.

+) 학습에 필요한 tensorflow 및 keras


## 데이터셋 생성 방법
횡단보도 촬영 이미지를 레이블링하기 전에, 전처리 가공 과정을 거칩니다.

`python .\src\labeling\preprocess.py (사진폴더)`를 실행합니다.

가공된 이미지는 `.\preprocessed_data\(폴더명)\`에 저장됩니다.


## 데이터가 저장되는 구조
전처리를 및 레이블링을 완료한 이미지는 다음과 같은 구조로 저장됩니다.

    Crosswalk/
    └─ preprocessed_data/
        ├─ dataset_1/
        │   ├─ labeled/   #레이블링 완료된 이미지
        │   ├─ preprocessed/   #가공된 이미지 (기본 위치)
        │   ├─ db.json   #해당 셋의 데이터베이스
        │   └─ README   #기타 기록용 (현재는 이미지 개수만)
        ├─ dataset_2/
        ├─ dataset_3/
        └─ ...


## 레이블링 방법
머신 러닝을 위한 레이블링 방법 안내입니다. 전처리를 완료한 이미지를 사용합니다.

`python .\src\labeling\labeling_tool.py .\preprocessed_data\(폴더명)\`으로 실행합니다.

또는 `python .\src\labeling\labeling_tool.py` 와 같이 인자 없이 실행하면 폴더를 선택할 수 있습니다.

![Alt text](/image/labeling_guide0.png)

아래 이미지에 적힌 순서대로 사진에 점을 찍습니다. (총 6개)

이미 찍은 점은 `ESC`키를 눌러 지울 수 있습니다. (실행 취소)
![Alt text](/image/labeling_guide1.png)

레이블링 완료한 이미지는 `.\preprocessed_data\(폴더명)\labeled\`에 저장됩니다.

또한 레이블링 상태와 계산된 레이블 값, 메타데이터 등은 `.\preprocessed_data\(폴더명)\db.json`파일에 저장됩니다.


## 시각화
이미지 데이터 정보와 레이블링 통계를 볼 수 있습니다.
`python .\src\stats.py`로 실행합니다.

    [1] Show total DB statistics  #전체 데이터 통계를 봅니다
    [2] Show labeling progress   #레이블링 상태를 봅니다

    Choose mode:

  


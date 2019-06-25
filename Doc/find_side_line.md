#Explanation for algorithm for side line
우리는 2 column 횡단보도의 이미지에서 양 side가 나오지 않은 경우를 자주 볼 수 있습니다. 이 경우에 한 side line과 middle line을 이용하여 남은 한 쪽 side line을 구하는 알고리즘에 대한 설명입니다.

코드는 `/src/labeling/compute_label_lib.py` 안에 find_side_point, find_otherside_line function 으로 구현되어 있습니다.

##1.  find_side_point

![Alt text](/images/sideline_explain0.png)

### 1.1. input

p1, p2, p3, p4 는 각각 labeling을 통해 input으로 받는 point이다. 

p1 = side_line(end point), p2 = side_line(not end point), p3 = middle_line(end point), p4 = middle_line(not end point)

image_with = 이미지의 가로, image_height = 이미지의 세로

end_line 은 p1, p3을 연결해서 만드는 line으로 끝 점들을 연결 한 것이다.

### 1.2. algorithm

우선 우리가 구해야 하는 side line의 한 point를 찾는 것을 목표로 한다.

image의 특징으로는 image안에 있는 대상의 높이에 따라 이미지 시점으로부터 떨어진 거리를 예측할 수 있는데 이를 사용한다.
 
![Alt text](/images/sideline_explain1.png)

위 그림과 같은 방식으로 정사형 개념을 통하여 각 point들마다 새로운 y 값을 구하였다. (3차원 평면에서 횡단보도들의 z값은 전부 0이라 가정)

이는 image 기준에서 좌표가 (x, y) 일 때 

`(image_height - y) * 24 / 38 * image_height / y`
가 된다.

24/38은 상수값으로 image를 찍을 때 각도를 생각하여 설정한 값이다.(변경 가능)

이를 통해 우리는 새로운 y값을 가진 2개의 end point를 가지게 된다. 다른 side_line의 end point도 end_line위에 있어야 하기 때문에 x좌표를 변수를 두고 거리를 비교함으로써 계산을 할려고 하였지만, 상수 값이 너무 많고 차수가 높아 계산하는데 무리가 있었다.

이를 해결하기 end_line을 새로운 좌표 평면에서 new_end_line으로 설정한다.

기존 end_line이 `y = ax+b` 였다면 new_end_line은 `y= (image_height-(ax + b))* 24 / 38 * image_height / (ax + b)`가 된다.

이는 변수 x에 대하여 -1 차수를 갖는 함수가 된다. 

![Alt text](/images/sideline_explain2.png)

new_p1, new_p3는 p1, p3의 x 좌표를 갖는 new_end_line위의 point이다.

그러면 new_p3(middle_line_point)에서의 접선(tangent line)(using derivative)과 그것의 수직하는 직선(normal line)을 이용하여 new_p1과 우리가 원하는 point의 중점을 구할 수 있고 그로인해 우리가 원하는 다른 sideline의 endpoint를 구할 수 있다.

`tangent line = [12 * a * math.pow(H, 2) / (-19 * math.pow(a * p3[0] + b, 2)),
             (12 * a * math.pow(H, 2) / (19 * math.pow(a * p3[0] + b, 2))) * p1[0] + new_p1y]`

`normal line = [(19 * math.pow(a * p3[0] + b, 2)) / (12 * a * math.pow(H, 2)),
             -p3[0] * (19 * math.pow(a * p3[0] + b, 2)) / (12 * a * math.pow(H, 2)) + new_p3y]`

## 2. find_otherside_line

### 2.1 input

이는 1.1 input 과 동일하다. 

### 2.2 algorithm

p1, p2를 잇는 side_line을 line1 이라 하고, p3, p4를 잇는 middle_line을 line2 라고 한다.

line1과 line2의 intersection point와 1에서 구한 endline_point를 이어주면 우리가 구할려 했던 other side line이 된다.
(이는 사진에서 위로 갈수록 거리가 멀어져 초점이 정해진다는 원리로 인해 가정하였다.)

![Alt text](/images/sideline_explain3.png)


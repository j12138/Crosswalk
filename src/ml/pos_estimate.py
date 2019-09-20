import math
import matplotlib.pyplot as plt
import numpy as np

fps = 1
queue = [[-0.38, -7.0], [-0.3, -5.0]]
error = [0.05, 5.0]


def compute_velocity(fps, queue):
    current = queue[0]
    prev = queue[1]

    dloc = current[0] - prev[0]

    vloc = dloc * fps
    vang = (current[1] - prev[1]) * fps

    vdir = fps * dloc / (math.sin(math.radians(prev[1]))) 

    return vloc, vang, vdir


def estimate_position(vloc, vang, vdir, queue, time):
    fig = plt.figure(figsize=(5, 5))
    ax = plt.subplot(111, projection='polar')
    ax.set_theta_zero_location("N")
    ax.set_rlabel_position(-112.5)
    current = queue[0]

    dloc = vdir * math.sin(current[1])
    next_loc = current[0] + (dloc * time)
    next_ang = current[1] + (vang * time)

    ax.plot(np.arange(current[1] - 10, current[1] + 10, 0.2) * (-1) * np.pi / 180.0,
            np.full((100, 1), current[0] - 0.1))
    ax.plot(np.arange(current[1] - 10, current[1] + 10, 0.2) * (-1) * np.pi / 180.0,
            np.full((100, 1), current[0] + 0.1))

    print(current[0] + 0.1)
    ax.set_rmax(2.0)
    plt.show()


vloc, vang, vdir = compute_velocity(fps, queue)
estimate_position(vloc, vang, vdir, queue, 1)

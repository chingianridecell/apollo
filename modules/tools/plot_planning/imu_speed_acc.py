#!/usr/bin/env python

###############################################################################
# Copyright 2019 The Apollo Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
###############################################################################

import math
from record_reader import RecordItemReader
from imu_speed import ImuSpeed


class ImuSpeedAcc:

    def __init__(self, is_lateral=False):
        self.timestamp_list = []
        self.acc_list = []
        self.imu_speed = ImuSpeed(is_lateral)

    def add(self, location_est):
        self.imu_speed.add(location_est)
        speed_timestamp_list = self.imu_speed.get_timestamp_list()

        index_50ms = len(speed_timestamp_list) - 1
        found_index_50ms = False
        last_timestamp = speed_timestamp_list[-1]
        while index_50ms >= 0:
            current_timestamp = speed_timestamp_list[index_50ms]
            if (last_timestamp - current_timestamp) >= 0.05:
                found_index_50ms = True
                break
            index_50ms -= 1

        if found_index_50ms:
            speed_list = self.imu_speed.get_speed_list()
            acc = (speed_list[-1] - speed_list[index_50ms]) / \
                (speed_timestamp_list[-1] - speed_timestamp_list[index_50ms])
            self.acc_list.append(acc)
            self.timestamp_list.append(speed_timestamp_list[-1])

    def get_acc_list(self):
        return self.acc_list

    def get_timestamp_list(self):
        return self.timestamp_list

    def get_lastest_acc(self):
        if len(self.acc_list) > 0:
            return self.acc_list[-1]
        else:
            return None

    def get_lastest_timestamp(self):
        if len(self.timestamp_list) > 0:
            return self.timestamp_list[-1]
        else:
            return None


if __name__ == "__main__":
    import sys
    import matplotlib.pyplot as plt
    import numpy as np
    from os import listdir
    from os.path import isfile, join

    def plot_freq(x, y, ax, color):
        Fs = len(y) / float(x[-1] - x[0])
        n = len(y)
        k = np.arange(n)
        T = n/Fs
        frq = k/T
        frq = frq[range(n/2)]

        Y = np.fft.fft(y)/n
        Y = Y[range(n/2)]
        ax.plot(frq, abs(Y), c=color)

    folders = sys.argv[1:]
    fig, ax = plt.subplots(2, 1)
    colors = ["g", "b", "r", "m", "y"]
    markers = ["o", "o", "o", "o"]
    for i in range(len(folders)):
        x = []
        y = []
        folder = folders[i]
        color = colors[i % len(colors)]
        marker = markers[i % len(markers)]
        fns = [f for f in listdir(folder) if isfile(join(folder, f))]
        fns.sort()
        for fn in fns:
            reader = RecordItemReader(folder + "/" + fn)
            processor = ImuSpeedAcc(True)
            last_pose_data = None
            last_chassis_data = None
            topics = ["/apollo/localization/pose"]
            for data in reader.read(topics):
                if "pose" in data:
                    last_pose_data = data["pose"]
                    processor.add(last_pose_data)

            data_x = processor.get_timestamp_list()
            data_y = processor.get_acc_list()

            x.extend(data_x)
            y.extend(data_y)

        if len(x) <= 0:
            continue
        #ax.scatter(data_x, data_y, c=color, marker=marker, alpha=0.4)
        ax[0].plot(x, y, c=color, alpha=0.4)
        plot_freq(x, y, ax[1], color)

        ax[0].set_xlabel('Timestamp')
        ax[0].set_ylabel('Acc')

    plt.show()

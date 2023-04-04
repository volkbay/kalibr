import numpy as np
import os
import cv2

from dv import AedatFile
from glob import glob
from matplotlib import pyplot as plt
import csv
from math import pi


def prep_aedat_2_bag(path_aedat, dataset_dir):
    """
        Aims to extract frames and imu information from an aedat file
        Inputs,
            path_aedat: Root path for the aedat file
        Outputs,
            dataset_dir: Folder that contains the output frames and imu information
    """

    img0_dir = dataset_dir + "/cam0"
    if not os.path.exists(img0_dir):
        os.makedirs(img0_dir)

    imu0_csv_dir = dataset_dir + "/imu0.csv"

    frame_tss = []
    with AedatFile(path_aedat) as f:
        # list all the names of streams in the file
        print(f.names)

        for f_count, frame in enumerate(f['frames']):
            frame_tss.append(frame.timestamp)
            imageName = str(frame.timestamp * pow(10,3)).zfill(19) + ".png"
            cv2.imwrite(img0_dir + "/" + imageName, frame.image)

        header = ['timestamp', 'omega_x', 'omega_y', 'omega_z', 'alpha_x', 'alpha_y', 'alpha_z']

        with open(imu0_csv_dir, 'w') as fc:
            writer = csv.writer(fc)
            writer.writerow(header)
            for f_count, frame in enumerate(f['imu']):
                accelerometer = [item*9.8 for item in frame.accelerometer]
                gyroscope = [item/180*pi for item in frame.gyroscope]
                # gyroscope = list(frame.gyroscope)
                info = [str(frame.timestamp * pow(10,3)).zfill(19)] + gyroscope + accelerometer
                writer.writerow(info)

def main():

    path_aedat = "./dat/dvSave.aedat4"
    dataset_dir = "./dat/davis_bag/"
    # dataset_dir = os.path.splitext(path_aedat)[0] + "/dataset_dir"

    # if not os.path.exists(dataset_dir):
    #     os.makedirs(dataset_dir)  

    prep_aedat_2_bag(path_aedat=path_aedat, dataset_dir=dataset_dir)

if __name__ == "__main__":
    main()

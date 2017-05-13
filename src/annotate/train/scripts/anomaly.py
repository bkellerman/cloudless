import argparse
import os
import sys
import requests
import shutil
from urlparse import urlparse

import numpy as np
import scipy
from scipy.ndimage import imread
from sklearn.ensemble import IsolationForest

rng = np.random.RandomState(42)

def create_data(images):
    X = []
    y = []
    for i in images:
        x = []
        y.append(i)
        a = imread(i)
        for k in range(4):
            x.append(np.mean(a[:,:,k]))
            x.append(np.std(a[:,:,k]))
            x.append(np.max(a[:,:,k]) - np.min(a[:,:,k]))
        X.append(x)

    return np.array(X), y

def most_anomalous(X, y):
    clf = IsolationForest(n_estimators=1000, max_samples=100, random_state=rng)
    clf.fit(X)
    y_pred = clf.predict(X)
    return np.take(y, np.where(y_pred==-1)[0])

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Find anomalous images'
    )
    parser.add_argument(
        '--dir', default='/tmp', help='Image file dir'
    )
    args = parser.parse_args()

    image_files = [os.path.join(args.dir, f) for f in os.listdir(args.dir) if '.png' in f]
    X, y = create_data(image_files)
    anom_files = most_anomalous(X, y)
    print anom_files

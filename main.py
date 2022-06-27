from collections import defaultdict
from fileinput import filename

from pip import main

import lsh
import json
import fast
import numpy as np
import os


def save_files(files_path, output):
    files= os.listdir(files_path)
    with open(output,'w') as f:
        for file in files:
            f.write(files_path + file + "\n")
    
if __name__ == "__main__":
    path = "./input/test/"
    filename = "./input/test_suites.txt"
    save_files(path, filename)
    mh_time, ptime, groups = fast.fast_pw(filename, 0.1, 1000, 1, True, 0)
    #print(mh_time)
    #print(ptime)
    i = 1
    for group in groups:
        i += 1
        print(group)
        
    print(i)

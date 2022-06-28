from collections import defaultdict
from fileinput import filename

from pip import main

import lsh
import json
import fast
import numpy as np
import os


def save_files(files_path, output):
    files= os.walk(files_path)
    with open(output,'w') as f:
        for path,dir_list,file_list in files:
            for file_name in file_list:
                if file_name.endswith(".json"):
                    f.write(os.path.join(path, file_name) + "\n")
    
if __name__ == "__main__":
    path = "./input/case/"
    filename = "./input/test_suites.txt"
    # save_files(path, filename)
    mh_time, ptime, groups = fast.fast_pw(filename, 0.8, 1, 10, True, 0)
    #print(mh_time)
    #print(ptime)
    i = 0
    for group in groups:
        if len(group) > 1:
            i += 1
            # print(group)       
    print(i)

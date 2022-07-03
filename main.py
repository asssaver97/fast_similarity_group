from calendar import leapdays
from collections import defaultdict
from fileinput import filename
import sys

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
    # filename = "./input/test_suites.txt"
    # save_files(path, filename)
    filename = sys.argv[1]
    fields=["b_requests","c_requests"]
    minJaccardSimilarty = 0.95
    regularExpression = "b_requests&c_requests"
    if len(sys.argv) > 2:
        regularExpression = sys.argv[2]
        if len(sys.argv) > 3:
            minJaccardSimilarty = float(sys.argv[3])
    mh_time, ptime, groups = fast.fast(filename, regularExpression, minJaccardSimilarty, 1, 20, True, 0)
    # print(mh_time)
    # print(ptime)
    # print(json.dumps(groups, indent=4, separators=(',', ': '), sort_keys=True))
    i = 0
    for group in groups.values():
        i += len(group)
    print("We can merge {} case.".format(i))
    outputpath = "./possibleSimilarCases.json"
    with open(outputpath, "w") as f:
        json.dump(groups, f, indent=4, separators=(',', ': '), sort_keys=True)

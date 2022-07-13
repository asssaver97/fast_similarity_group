import argparse
import json
import os
import sys
from calendar import leapdays
from collections import defaultdict
from fileinput import filename

import numpy as np
from pip import main

import fast
import lsh


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
    parser = argparse.ArgumentParser(description='相似度分析工具')
    parser.add_argument('--input', '-i', help='存放所有测试用例地址的文件名，必要参数', required=True)
    parser.add_argument('--similarity', '-s', help='相似度阈值，非必要参数，默认值为0.95', default=0.95)
    parser.add_argument('--rules', '-r', help='规则表达式，非必要参数，默认值为b_requests&c_requests', default='b_requests&c_requests')
    parser.add_argument('--allowSmallCase', '-a', help='是否允许小case算法，非必要参数，默认True', default=True)
    args = parser.parse_args()
    
    groups = fast.fast(args.input, args.rules, args.similarity, 1, 20, True, 0, args.allowSmallCase)
    
    # print(json.dumps(groups, indent=4, separators=(',', ': '), sort_keys=True))
    i = 0
    for group in groups.values():
        i += len(group)
    # print("We can merge {} case.".format(i))
    outputpath = "./possibleSimilarCases.json"
    with open(outputpath, "w") as f:
        json.dump(groups, f, indent=4, separators=(',', ': '), sort_keys=True)

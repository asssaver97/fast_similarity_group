from enum import unique
import json
import os
import random
from select import select
import sys
import time
from collections import OrderedDict, defaultdict
from struct import pack, unpack
from tokenize import group

import lsh


def loadTestSuite(input_file, bbox=True, k=0):
    """Read the file and prints the feature set of the file

    Args:
        input_file (str): path of input file
        bbox (bool, optional): _description_. Defaults to True.
        k (int, optional): _description_. Defaults to 0.

    Returns:
        TS (dict): key=tc_ID, val=set(coverd lines)
    """
    TS = defaultdict()
    FM = dict()
    with open(input_file) as fin:
        tcID = 1
        for tc in fin:
            tc = tc.strip("\n")
            with open(tc) as f:
                if bbox:
                    load_dict = json.load(f)
                    requests = set()
                    for request in load_dict["b_requests"]:
                        requests.add("b_requests"+request)
                    for request in load_dict["c_requests"]:
                        requests.add("c_requests"+request)
                    TS[tcID] = requests
                    FM[tcID] = tc
                # TODO white box
                else:
                    TS[tcID] = set(tc[:-1].split())
            tcID += 1
    shuffled = TS.items()
    random.shuffle(shuffled)
    TS = OrderedDict(shuffled)
    if bbox:
        TS = lsh.kShingles(TS, k)
    return TS, FM


def storeSignatures(input_file, sigfile, hashes, bbox=True, k=0):
    with open(sigfile, "w") as sigfile:
        with open(input_file) as fin:
            tcID = 1
            for tc in fin:
                if bbox:
                    # shingling
                    tc_ = tc[:-1]
                    tc_shingles = set()
                    for i in range(len(tc_) - k + 1):
                        tc_shingles.add(hash(tc_[i:i + k]))

                    sig = lsh.tcMinhashing((tcID, set(tc_shingles)), hashes)
                else:
                    tc_ = tc[:-1].split()
                    sig = lsh.tcMinhashing((tcID, set(tc_)), hashes)
                for hash_ in sig:
                    sigfile.write(repr(unpack('>d', hash_)[0]))
                    sigfile.write(" ")
                sigfile.write("\n")
                tcID += 1


def loadSignatures(input_file):
    """INPUT
    (str)input_file: path of input file

    OUTPUT
    (dict)TS: key=tc_ID, val=set(covered lines), sigtime"""
    sig = {}
    start = time.process_time()
    with open(input_file, "r") as fin:
        tcID = 1
        for tc in fin:
            sig[tcID] = [pack('>d', float(i)) for i in tc[:-1].split()]
            tcID += 1
    return sig, time.process_time() - start


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #


# lsh + pairwise comparison with candidate set
def fast_pw(input_file, minJaccardSimilarty=0.95, r=1, b=100, bbox=True, k=0):
    """INPUT
    (str)input_file: path of input file
    (int)r: number of rows
    (int)b: number of bands
    (bool)bbox: True if BB prioritization
    (int)k: k-shingle size (for BB prioritization). If 0 take the whole sentence as feature.

    OUTPUT
    (list)P: prioritized test suite
    """
    threshold = 0
    if minJaccardSimilarty < 1:
        while float(threshold)/float(threshold+1) < minJaccardSimilarty:
            threshold += 1
    print("We count the number of requests less than {} as a small case.".format(threshold))
    maxJaccardDistance = 1 - minJaccardSimilarty
    # number of hash functions
    n = r * b  
    
    # generate hash functions
    hashes = [lsh.hashFamily(i) for i in range(n)] 

    # generate feature set of each file
    test_suite, file_name_map = loadTestSuite(input_file, bbox=bbox, k=k) 
    print("Before group, we heve {} case.".format(len(test_suite)))
    # print(file_name_map)
    # generate minhashes signatures
    mh_t = time.process_time()
    tcs_minhashes = {tc[0]: lsh.tcMinhashing(tc, hashes)
                        for tc in test_suite.items()}
    mh_time = time.process_time() - mh_t
    #print(json.dumps(tcs_minhashes, sort_keys=True, indent=4, separators=(',', ':')))
    print("minHash time: {}".format(mh_time))
    ptime_start = time.process_time()
    
    # get the ID of test cases
    tcs = set(tcs_minhashes.keys())

    # BASE = 0.5
    # SIZE = int(len(tcs)*BASE) + 1

    # Locality-Sensitive Hashing (LSH)
    # bucket = lsh.LSHBucket(tcs_minhashes.items(), b, r, n)
    # print(bucket)

    # store the results
    group_tcs = list()
    # prioritized_tcs = [0]
    tmp_group = list()

    # First TC
    # selected_tcs_minhash = lsh.tcMinhashing((0, set()), hashes)
    selected_tc = random.choice(tcs_minhashes.keys())
    selected_tcs_minhash = tcs_minhashes[selected_tc]
    # for i in range(n):
    #     if tcs_minhashes[first_tc][i] < selected_tcs_minhash[i]:
    #         selected_tcs_minhash[i] = tcs_minhashes[first_tc][i]
    # prioritized_tcs.append(first_tc)
    tmp_group.append(file_name_map[selected_tc])
    tcs -= set([selected_tc])
    del tcs_minhashes[selected_tc]
    
    while len(tcs_minhashes) > 0:
        tmpMaxJaccardDistance = maxJaccardDistance
        n = float(len(test_suite[selected_tc]))
        if n < threshold:
            # print("only one")
            tmpMaxJaccardDistance = n / (n+2)
        min_dist = sys.maxsize
        for candidate in tcs_minhashes:
            dist = lsh.jDistanceEstimate(
                    selected_tcs_minhash, tcs_minhashes[candidate])
            if dist < min_dist:
                selected_tc, min_dist = candidate, dist
                
        selected_tcs_minhash = tcs_minhashes[selected_tc]  
        tcs -= set([selected_tc])
        del tcs_minhashes[selected_tc]
        
        if min_dist > tmpMaxJaccardDistance:
            group_tcs.append(tmp_group[:])
            tmp_group.clear()
        tmp_group.append(file_name_map[selected_tc])
        
        if min_dist < tmpMaxJaccardDistance and tmpMaxJaccardDistance < maxJaccardDistance:
            print("防止连锁反应")
            group_tcs.append(tmp_group[:])
            tmp_group.clear()
            tmp_group.append(file_name_map[selected_tc])
            
    group_tcs.append(tmp_group[:])
    ptime = time.process_time() - ptime_start
    print("prioritize time: {}".format(ptime))
    return mh_time, ptime, group_tcs
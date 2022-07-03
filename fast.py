from dataclasses import field
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


def loadTestSuite(input_file, fields=["b_requests","c_requests"], bbox=True, k=0):
    """Read the file and prints the feature set of the file

    Args:
        input_file (str): path of input file
        bbox (bool, optional): _description_. Defaults to True.
        k (int, optional): _description_. Defaults to 0.

    Returns:
        TS (dict): key=tc_ID, val=set(coverd lines)
    """
    TS = defaultdict()
    FM = defaultdict()
    owner_map = defaultdict()
    with open(input_file) as fin:
        tcID = 1
        for tc in fin:
            tc = tc.strip("\n")
            with open(tc) as f:
                if bbox:
                    load_dict = json.load(f)
                    requests = set()
                    for field in fields:
                        for request in load_dict[field]:
                            requests.add(field+request)
                    TS[tcID] = requests
                    FM[tcID] = tc
                    owner_map[tcID] = load_dict["owner"]
                # TODO white box
                else:
                    TS[tcID] = set(tc[:-1].split())
            tcID += 1
    shuffled = TS.items()
    random.shuffle(shuffled)
    TS = OrderedDict(shuffled)
    if bbox:
        TS = lsh.kShingles(TS, k)
    return TS, FM, owner_map


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

def contains(intput_files):
    print("to do")


# lsh + pairwise comparison with candidate set
def fast_pw(input_file, threshold=0, maxJaccardDistance=0.05, fields=["b_requests","c_requests"], group_tcs={},r=1, b=100, bbox=True, k=0):
    """INPUT
    (str)input_file: path of input file
    (int)r: number of rows
    (int)b: number of bands
    (bool)bbox: True if BB prioritization
    (int)k: k-shingle size (for BB prioritization). If 0 take the whole sentence as feature.

    OUTPUT
    (list)P: prioritized test suite
    """
    # number of hash functions
    n = r * b  
    
    # generate hash functions
    hashes = [lsh.hashFamily(i) for i in range(n)] 

    # generate feature set of each file
    test_suite, file_name_map, owner_map = loadTestSuite(input_file, fields=fields, bbox=bbox, k=k) 
    # print("Before group, we heve {} case.".format(len(test_suite)))
    # print(file_name_map)
    # generate minhashes signatures
    mh_t = time.process_time()
    tcs_minhashes = {tc[0]: lsh.tcMinhashing(tc, hashes)
                        for tc in test_suite.items()}
    # print(tcs_minhashes)
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
    # group_tcs = {}
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
    tmp_group.append({"case:": file_name_map[selected_tc], 
                      "owner:": owner_map[selected_tc]})
    tcs -= set([selected_tc])
    del tcs_minhashes[selected_tc]
    
    while len(tcs_minhashes) > 0:
        tmpMaxJaccardDistance = maxJaccardDistance
        n = float(len(test_suite[selected_tc]))
        if n < threshold:
            # print("only one")
            tmpMaxJaccardDistance = n / (n+1)
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
            if len(tmp_group) > 1:
                group_tcs.setdefault(round(last_dist,3),[]).append(tmp_group[:])
            tmp_group.clear()
        tmp_group.append({"case:": file_name_map[selected_tc], 
                          "owner:": owner_map[selected_tc]})
        
        if min_dist < tmpMaxJaccardDistance and tmpMaxJaccardDistance < maxJaccardDistance:
            print("防止连锁反应")
            if len(tmp_group) > 1:
                group_tcs.setdefault(round(last_dist,3),[]).append(tmp_group[:])
            tmp_group.clear()
            tmp_group.append({"case:": file_name_map[selected_tc], 
                            "owner:": owner_map[selected_tc]})
        last_dist = min_dist
    if len(tmp_group) > 1:        
        group_tcs.setdefault(round(last_dist,3),[]).append(tmp_group[:])
    ptime = time.process_time() - ptime_start
    print("prioritize time: {}".format(ptime))
    return mh_time, ptime, group_tcs


def fast(input_file, regularExpression="b_requests&c_requests", minJaccardSimilarty=0.95, r=1, b=100, bbox=True, k=0):
    threshold = 0
    if minJaccardSimilarty < 1:
        while float(threshold)/float(threshold+1) < minJaccardSimilarty:
            threshold += 1
    print("We count the number of requests less than {} as a small case.".format(threshold))
    maxJaccardDistance = 1 - minJaccardSimilarty
    fields = list()
    field = ""
    group_tcs = {}
    i = 1
    print("Ragular expression {}:".format(i), end=" ")
    for c in regularExpression:
        if c == "&":
            print(field, end=" & ")
            fields.append(field)
            field = ""
        elif c == "|":
            print(field)
            i += 1
            fields.append(field)
            field = ""
            mh_time, ptime, group_tcs=fast_pw(input_file, threshold, maxJaccardDistance,fields,group_tcs,r,b,bbox,k)
            print("Ragular expression {}:".format(i), end=" ")
        else:
            field += c
    print(field)
    fields.append(field)
    mh_time, ptime, group_tcs=fast_pw(input_file, threshold, maxJaccardDistance,fields,group_tcs,r,b,bbox,k)
    return mh_time, ptime, group_tcs

import copy
import json
import os
import random
import sys
import time
from collections import OrderedDict, defaultdict
from dataclasses import field
from enum import unique
from select import select
from struct import pack, unpack
from tokenize import group

from numpy import choose, integer

import lsh


def loadTestSuite(input_file, field="b_requests", bbox=True, k=0):
    """Read the file and prints the feature set of the file

    Args:
        input_file (str): path of input file
        bbox (bool, optional): _description_. Defaults to True.
        k (int, optional): _description_. Defaults to 0.

    Returns:
        TS (dict): key=tc_ID, val=set(coverd lines)
    """
    TS = defaultdict()
    owner_map = defaultdict()
    with open(input_file) as fin:
        for tc in fin:
            tc = tc.strip("\n")
            with open(tc) as f:
                if bbox:
                    load_dict = json.load(f)
                    TS[tc] = load_dict[field]
                    owner_map[tc] = load_dict["owner"]
                # TODO white box
                else:
                    TS[tc] = set(tc[:-1].split())
    shuffled = TS.items()
    random.shuffle(shuffled)
    TS = OrderedDict(shuffled)
    if bbox:
        TS = lsh.kShingles(TS, k)
    return TS, owner_map


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
def fast_pw(input_file, group_tcs:dict, minJaccardSimilarty=0.95, rule="b_requests&c_requests", fields=["b_requests","c_requests"], 
            weights=[1, 1],r=1, b=100, bbox=True, k=0, allowSmallCase=True):
    """
    Args:
        input_file (str): path of input file.
        threshold (int, optional): _description_. Defaults to 0.
        maxJaccardDistance (float, optional): _description_. Defaults to 0.05.
        fields (list, optional): _description_. Defaults to ["b_requests","c_requests"].
        group_tcs (dict, optional): _description_. Defaults to {}.
        r (int, optional): number of rows. Defaults to 1.
        b (int, optional): number of bands. Defaults to 100.
        bbox (bool, optional): True if BB prioritization. Defaults to True.
        k (int, optional): k-shingle size (for BB prioritization). If 0 take the whole sentence as feature.. Defaults to 0.

    Returns:
        mh_time:
        ptime: 
        group_tcs:
    """
    print(rule)
        
    # number of hash functions
    n = r * b  
    
    # generate hash functions
    hashes = [lsh.hashFamily(i) for i in range(n)] 

    for i, weight in enumerate(weights):
        # calculate the similatity threshold for each field
        tmpMinJaccardSimilarty = weight * minJaccardSimilarty
        print(tmpMinJaccardSimilarty)
        threshold = 0
        if minJaccardSimilarty < 1:
            while float(threshold)/float(threshold+1) < tmpMinJaccardSimilarty:
                threshold += 1
        # generate feature set of each file
        test_suite, owner_map = loadTestSuite(input_file, field=fields[i], bbox=bbox, k=k) 
        # generate minhashes signatures
        mh_t = time.process_time()
        tcs_minhashes = {tc[0]: lsh.tcMinhashing(tc, hashes)
                            for tc in test_suite.items()}
        # print(" ".join(tcs_minhashes))
        mh_time = time.process_time() - mh_t
        print("minHash time: {}".format(mh_time))
        ptime_start = time.process_time()
        
        # get the ID of test cases
        tcs = set(tcs_minhashes.keys())
        choose_tcs = {"null": []}
        if i > 0 :
            for tc in tcs:
                choose_tcs[tc] = list(group_tcs[tc]["similar_cases"].keys())
        else: 
            for tc in tcs:
                choose_tcs[tc] = list(tcs)
                choose_tcs[tc].remove(tc)

        for selected_tc in tcs:
            # selected_tc = random.choice(tcs_minhashes.keys())
            selected_tcs_minhash = tcs_minhashes[selected_tc]
            if selected_tc not in group_tcs:
                group_tcs[selected_tc] = {"owner": owner_map[selected_tc], "similar_cases": {}}
            # print(type(choose_tcs[selected_tc]))
            candidates = copy.deepcopy(choose_tcs[selected_tc])
            for candidate in choose_tcs[selected_tc]:
            # tcs -= set([selected_tc])
            # del tcs_minhashes[selected_tc]
            # while len(tcs_minhashes) > 0:
                tmptmpMinJaccardSimilarty = tmpMinJaccardSimilarty
                n = float(len(test_suite[selected_tc]))
                if allowSmallCase and n < threshold:
                    # print("only one")
                    tmptmpMinJaccardSimilarty = n / (n+1)
                sim = lsh.jSimilarityEstimate(
                        selected_tcs_minhash, tcs_minhashes[candidate])
                if sim >= tmptmpMinJaccardSimilarty:
                    group_tcs[selected_tc]["similar_cases"].setdefault(candidate, {"owner": owner_map[selected_tc], 
                                                                                   "Jaccard similarity": sim,
                                                                                   "base on rule": rule})
                elif i > 0:
                    # print(selected_tc)
                    # print(candidate)
                    group_tcs[selected_tc]["similar_cases"].pop(candidate)
        ptime = time.process_time() - ptime_start
        print("prioritize time: {}".format(ptime))
    return group_tcs    
    

def fast(input_file, regularExpression="b_requests&c_requests", minJaccardSimilarty=0.95, r=1, b=100, bbox=True, 
         k=0, allowSmallCase=True):
    fields = list()
    field = ""
    weights = list()
    weight = 1
    rule = ""
    group_tcs = defaultdict()
    i = 1
    for c in regularExpression:
        if c == "&":
            rule = rule + field + " & "
            # print(field, end=" & ")
            weights.append(weight)
            weight = 1
            fields.append(field)
            field = ""
        elif c == "|":
            rule = rule + field
            weights.append(weight)
            weight = 1
            fields.append(field)
            field = ""
            print("Ragular expression {}:".format(i), end=" ")
            group_tcs=fast_pw(input_file=input_file, group_tcs=group_tcs, minJaccardSimilarty=minJaccardSimilarty,
                              rule=rule, fields=fields, weights=weights, r=r, b=b, bbox=bbox, k=k, allowSmallCase=allowSmallCase)
            fields.clear()
            weights.clear()
            rule = ""
            i += 1
        elif c == "*":
            weight = float(field)
            field = ""
        else:
            field += c
    rule = rule + field
    weights.append(weight)
    fields.append(field)
    print("Ragular expression {}:".format(i), end=" ")
    group_tcs=fast_pw(input_file=input_file, group_tcs=group_tcs, minJaccardSimilarty=minJaccardSimilarty,
                       rule=rule, fields=fields, weights=weights, r=r, b=b, bbox=bbox, k=k, allowSmallCase=allowSmallCase)
    return group_tcs

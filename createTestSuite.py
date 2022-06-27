from fileinput import filename
import json
import random


with open("./input/100.json",'r') as load_f:
    load_dict = json.load(load_f)

testfiles = list()
for i in range(100):
    testfiles.append(str(i)+".xml")

for i in range(1000):
    m, n = random.randint(1, 20), random.randint(1,20)
    br, cr = list(), list()

    for _ in range(m):
        j = random.randint(0, 99)
        br.append(testfiles[j])

    for _ in range(n):
        j = random.randint(0, 99)
        cr.append(testfiles[j])

    load_dict["b_requests"] = br
    load_dict["c_requests"] = cr

    filename = "./input/test/" + str(i) + ".json" 
    with open(filename, 'w') as f:
        json.dump(load_dict, f, sort_keys=True, indent=4)
        
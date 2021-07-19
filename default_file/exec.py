#!/usr/bin/env python3
# coding: utf-8

import sys, json, jsonpickle, copy, pickle

from platon import makepayload

if __name__ == "__main__":
    if len(sys.argv) < 5:
        msg = ("Sandbox did not call exec properly:\n"
               +"Usage: python3 exec.py [exec] [input_json] [output_json] [result_json]")
        print(msg, file=sys.stderr)
        sys.exit(1)

    command_exec = sys.argv[1]
    input_json = sys.argv[2]
    output_json = sys.argv[3]
    result_json = sys.argv[4]
    
    with open(input_json, "r+") as f:
        dic = json.load(f)
        copy_dic = copy.deepcopy(dic)
    
    if command_exec in dic:
        exec(dic[command_exec], copy_dic)
    else:
        print(("No default next script. Please define a next script."),
              file = sys.stderr)
        sys.exit(1)

    for key in copy_dic.keys():
        if key in dic.keys():
            dic[key] = copy_dic[key]

    ploaddic = makepayload(dic)
    with open(result_json,"w+") as pload:
        pload.write(jsonpickle.encode(ploaddic, unpicklable=False))

    with open(output_json, "wb") as output:
        output.write(pickle.dumps(dic))

    with open(input_json, "w+") as f:
        f.write(jsonpickle.encode(dic, unpicklable=False))
    
    sys.exit(0)
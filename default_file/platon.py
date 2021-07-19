import os, subprocess, json, jsonpickle

def valid_key(key):
    # pas de code 
    if key.endswith(".py"): 
        return False
    # pas les settings 
    if key=="settings":
        return False
    # pas les variables "_privées" 
    if key.startswith("_"):
        return False
    # pas les start, next et end
    if key in ["start", "next", "end"]:
        return False
    return True

def makepayload(dic, mode=""):
    """
    Objectif réduire la taille du dict retourné au front.
    """
    d={}
    for key in dic.keys():
        if valid_key(key):
            d[key]= dic[key]
    return d

def build(plid, params):
    """
    création de l'environement
    """
    try:
        os.mkdir(str(plid))
        with open(str(plid)+".json", "r") as f:
            pl = json.load(f)
            pl.update(params)
    except FileExistsError as e:
        print(e)

    try:
        f = open(os.path.join(str(plid), "pl.json"), "w")
        f.write(jsonpickle.encode(pl, unpicklable=False))

        for file in pl["__files"]:
            f = open(os.path.join(str(plid), file), "w")
            f.write(pl["__files"][file])
    except Exception as e:
        print(e)

    command = "python3 builder.py pl.json processed.json"
    try:
        subprocess.run([command], shell=True, cwd=str(plid))
    except Exception as e:
        return e

    print(plid)

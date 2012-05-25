
import json

def read_json(fname):
    with open(fname) as f:
        return json.loads(f.read())

def write_json(obj, fname):
    with open(fname, "w") as f:
        f.write(json.dumps(obj))


import json

def read_json(fname):
    with open(fname) as f:
        return json.loads(f.read())

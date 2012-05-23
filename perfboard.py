#!/usr/bin/env python

import argparse, commands, collections
import datetime
import json
import os
import glob
import logging
import pprint
import time

import score

from util import read_json

log = None

def init_logging():
    global log
    if log:
        return
    log = logging.getLogger("perfboard")
    log.setLevel(logging.DEBUG)
    formatter = logging.Formatter(fmt="%(asctime)s.%(msecs)03d - %(name)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    log.addHandler(handler)

class AbstractRecognizer( object ):
    """Defines a generic recognizer interface. Override `process` and `results`. 
    Set `self.labels_recognized` to specify the labels this recognizer can produce
    """
    def __init__(self, labels):
        self.labels_recognized = []

    def process(self, chunk):
        """process chunk of data (typically json-encoded list of records) and update internal state"""
        pass

    def detected(self):
        """returned order list of recognition results."""
        pass

    def version(self):
        head, tail = os.path.split(__file__)
        module = tail.rstrip(".pyc")
        return ("%s.%s-%s"% (module, self.__class__.__name__, commands.getoutput('git rev-parse HEAD'))).lstrip("./")


def csv(value):
    return map(str, value.split(",")) 

def json_encode(obj):
    return json.dumps(obj, default=lambda obj: obj.isoformat() if isinstance(obj, datetime.datetime) else None)

def main():
    init_logging()

    parser = argparse.ArgumentParser(description="performance metric dashboard for continuous context recognition")
    parser.add_argument("truths", metavar='TRUTH_FILE', type=str, nargs="+", help='ground truth files')
    parser.add_argument("--outpath", metavar="OUTPUT_PATH", type=str, help="where to write output file(s)")
    parser.add_argument("--recognizers", metavar="RECOGNIZERS", type=csv, default=[], required=True, help="comma-seperated fully qualified class names of recognizers to use")

    args = parser.parse_args()

    rzs = init_recognizers(args.recognizers)

    results = []

    recogs = collections.defaultdict(int)

    for truth_file in args.truths:
        log.info("processing %s..." % truth_file)
        d = read_json(truth_file) #read the ground truth files

        for data_file in glob.glob(d["data_path"]):
            log.info("reading data from %s..." % data_file)
            with open(data_file) as f: #read the raw data
                chunk = f.read()
                for rz in rzs.values():
                    rz.process(chunk) #feed raw data to each of the recognizers
                    
        for rz in rzs.values():        
            log.info("evaluating recognizer %s for label %s..." % (rz, rz.label))
            res = d.copy()
            res["detected"] = rz.results()
            res["labels"] = [x for x in res["labels"] if x["label"] == rz.label] #filter for binary classification
            res["scores"] = score.score_results(res)
            res["recognizer"] = rz.version()
            recogs[res["recognizer"]] += 1
            res["labels_file"] = truth_file
            results.append(res)

    scored = score.score_aggregate(results)
    scored["results"] = results
    scored["recognizers"] = recogs.keys()
    scored["t"] = datetime.datetime.now().isoformat()

    if args.outpath:
        with open(args.outpath, "w") as f:
            log.info("writing scored results to %s..." % args.outpath)
            f.write(json_encode(scored))

    else:
        print json_encode(scored)

def init_recognizers(rzs):
    d = dict() #import user-defined recognizers
    for rz_name in rzs:
        p = rz_name.rsplit(".", 1)
        if not len(p) == 2:
            raise ValueError("recognizers must be specified by <module_name>.<class_name>")
        module_name, class_name = p[0], p[1]
        module = import_name(module_name)
        d[rz_name] = getattr(module, class_name)() #init the recognizer
    return d


def import_name(name):
    mod = __import__(name)
    components = name.split('.')
    for comp in components[1:]:
        mod = getattr(mod, comp)
    return mod        

    
if __name__ == "__main__":
    main()


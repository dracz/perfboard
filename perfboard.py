#!/usr/bin/env python

import argparse, commands, collections, shutil
import datetime
import json
import os
import glob
import logging
import pprint
import time

import score

from util import read_json, write_json

DEFAULT_OUTPATH = "static"

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
    """Defines a simple generic recognizer interface."""
    def process(self, recs):
        """process raw data records and update internal state. `recs` is an iterable."""
        raise NotImplementedError("")

    def detected(self, time_range=None):
        """return ordered list of recognition results of the form `[{"t1":<datetime_start>, "t2":<datetime_end>, "label":<string>}, ...]`
        `time_range`, if present is a 2-tuple of datetime objects that restrict the result set to items with timestamps within, or overlapping, the range.
        """
        raise NotImplementedError()

    def labels(self):
        """returns a list of label classes that this recognizer supports"""
        raise NotImplementedError()


def csv(value):
    return map(str, value.split(",")) 

def json_encode(obj):
    return json.dumps(obj, default=lambda obj: obj.isoformat() if isinstance(obj, datetime.datetime) else None)

SCORES_FILE = "scores.json"        #hold latest scores
SCORES_LIST = "scores_list.json"

def main():
    init_logging()

    parser = argparse.ArgumentParser(description="performance metric dashboard for continuous context recognition")
    parser.add_argument("truths", metavar='TRUTH_FILE', type=str, nargs="+", help='ground truth files')
    parser.add_argument("--outpath", metavar="OUTPUT_PATH", type=str, default=DEFAULT_OUTPATH, help="dir to write `scores.json`")
    parser.add_argument("--norotate", action="store_true", default=False, help="to disable rotating scores")
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
                    
        for rz_name, rz in rzs.iteritems():        
            log.info("evaluating recognizer %s for labels %s..." % (rz, rz.labels()))
            res = d.copy()
            res["detected"] = rz.results()
            res["labels"] = [x for x in res["labels"] if x["label"] in rz.labels()] 
            res["scores"] = score.score_results(res)
            res["recognizer"] = rz_name
            recogs[res["recognizer"]] += 1
            res["labels_file"] = truth_file
            results.append(res)

    scored = score.score_aggregate(results)
    scored["results"] = results
    scored["recognizers"] = recogs.keys()
    scored["t"] = datetime.datetime.now().isoformat()

    sf = os.path.join(args.outpath, SCORES_FILE)
    if os.path.exists(sf):
        if not args.norotate:
            #copy existing scores.json to scores-<iso time>.json, update scores_history
            dt = read_json(sf)["t"]
            head, tail = os.path.split(sf)
            name, ext = tail.rsplit(".", 1)
            fn = "%s-%s.%s"%(name,dt,ext)
            nf = os.path.join(args.outpath, fn)
            log.info("rotating %s to %s..." % (sf, nf))
            shutil.copyfile(sf, nf)

            sl = os.path.join(args.outpath, SCORES_LIST)
            log.info("updating %s..." % sl)        
            if not os.path.exists(sl):
                write_json([fn], sl)
            else:
                l = read_json(sl)
                l.insert(0, fn)
                write_json(l, sl)
            
    log.info("writing %s..." % sf)        
    write_json(scored, sf)

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


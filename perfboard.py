#!/usr/bin/env python

import argparse, commands, collections, shutil
import datetime
import json
import os
import glob, gzip
import logging
import pprint, re
import time

import score, viz

from util import read_json, write_json
from iso8601.iso8601 import parse_date

DEFAULT_OUTPATH = "static"
SCORES_DIR = "scores"
MAX_SAMPLE_RATE = 60

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

def csv(value):
    """Return list of strings from comma seperated string"""
    return map(str, value.split(",")) 

def json_encode(obj):
    return json.dumps(obj, default=lambda obj: obj.isoformat() if isinstance(obj, datetime.datetime) else None)

SCORES_FILE = "scores/scores.json"        #hold latest scores
SCORES_LIST = "scores/scores_list.json"

def main():
    init_logging()

    parser = argparse.ArgumentParser(description="performance metric dashboard for continuous context recognition")
    parser.add_argument("truths", metavar='TRUTH_FILE', type=str, nargs="+", help='ground truth files')
    parser.add_argument("--outpath", metavar="OUTPUT_PATH", type=str, default=DEFAULT_OUTPATH, help="dir to write `scores.json`")
    parser.add_argument("--norotate", action="store_true", default=False, help="to disable rotating scores")
    parser.add_argument("--debug", action="store_true", default=False, help="add extra debugging info to the result scores")
    parser.add_argument("--recognizers", metavar="RECOGNIZERS", type=csv, default=[], required=True, help="comma-seperated fully qualified class names of recognizers to use")

    args = parser.parse_args()

    rzs = init_recognizers(args.recognizers)

    results = []

    recogs = collections.defaultdict(int)

    for truth_file in args.truths:
        log.info("processing %s..." % truth_file)
        d = read_json(truth_file) #read the ground truth files

        head, tail = os.path.split(truth_file)
        data_path =  os.path.join(head, d["data_path"])

        sample_times = collections.defaultdict(list)

        for data_file in glob.glob(data_path):
            log.info("reading data from %s..." % data_file)

            if data_file.endswith(".gz"):
                chunk = gzip.open(data_file).read()
            else:
                chunk = open(data_file).read()

            try:
                recs = json.loads(chunk)
            except:
                print "FAILED to parse recs from %s" % data_file
                print "trying to escape slashes and reparse..."
                s = re.sub(r'\\[^\\]', r'\\\\', chunk) 
                recs = json.loads(s)
                
            if recs:
                d["t1"] = min([recs[0]["time"], ])
                d["t2"] = max([recs[-1]["time"], ])

            for rz in rzs.values():
                rz.process(recs) #feed raw data to each of the recognizers

            if args.debug:
                
                for rec in recs:
                    sample_times[rec["type"]].append(parse_date(rec["time"]))

        if args.debug:
            #sampling intervals 
            d["sample_intervals"] = {}
            for k, v in sample_times.iteritems():
                si = []
                for i in v:
                    if si and (i - si[-1][1]) < datetime.timedelta(seconds=MAX_SAMPLE_RATE):
                        si[-1][1] = i
                        si[-1][2] += 1
                    else:
                        si.append( [i, i, 1] )
                intervals = map(lambda x: dict(t1=x[0].isoformat(), t2=x[1].isoformat(), count=x[2]), si)
                d["sample_intervals"][k] = dict(intervals=intervals, count=len(v)) 

        for rz_name, rz in rzs.iteritems():        
            log.info("evaluating recognizer %s for labels %s..." % (rz, rz.labels_supported()))
            res = d.copy()
            res["detected"] = rz.get_results()
            res["labels"] = [x for x in res["labels"] if x["label"] in rz.labels_supported()] 
            res["scores"] = score.score_results(res)
            res["recognizer"] = rz_name
            recogs[res["recognizer"]] += 1
            res["labels_file"] = truth_file
            results.append(res)

            rz.reset()

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

            fn = os.path.join(SCORES_DIR, "%s-%s.%s"%(name,dt,ext))
            nf = os.path.join(args.outpath, fn)
            log.info("rotating %s to %s..." % (sf, nf))
            shutil.copyfile(sf, nf)

            sl = os.path.join(args.outpath, SCORES_LIST)
            log.info("updating %s..." % sl)        
            ds = SCORES_FILE
            if not os.path.exists(sl):
                write_json([ds, fn], sl)
            else:
                l = read_json(sl)
                if not l[0] == ds:
                    l.insert(0, ds)
                l.insert(1, fn)
                write_json(l, sl)
            
    log.info("writing %s..." % sf)        
    write_json(scored, sf)

import sys

def init_recognizers(rzs):
    d = dict() #import user-defined recognizers
    for rz_name in rzs:
        p = rz_name.rsplit(".", 1)
        if not len(p) == 2:
            raise ValueError("recognizers must be specified by [<path>/]<module_name>.<class_name>")
        b, class_name = p[0], p[1]

        path, module_name = os.path.split(b)
        if path:
            sys.path.append(path)

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


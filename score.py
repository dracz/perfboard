#!/usr/bin/env python
            
from optparse import OptionParser
import datetime, glob, os, sys, itertools
from itertools import islice

import json, pprint
from collections import defaultdict

sys.path.append("..")

from iso8601.iso8601 import parse_date

def score_results(results):
    """Score list of detected events to list of ground truth items (from test_cases.py). 
    See: J.A. Ward et al. (2011) http://dl.acm.org/citation.cfm?id=1889687

    returns dict containing:

    segments - ordered list of scored segments. segment is dict with t1, t2, score, and optional err
    """
    truth_time = 0
    truths = results["labels"]
    detected = results["detected"]

    for truth in truths:
        truth_time += (parse_date(truth["t2"]) - parse_date(truth["t1"])).seconds

    overlapped = False
    overlaps = defaultdict(list) #list of state index that overlap truth keyed on truth index

    segs = extract_segments(results)
    segs = score_segments(segs, truths, detected)

    return dict(segments=segs,
                frame_score=score_frames(segs),
                events=score_events(truths, detected, segs))
               
def extract_segments(results):
    """extract the time segments from labels and detected """
    tt = [ ( parse_date(x["t1"]), parse_date(x["t2"]) ) for x in results["labels"]+results["detected"] ]
    ts = sorted(itertools.chain.from_iterable( tt ))
    t1 = parse_date(results["t1"])
    if t1 < ts[0]:
        ts.insert(0, t1)
    t2 = parse_date(results["t2"])
    if t2 > ts[-1]:
        ts.append(t2)
    return [ dict(t1=x[0].isoformat(), t2=x[1].isoformat()) for x in list(sliding_window(ts, 2)) ]

def label_segments(segs, truths, detected):
    """for each segment, attach `label` from `truth` and `match=True` when truth detected label matches truth, else False if match fails"""
    for seg in segs:
        for truth in truths:
            if time_overlap(seg, truth):            
                seg["label"] = truth["label"]
                for det in detected:
                    if time_overlap(seg, det):
                        if det["label"] == truth["label"]:
                            seg["match"] = True
                        else:
                            seg["match"] = False
    return segs

def score_frames(segs):
    """score the frame errors from the segments"""
    d = dict(D=0, I=0, F=0, M=0, Us=0, Ue=0, Os=0, Oe=0, TP=0, TN=0)
    for seg in segs:
        secs = (parse_date(seg["t2"]) - parse_date(seg["t1"])).total_seconds()
        if seg["score"] == "FP" or seg["score"] == "FN":
            if seg.get("err"):
                d[seg["err"]] += secs
        elif seg["score"] == "TP" or seg["score"] == "TN":
            d[seg["score"]] += secs

    d["P"] = d["D"] + d["F"] + d["Us"] + d["Ue"] + d["TP"] #positive frames
    d["N"] = d["I"] + d["M"] + d["Os"] + d["Oe"] + d["TN"] #negative frames

    #calculate frame ratessiter
    ret = dict(p_rates={}, n_rates={}, frame_counts=d)

    POS = ["D", "F", "Us", "Ue", "TP"]
    NEG = ["I", "M", "Os", "Oe", "TN"]

    if d["P"]:
        for i in POS:
            ret["p_rates"][i+"r"] = d[i]*1.0 / d["P"]

    if d["N"]:
        for i in NEG:
            ret["n_rates"][i+"r"] = d[i]*1.0 / d["N"]
    if d["P"] or d["N"]:   
        ret["acc"] = (d["TP"]*1.0 + d["TN"]) / (d["P"]*1.0 + d["N"]) 
        ret["p_rate"] = d["P"]*1.0/(d["P"] + d["N"])
        ret["n_rate"] = d["N"]*1.0/(d["P"] + d["N"])
    return ret

def score_segments(segs, truths, detected):        
    """score the segments extracted from truths and detected lists"""
    matches = 0
    for seg in segs:
        truth_match = detected_match = False
        for truth in truths:
            if time_overlap(seg, truth):
                truth_match = True
        for det in detected:
            if time_overlap(seg, det):
                detected_match = True

        #assign basic score to segment (TP|TN|FP|FN)
        if truth_match:
            if detected_match:
                seg["score"] = "TP"
            else:
                seg["score"] = "FN"
        else:
            if detected_match:
                seg["score"] = "FP"
            else:
                seg["score"] = "TN"

    # assign error class to all FN and FP. fig 3, ward et al 2011
    prev_score = next_score = None
    for i in range(len(segs)):
        score = segs[i]["score"]
        if score == "TP" or score == "TN":
            continue 

        if i < len(segs)-1:
            next_score = segs[i+1]["score"]

        if i > 0:
            prev_score = segs[i-1]["score"]

        if i == 0: #beginning of sequence

            if score == "FP":
                if next_score is None or next_score == "TN" or next_score == "FN":
                    segs[i]["err"] = "I"
                elif next_score == "TP":
                    segs[i]["err"] = "Os"
                else:
                    warn("Unhandled error case: %s followed by %s" % (score, next_score))

            elif score == "FN":
                if next_score is None or next_score == "TN" or next_score == "FP":
                    segs[i]["err"] = "D"
                elif next_score == "TP":
                    segs[i]["err"] = "Us"
                else:
                    warn("Unhandled error case: %s followed by %s" % (score, next_score))

        elif i == len(segs) - 1: #end of sequence

            if score == "FP":
                if prev_score == "TN" or prev_score == "FN":
                    segs[i]["err"] = "I"
                elif prev_score == "TP":
                    segs[i]["err"] = "Oe"
                else:
                    warn("Unhandled error case: %s followed by %s" % (score, next_score))
                    
            elif score == "FN":
                if prev_score == None or prev_score == "TN" or prev_score == "FP":
                    segs[i]["err"] = "D"
                elif prev_score == "TP":
                    segs[i]["err"] = "Ue"
                else:
                    warn("Unhandled error case: %s followed by %s" % (score, next_score))

        else: #middle sequence

            if score == "FP":
                if next_score == "TP":
                    if prev_score == "TP":
                        segs[i]["err"] = "M"
                    elif prev_score == "TN" or prev_score == "FN":
                        segs[i]["err"] = "Os"
                    else:
                        warn("Unhandled error case: %s %s %s" % (prev_score, score, next_score))

                elif next_score == "TN" or next_score == "FN":
                    if prev_score == "TN" or prev_score == "FN":
                        segs[i]["err"] = "I"
                    elif prev_score == "TP":
                        segs[i]["err"] = "Oe"
                    else:
                        warn("Unhandled error case: %s %s %s" % (prev_score, score, next_score))
                else:
                    warn("Unhandled error case: %s followed by %s" % (score, next_score))

            elif score == "FN":

                if next_score == "TP":
                    if prev_score == "TP":
                        segs[i]["err"] = "F"
                    elif prev_score == "TN" or prev_score == "FP":
                        segs[i]["err"] = "Us"
                    else:
                        warn("Unhandled error case: %s %s %s" % (prev_score, score, next_score))

                elif next_score == "TN" or next_score == "FP":
                    if prev_score == "TN" or prev_score == "FP":
                        segs[i]["err"] = "D"
                    elif prev_score == "TP":
                        segs[i]["err"] = "Ue"
                    else:
                        warn("Unhandled error case: %s %s %s" % (prev_score, score, next_score))

            else:
                raise warn("Unknown score: %s" % score)

    return segs

# Event types for Actual Events (ground truth) and Returned Events (detected)
EVENT_DELETION = "D"
FRAGMENTED_EVENT = "F"
MERGED_EVENT = "M"
FRAGMENTED_AND_MERGED = "FM"

INSERTION_RETURN = "I'"
MERGING_RETURN = "M'"
FRAGMENTING_RETURN = "F'"
FRAGMENTING_AND_MERGING = "FM'"

CORRECT = "C"

def score_events(truths, detected, segs):
    """score truth and detected events.
    returns dict of truth, detected, and stats
    """

    #1st pass, so-called 'trivial' assignments from segments
    for d in truths+detected:
        for seg in segs:
            if time_overlap(d, seg):
                if seg.get("err") == "D":
                    d["event_score"] = EVENT_DELETION
                elif seg.get("err") == "F":
                    d["event_score"] = FRAGMENTED_EVENT
                elif seg.get("err") == "I":
                    d["event_score"] = INSERTION_RETURN
                elif seg.get("err") == "M":                    
                    d["event_score"] = MERGING_RETURN

    #2nd pass, overlaps between scored events
    for d in detected:
        for t in truths:
            if time_overlap(d, t):
                if d.get("event_score") == MERGING_RETURN:
                    if t.get("event_score") == FRAGMENTED_EVENT:
                        t["event_score"] = FRAGMENTED_AND_MERGED
                    else:
                        t["event_score"] = MERGED_EVENT

                if t.get("event_score") == FRAGMENTED_EVENT:
                    if d.get("event_score") == MERGING_RETURN:
                        d["event_score"] = FRAGMENTING_AND_MERGING
                    else:
                        d["event_score"] = FRAGMENTING_RETURN
                        
    #3rd pass, anything so far unscored is then Correct
    for d in detected+truths:
        if not d.get("event_score"):
            d["event_score"] = CORRECT
                        
    #count up the scores
    d_counts = {CORRECT:0,
                FRAGMENTING_RETURN:0,
                MERGING_RETURN:0,
                FRAGMENTING_AND_MERGING:0,                 
                INSERTION_RETURN:0}

    t_counts = {CORRECT:0,
                EVENT_DELETION:0,
                FRAGMENTED_EVENT:0,
                FRAGMENTED_AND_MERGED:0,
                MERGED_EVENT:0}

    for d in detected:
        d_counts[d.get("event_score")] += 1

    for v in truths:
        t_counts[v.get("event_score")] += 1

    return dict(truths=truths, detected=detected, d_counts=d_counts, t_counts=t_counts, d_rates=pct_dict(d_counts), t_rates=pct_dict(t_counts))

DEFAULT_WINDOW_WIDTH=3

def sliding_window(seq, n=DEFAULT_WINDOW_WIDTH):
    """returns iterator over sliding window (of width n) over data from the sequence `seq`
    s -> (s0,s1,...s[n-1]), (s1,s2,...,sn), ...                   
    """
    it = iter(seq)
    result = tuple(islice(it, n))
    if len(result) == n:
        yield result    
    for elem in it:
        result = result[1:] + (elem,)
        yield result

def pct_dict(d):
    #take int count values of dict d and return dict of each rate
    n = sum(d.itervalues())
    r = {}
    for k, v in d.iteritems():
        if n == 0:
            r[k] = None
        else:
            r[k] = d[k]*1.0/n
    return r

def warn(msg):
    print "WARNING:", msg

def time_overlap(d1, d2):
    """return True if the t1, t2 in d1 overlap t1, t2 in d2."""
    gt1, gt2, vt1, vt2 = parse_date(d1["t1"]), parse_date(d1["t2"]), parse_date(d2["t1"]), parse_date(d2["t2"])
    return (gt1 != vt2) and (vt1 != gt2) and (gt1 <= vt2) and (vt1 <= gt2) 


def score_aggregate(results):
    """compute aggregate scores and stats from list of detection results"""
    scores = []
    truth_count = detected_count = segment_count = 0

    for res in results:
        scores.append(res["scores"])
        truth_count += len(res["labels"])
        detected_count += len(res["detected"])
        segment_count += len(res["scores"]["segments"])

    ret = dict()
    ret["scores"] = sum_scores(scores)
    ret["stats"] = dict(truth_count=truth_count, detected_count=detected_count, segment_count=segment_count)
    return ret
    

def sum_scores(scores):
    """sum up the scores"""
    segs = itertools.chain(*[x["segments"][:] for x in scores]) #all the segs in flat list
    d_counts = sum_dicts([x["events"]["d_counts"] for x in scores])
    t_counts = sum_dicts([x["events"]["t_counts"] for x in scores])
    d_rates = pct_dict(d_counts)
    t_rates = pct_dict(t_counts)
    return dict(frame_scores=score_frames(segs), event_scores=dict(d_counts=d_counts, t_counts=t_counts, d_rates=d_rates, t_rates=t_rates))

def sum_dicts(l):
    """sum dict vals in list l"""
    r = defaultdict(int)
    for d in l:
        for k, v in d.iteritems():
            r[k] += v
    return r

def update_scores_list(list_file, score_file):
    """update list of score files"""
    fnames = []
    head, tail = os.path.split(score_file)
    if os.path.exists(list_file):
        with open(list_file, "r") as f:
            fnames = json.loads(f.read())
            if tail not in fnames:
                fnames.append(tail)
            fnames.sort()
            fnames.reverse()
    else:
        fnames.append(tail)

    with open(list_file, "w") as f:
        print "writing %s..." % list_file
        f.write(json.dumps(fnames))

    







import json

import sys
sys.path.append("..")

from perfboard import AbstractRecognizer

class DummyWalkingDetector(AbstractRecognizer):
    """always return the walking results from the example output"""
    def __init__(self):
        self.label = "WALKING"

    def process(self, chunk):
        pass

    def results(self, errors=True):
        with open("test/example_result.json") as f:
            res = json.loads(f.read())["detected"]
            return [r for r in res if r["label"] == "WALKING" ]

class DummyRunningDetector(AbstractRecognizer):
    """always return the running results from the example output"""
    def __init__(self):
        self.label = "RUNNING"

    def process(self, chunk):
        pass

    def results(self, errors=True):
        with open("test/example_result.json") as f:
            res = json.loads(f.read())["detected"]
            return [r for r in res if r["label"] == "RUNNING" ]

class DummyStandingDetector(AbstractRecognizer):
    """always return the standing results from the example output"""
    def __init__(self):
        self.label = "STANDING"

    def process(self, chunk):
        pass

    def results(self, errors=True):
        with open("test/example_result.json") as f:
            res = json.loads(f.read())["detected"]
            return [r for r in res if r["label"] == "STANDING" ]


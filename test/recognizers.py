
import json

import sys
sys.path.append("..")

from recog import AbstractRecognizer

""" These are some dummy recognizers that are used to test the system"""

class DummyWalkingDetector(AbstractRecognizer):
    """always return the walking results from the example output"""
    def labels_supported(self):
        return ["WALKING"]

    def process(self, chunk):
        pass

    def get_results(self, errors=True):
        with open("test/example_result.json") as f:
            res = json.loads(f.read())
            return [r for r in res if r["label"] == "WALKING" ]

    def reset(self):
        pass

class DummyRunningDetector(AbstractRecognizer):
    """always return the running results from the example output"""
    def labels_supported(self):
        return ["RUNNING"]

    def process(self, chunk):
        pass

    def get_results(self, errors=True):
        with open("test/example_result.json") as f:
            res = json.loads(f.read())
            return [r for r in res if r["label"] == "RUNNING" ]

    def reset(self):
        pass

class DummyStandingDetector(AbstractRecognizer):
    """always return the standing results from the example output"""
    def labels_supported(self):
        return ["STANDING"]

    def process(self, chunk):
        pass

    def get_results(self, errors=True):
        with open("test/example_result.json") as f:
            res = json.loads(f.read())
            return [r for r in res if r["label"] == "STANDING" ]

    def reset(self):
        pass


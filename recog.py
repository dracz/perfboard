
class AbstractRecognizer( object ):
    """Defines a simple, generic recognizer interface."""

    def train(self, recs, labels):
        """train the recognizer with the `recs` and ground truth `labels`""" 
        raise NotImplementedError()
        
    def test(self, recs):
        """process raw data records and update internal state. `recs` is an iterable."""
        raise NotImplementedError()

    def process(self, recs):
        """process raw data records and update internal state. `recs` is an iterable."""
        self.test(recs)


    def get_results(self, time_range=None):
        """return ordered list of recognition results of the form `[{"t1":datetime, "t2":datetime, "label":str}, ...]`
        `time_range`, if present is a 2-tuple of datetime objects that restrict the result set to items with timestamps within, or overlapping, the range.
        """
        raise NotImplementedError()


    def labels_supported(self):
        """returns a list of labels that this recognizer supports (generates). 
        This is used by the framework to determine how to score the recognizers given some arbitrary labeled ground truth data.
        """
        raise NotImplementedError()


    def reset(self):
        """reset all the state of the recognizer. 
        this is called between test cases to prevent side effects"""
        raise NotImplementedError()        


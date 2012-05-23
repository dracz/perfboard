<link rel="stylesheet" type="text/css" href="markdown.css" />
<!-- To generate the html from this markdown file: perl ~/Markdown.pl --html4tags README.md > static/README.html -->

# perfboard
A performance metrics dashboard for continuous context recognition systems

## Background
This project provides a framework for the evaluation and visualization of continuous context-recognition systems. We are investigating systems for automatic detection of visits, paths, and activities from mobile sensor data, and develop these tools to help evaluate the feasibility and quality of various approaches.

## Overview
This section provides an overview of a continuous context recognition systems development life-cycle and how this framework fits in.

1. **Ground truth collection** - Ground truth corpora consist of [raw data][] files, typically collected from sensors carried or worn by a subject, and [ground truth][] labels provided by researchers, subjects, click workers, or other observers, over intervals of the data. The labels provide the *truth* about what the user was doing during the labeled interval, and are required for development and evaluation of most classification/detection/recognition systems.

2. **Recognizer development** - The raw data and associated ground truth labels collected in the previous step help in various aspects of the development, training, and testing various components of recognition system pipelines. Here we mainly focus on [binary classification](http://en.wikipedia.org/wiki/Binary_classification) and define an abstract [recognizer interface][] that allows recognizers to be plugged in.

3. **Evaluation** - Now with the data and framework, we can feed [raw data][] from selected [ground truth][] cases to various activity recognizers that implement the [recognizer interface][], compare the detection results to the ground truth labels, log the [test results][], and finally, compute and render detailed performance metrics. [[1](#ref1)]

4. **Iteration** - Based on the performance results, we may return to step 2 and tweak parameters, modify code, try something new, or to step 1 to scale-up the testing, gather more test data, etc, and improve performance. Once the performance of a recognizer is above the desired level for a diverse data set, we can be more confident in the feasibility of the approach.

## Running Performance Tests
The `perfboard` command line utility can be used to test the performance for one or more classifiers using a set of labeled [ground truth][] data. The tool can instantiate one or more recognizers, read a set of ground truth files, feed raw data from the ground truths to the recognizers, retrieve the results from the recognizers, and finally compute and render performance metrics. Usage:

    perfboard.py [-h] [--outpath OUTPUT_PATH] --recognizers RECOGNIZER_LIST
	                    TRUTH_FILE [TRUTH_FILE ...]

For example, to test 3 different recognizers using the `example_truth.json` case, and write the final scored results to `static/scores.json`:

    ./perfboard.py --recognizers=test.recognizers.DummyWalkingDetector,test.recognizers.DummyRunningDetector,test.recognizers.DummyStandingDetector 
	               --outpath=static/scores.json  test/example_truth.json

Results written to  `static/scores.json` are picked up by the performance dashboard which can be accessed by running a web server serving `perfboard/static` dir, then browsing to that location, ie:

    http://localhost/perfboard/


<a id="raw_data"/>
## Raw Data
Raw data files contain raw sensor and/or behavioral data, for example accelerometer continuously logged from the mobile device of a subject while the subject performs some sequence predefined activities. Raw data can be collected in any format, be we present a generic record structure here for various kinds of mobile data.

    coming...

<a id="ground_truth"/>
## Ground Truth
Ground truth files encode labels containing the precise start and end times of activities performed by the user, as well as references to the [raw data][] that corresponds to the activities. The ground truth label files are json encoded in [json][] and have the following form:

    {
	"data_path": "raw_data/device1_20120516", 
	"t1": "2012-05-16T09:00:00-08:00", 
	"t2": "2012-05-16T09:20:00-08:00",
	"description": "Activity recognition data collection with subject DR on morning of 5/16/2012", 
	"device": "Nokia C7-00", 
	"hw": "353755043225509", 
	"sw": "qt-hubris-client-v0.0.3", 
	"subject": {
	    "bday": "08/22/1975", 
	    "gender": "male", 
	    "handedness": "RIGHT", 
	    "height": "183cm", 
	    "id": "DR", 
	    "weight": "165lbs"
	}, 
	"labels": [
	    {
		"body_position": "RIGHT_FRONT_POCKET",
		"t1": "2012-05-16T09:00:00-08:00", 
		"t2": "2012-05-20T09:05:00-08:00", 
		"label": "STANDING"
	    }, 
	    {
		"body_position": "RIGHT_FRONT_POCKET",
		"t1": "2012-05-16T09:05:00-08:00", 
		"t2": "2012-05-20T09:15:00-08:00", 
		"label": "WALKING"
	    }, 
	    {
		"body_position": "RIGHT_HAND",
		"t1": "2012-05-16T09:15:00-08:00", 
		"t2": "2012-05-20T09:15:30-08:00", 
		"label": "STANDING"
	    }, 
	    {
	        "body_position": "RIGHT_BACK_POCKET",
		"t1": "2012-05-16T09:15:30-08:00", 
		"t2": "2012-05-20T09:18:30-08:00", 
		"label": "RUNNING"
	    }, 
	    {
		"body_position": "RIGHT_HAND",
		"t1": "2012-05-16T09:18:30-08:00", 
		"t2": "2012-05-20T09:20:00-08:00", 
		"label": "STANDING"
	    }
	], 
    }

<a id="recognizer_interface"/>
## Recognizer Interface
Recognizers process time-ordered chunks of [raw data][] and produce sets of [recognizer results][]. The `perfboard.AbstractRecognizer` [python][] class is shown here: 

	class AbstractRecognizer( object ):
		"""Defines a generic recognizer interface. Override `process` and `results`. 
		Set `self.labels_recognized` to specify the labels this recognizer can produce
		"""
		def __init__(self):
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


<a id="recognizer_results"/>
## Recognizer results
Recognizers output labeled time intervals of the form:

    [
        {
            "label": "STANDING", 
            "t1": "2012-05-16T09:00:00-08:00", 
            "t2": "2012-05-20T09:05:00-08:00"
        }, 
        {
            "label": "WALKING", 
            "t1": "2012-05-16T09:05:00-08:00", 
            "t2": "2012-05-20T09:15:00-08:00"
        }, 
        {
            "label": "STANDING", 
            "t1": "2012-05-16T09:15:00-08:00", 
            "t2": "2012-05-20T09:15:30-08:00"
        }, 
        {
            "label": "RUNNING", 
            "t1": "2012-05-16T09:15:30-08:00", 
            "t2": "2012-05-20T09:18:30-08:00"
        }, 
        {
            "label": "STANDING", 
            "t1": "2012-05-16T09:18:30-08:00", 
            "t2": "2012-05-20T09:20:00-08:00"
        }
    ]

<a id="test_results">
##Test Results
The [recognizer results][] are combined with the [ground truth][] items to encode the test results output. Results for the above example would be:

    {
        "description": "Activity recognition data collection with subject DR on morning of 5/16/2012", 
        "device": "Nokia C7-00", 
        "sw": "qt-hubris-client-v0.0.3", 
        "data_path": "raw_data/device1_20120516", 
        "t1": "2012-05-16T09:00:00-08:00"
        "t2": "2012-05-16T09:20:00-08:00", 
        "hw": "353755043225509", 
        "subject": {
            "weight": "165lbs", 
            "bday": "08/22/1975", 
            "gender": "male", 
            "handedness": "RIGHT", 
            "height": "183cm", 
            "id": "DR"
        }, 
        "labels": [
            {
                "t1": "2012-05-16T09:00:00-08:00", 
                "t2": "2012-05-20T09:05:00-08:00", 
                "label": "STANDING", 
                "body_position": "RIGHT_FRONT_POCKET"
            }, 
            {
                "t1": "2012-05-16T09:05:00-08:00", 
                "t2": "2012-05-20T09:15:00-08:00", 
                "label": "WALKING", 
                "body_position": "RIGHT_FRONT_POCKET"
            }, 
            {
                "t1": "2012-05-16T09:15:00-08:00", 
                "t2": "2012-05-20T09:15:30-08:00", 
                "label": "STANDING", 
                "body_position": "RIGHT_HAND"
            }, 
            {
                "t1": "2012-05-16T09:15:30-08:00", 
                "t2": "2012-05-20T09:18:30-08:00", 
                "label": "RUNNING", 
                "body_position": "RIGHT_BACK_POCKET"
            }, 
            {
                "t1": "2012-05-16T09:18:30-08:00", 
                "t2": "2012-05-20T09:20:00-08:00", 
                "label": "STANDING", 
                "body_position": "RIGHT_HAND"
            }
        ], 
        "results": [
            {
                "t1": "2012-05-16T09:00:00-08:00", 
                "t2": "2012-05-20T09:05:00-08:00", 
                "label": "STANDING"
            }, 
            {
                "t1": "2012-05-16T09:05:00-08:00", 
                "t2": "2012-05-20T09:15:00-08:00", 
                "label": "WALKING"
            }, 
            {
                "t1": "2012-05-16T09:15:00-08:00", 
                "t2": "2012-05-20T09:15:30-08:00", 
                "label": "STANDING"
            }, 
            {
                "t1": "2012-05-16T09:15:30-08:00", 
                "t2": "2012-05-20T09:18:30-08:00", 
                "label": "RUNNING"
            }, 
            {
                "t1": "2012-05-16T09:18:30-08:00", 
                "t2": "2012-05-20T09:20:00-08:00", 
                "label": "STANDING"
            }
        ], 
    }


[raw data]: #raw_data 
[ground truth]: #ground_truth
[recognizer interface]: #recognizer_interface
[recognizer results]: #recognizer_results
[test results]: #test_results
[json]: http://www.json.org/
[python]: http://python.org

## References
<a name="ref1"/>
[1] Ward, J. A., Lukowicz, P., & Gellersen, H. W. (2011). Performance metrics for activity recognition. ACM Transactions on Intelligent Systems and Technology (TIST), 2(1), 1-23. doi:10.1145/1889681.1889687. [PDF](http://gtubicomp.pbworks.com/w/file/fetch/48480476/Ward2011-Performance%20metrics%20for%20activity%20recognition.pdf)

# perfboard
A performance metrics dashboard for continuous context recognition systems

<link rel="stylesheet" type="text/css" href="markdown.css"></link>
<script src="http://code.jquery.com/jquery.min.js"></script>
<script src="http://d3js.org/d3.v2.js"></script>
<script src="util.js" type="text/javascript"></script>
<!-- To generate the html from this markdown file: perl ~/Markdown.pl --html4tags README.md > static/README.html -->

## Background
This project provides a framework for the evaluation and visualization of continuous context-recognition systems. We are investigating systems for automatic detection of visits, paths, and activities from mobile sensor data, and developed this system to help evaluate the feasibility and quality of various approaches.

## Overview
This section provides an overview of a typical development life-cycle for continuous context recognition systems and explains how this framework fits in.

1. **Ground truth collection** - Ground truth corpora consist of [raw data][] files, typically collected from sensors carried or worn by a subject, and [ground truth][] labels provided by researchers, subjects, click workers, or other observers, over intervals of the data. The labels provide the *truth* about what the user (or device) was doing during the labeled interval, and are useful for the development and evaluation of sytems for classification, detection, or recognition.

2. **Recognizer development** - The raw data and associated ground truth labels are required for training and testing of various components in a recognition system pipeline. Here we mainly focus on [binary classification](http://en.wikipedia.org/wiki/Binary_classification) and define an abstract [recognizer interface][] that allows user-defined classifiers to be plugged in to the system.

3. **Evaluation** - Now, using this framework we can feed [raw data][] from selected [ground truth][] cases to one or more recognizers that implement the [recognizer interface][] and analyze the returned results. Results from each recognizer are compared with the labels from each ground truth case, and both individual and aggregate [test results][] are computed and logged. Finally, detailed [performance metrics](#metrics) are rendered for further inspection. 

4. **Iteration** - Based on the performance results, we may return to step 2 and tweak parameters, modify code, try something new, etc. Alternatively, we can return to step 1 to gather more test data and scale up the testing. Once the performance of a recognizer is above the desired level for a diverse data set, we can be more confident in the feasibility of the approach, and begin to move toward productization.

## Running Performance Tests
The `perfboard` command line utility can be used to test the performance for one or more classifiers using a set of labeled [ground truth][] data. The tool can read a set of ground truth input files, instantiate one or more specified recognizers, feed raw data from the ground truths to the recognizers, retrieve the results from the recognizers, and finally compute and render performance metrics. Usage:

    perfboard.py [-h] [--outpath OUTPUT_PATH] --recognizers RECOGNIZER_LIST
	                    TRUTH_FILE [TRUTH_FILE ...]

For example, to test the `test.recognizers.DummyWalkingDetector` against the `example_truth.json` test case:

    ./perfboard.py --recognizers=test.recognizers.DummyWalkingDetector test/example_truth.json

By default, result objects are written to `static/scores.json` and then can be picked up from that location by the performance dashboard. The dashboard can be accessed by running a web server and serving the `perfboard/static` dir.


<a id="raw_data"></a>
## Raw Data
Raw data files contain raw sensor and/or behavioral data, for example accelerometer continuously logged from the mobile device of a subject while the subject performs some sequence predefined activities. Raw data can be collected in any format, but we present a generic record structure here for various kinds of mobile data.

    record description coming soon...

<a id="ground_truth"></a>
## Ground Truth
Ground truth files encode labels containing the precise start and end times of activities performed by the user, as well as references to the [raw data][] that corresponds to the activities. The ground truth label files are json encoded in [json][] and have the following form:

<pre><code class="jsontxt" id="truth_example"></code></pre>
<script>d3.json("example_truth.json", function(json) {$("#truth_example").html(syntaxHighlight(json));});</script>

<a id="recognizer_interface"></a>
## Recognizer Interface
Recognizers process time-ordered chunks of [raw data][] and return detection results. The `perfboard.AbstractRecognizer` [python][] class is shown here: 

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


<a id="test_results"></a>
## Test Results
The final test results are encoded in a object that combines all [ground truth][] items, [recognizer results][], and performance metrics. Results for the above example, might look like:

<pre><code class="jsontxt" id="scores_example"></code></pre>
<script>d3.json("example_scores.json", function(json) {$("#scores_example").html(syntaxHighlight(json));});</script>

<a name="metrics"></a>
## Performance Metrics
The metrics used here are based on <span class="bibref">[[1](#ref1)]</span>. For each ground truth, raw data is fed to each recognizer and result detail is generated.

[raw data]: #raw_data 
[ground truth]: #ground_truth
[recognizer interface]: #recognizer_interface
[test results]: #test_results
[json]: http://www.json.org/
[python]: http://python.org

## References
<a name="ref1"></a>
<span class="bibref">[1]</span> Ward, J. A., Lukowicz, P., & Gellersen, H. W. (2011). Performance metrics for activity recognition. ACM Transactions on Intelligent Systems and Technology (TIST), 2(1), 1-23. doi:10.1145/1889681.1889687. [PDF](http://gtubicomp.pbworks.com/w/file/fetch/48480476/Ward2011-Performance%20metrics%20for%20activity%20recognition.pdf)

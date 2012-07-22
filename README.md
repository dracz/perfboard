# perfboard
A performance metrics dashboard for continuous context recognition systems

<link rel="stylesheet" type="text/css" href="markdown.css"></link>
<script src="http://code.jquery.com/jquery.min.js"></script>
<script src="http://d3js.org/d3.v2.js"></script>
<script src="util.js" type="text/javascript"></script>

<link href="prettify/prettify.css" type="text/css" rel="stylesheet" />
<script type="text/javascript" src="prettify/prettify.js"></script>
<script type="text/javascript">$(document).ready(function() {prettyPrint()});</script>

<!-- To generate the html from this markdown file: perl ~/Markdown.pl --html4tags README.md > static/README.html -->

## Background
We've been investigating systems for automated recognition of visits, paths, and activities from mobile sensor data, and have developed these tools to help evaluate the feasibility and quality of various approaches. This project provides a framework for: 1) defining ground truth data, 2) interfacing with context recognizers, 2) feeding data from test cases to context recognizer(s), and 3) scoring and visualizing recognizer performance <span class='bibref'>[[1](#ref1)]</span>.

## Overview
This section provides an overview of a typical development process for a continuous context recognition system and explains how this framework can fit in. Here we define a continuous context recognition system as one that continually infers context (of user/device) from raw data streams (from user/device). Recognizers consume raw time series data (from sensors and events) and produce labels over time intervals (with some confidence). The labels encode the context of the user/device over various time interval, for example: _HOME_, _WORK_, _RUNNING_, _WALKING_, _BIKING_, _DRIVING_. 

1. **Ground truth collection** - We start with the collection of ground truth corpora consisting of [raw data][] files, typically collected from sensors carried or worn by a subject, and [ground truth][] labels provided by researchers, subjects, click workers, or other observers, over intervals of the data. The labels provide the *truth* about what the user (or device) was doing during the labeled interval, and are essential for the development and evaluation of systems for classification, detection, or recognition.

2. **Recognizer development** - Now that we have some raw data and ground truth, we begin developing our recognition system. Here, we mainly focus on [binary classification](http://en.wikipedia.org/wiki/Binary_classification), and try to build and test various recognizers that can infer the context of the user from some raw data streams. We implement the abstract [recognizer interface][] that allows user-defined classifiers to be plugged in to the test framework.

3. **Evaluation** - Once we have candidate recognizers ready for testing, we feed [raw data][] from [ground truth][] cases to specified recognizers (implementing the [recognizer interface][]) and analyze the returned results. The recognizer results are compared with the ground truth labels and detailed [performance metrics](#metrics) are computed, [test results][] are logged, and visualizations are rendered for inspection.

4. **Iteration** - Based on the performance results, we may return to step 2 and tweak parameters, modify code, try something new, etc. Alternatively, we can return to step 1 to gather more labeled data to scale up the testing. Once the performance of a recognizer is above the desired level for a diverse data set, we can be more confident in the feasibility of the approach and begin to move toward productization.

## Dependencies
- [python][] 2.7 
- [iso8601.py][http://pypi.python.org/pypi/iso8601/] $ pip install iso8601


<a id="raw_data"></a>
## Raw Data
Raw data files contain timestamped sensor and/or behavioral data logged (continuously or periodically) from one or more devices associated with a test subject. Raw data often come from mobile phone sensors like WLAN, GSM, GPS, magnetometer, Bluetooth, ambient light, microphone, etc, but may also come from other sensors in the environment or worn on the body, or from external data sources. Raw data records are encoded in an application specific manner and should only be passed to recognizers that understand the format.

<a id="ground_truth"></a>
## Ground Truth
Ground truth files encode labels containing the precise start and end times of specific activities performed by the user during the raw data collection. The ground truth label files are encoded in [json][] and have the following form:

<pre><code id="truth_example"></code></pre>
<script>d3.json("example_truth.json", function(json) {$("#truth_example").html(syntaxHighlight(json));});</script>

The following table describes the various fields of ground truth items:

- `data_path` - glob expression specifying [raw data][] files for this case
- `description` - description of test case (optional)
- `sw` - client software identifier
- `t1` - earliest t1 of data record, label, or detected
- `t2` - latest t2 for data record, label, or detected
- `hw` - hardware identifier
- `device` - device model (optional)
- `subject` - infomartion about the human test subject
- `labels` - list of labeled intervals over the raw data. Labels contain the following fields:
  - `t1` - [isotime][] timestamp of label start
  - `t2` - [isotime][] timestamp of label end
  - `label` - String constant defining the ground truth label
  - `body_position` - String constant identifying the where the device was carried on the body

How ground truth labels are initially captured is out of the scope of this document, but there are various approaches such as self-reported, hand-written user diaries, mobile phone-based labeling tools, crowdsourced labeling, and of course, following subjects around with clipboards.

<a id="recognizer_interface"></a>
## Recognizer Interface
Recognizers process time-ordered chunks of [raw data][] records and return lists of [recognizer results](#recognizer_results). Recognizers MUST implement the `perfboard.AbstractRecognizer` interface to be compatible with this framework. The `perfboard.AbstractRecognizer` [python][] class is shown here: 

<pre><code class="prettyprint lang-py">class AbstractRecognizer( object ):
	"""Defines a simple generic recognizer interface."""
	def process(self, data):
		"""process raw data records and update internal state."""
		raise NotImplementedError()

	def get_results(self, time_range=None):
		"""return ordered list of recognition results of the form `[{"t1":<datetime_start>, "t2":<datetime_end>, "label":<string>}, ...]`
		`time_range`, if present is a 2-tuple of datetime objects that restrict the result set to items with timestamps within, or overlapping, the range.
		"""
		raise NotImplementedError()

	def labels_supported(self):
		"""returns a list of labels that this recognizer supports (generates). 
		This is used by the framework to determine how to score the recognizers given some arbitrary labeled ground truth data.
		"""
		raise NotImplementedError()
</code></pre>

Raw data are fed to a recognizer using the `process()` method. Results are retrieved using the `get_results()` method and example is shown in [recognizer results](#recognizer_results). The `labels_supported()` method is used to filter the [ground truth][] labels to include only those supported by the specified recognizer before the results are compared.

<a name="recognizer_results"></a>
## Recognizer results

The `get_results()` method returns lists of dictionaries containing the labeled time intervals. For example, recognizer results have the following form (after json-encoding):

<pre><code id="results_example"></code></pre>
<script>d3.json("example_result.json", function(json) {$("#results_example").html(syntaxHighlight(json));});</script>


<a name="cmdline"></a>
## Running Performance Tests
A test run typically contains the following steps:

1. Read ground truth input file(s)
2. Instantiate specified recognizers
3. Feed raw data from each ground truth file to each recognizer
4. Retrieve results from the recognizers
5. Compute and render [performance metrics](#metrics)

The `perfboard` command line utility is used to run performance tests.

    perfboard.py [-h] [--outpath OUTPUT_PATH] [--norotate] --recognizers RECOGNIZERS TRUTH_FILE [TRUTH_FILE ...]

For example, to test the `test.recognizers.DummyWalkingDetector` against the `example_truth.json` test case:

    ./perfboard.py --recognizers=test.recognizers.DummyWalkingDetector test/example_truth.json

By default, result objects are written to `static/scores.json` and can then be retrieved by the [performance dashboard](#dashboard) via ajax. 

Existing scores file are copied to timestamped filenames before new results are written and a list of scores history is updated in the `static/scores_list.json` file. The dashboard reads the scores list and presents it in a pulldown menu. To disable the rotation of scores to timestamped files use the `--norotate` option.

To run the example tests conveniently, use:

    test/test.sh

<a id="test_results"></a>
## Test Results
Final test results are encoded in a object that combines all [ground truth][] items, results from recognizer `get_results()`, and all performance metrics. For example, test results from the above example might look like the following:

<pre><code id="scores_example"></code></pre>
<script>d3.json("example_scores.json", function(json) {$("#scores_example").html(syntaxHighlight(json));});</script>

The result object has the following fields:

- `t` is the timestamp of the test run in [isotime][]
- `stats` is dictionary of total number of ground truths `truth_count`, recognizer results `detected_count`, and scored segments `segment_count` from all test cases
- `results` is list of the scored test case results. Each result object has the same form as a [ground truth][] item, with additional keys: 
  - `detected` list of recognizer results for the test
  - `scores` contains the event and frame scores for the test
  - `recognizer` field specifying which recognizer was used in the test
  - items in `labels` and `detected` now have `event_score` field containing the [event score](#event_score)
- `recognizers` is list of recognizers that were used in the test
- `scores` is dictionary of aggregate scores from all ground truth cases combined. 

<a name="dashboard"></a>
## Dashboard
The dashboard can be accessed by running a web server and serving the `perfboard/static` dir and visiting the `index.html` file there.

*Note:* The dashboard won't work when served using `file://` url rather than `http://` url (for ajax security reasons).

The top of the dashboard shows an overview of results from all the test cases in a test run:

<img src="dashboard_top.png"/>

The overview shows the test time, total number of ground truth cases, total number of ground truth labels, total number of detected output, and overall stats of frame and event scores. Frame scores report whether individual units of time (seconds) match the ground truth. _Positive frames_ are those where we have a ground truth prediction for the frame, _negative frames_ are those where there is no ground truth label (null-class). Overview statistics and pie charts for _positive frames_, _negative frames_, _ground truth events_, and _detected events_ show the rates of the various kinds of errors.

The top bar also provides a pull-down selector to jump to individual test results, and another pull-down selector for rendering other result sets.

Each ground truth case in a result set is rendered in a result detail panel similar to that shown here:

<img src="dashboard_case_detail.png"/>

The result detail shows similar statistics and pie charts for _positive frames_, _negative frames_, _ground truth events_, and _detected events_, but also includes a time interval diagram and event analysis diagram. The time-interval diagram shows the truth, detection, and segment time intervals and corresponding scores. Hovering over the intervals will show the timing, labels, and scores. The event analysis diagrams shows the truth and detected event scores in a single chart.

<a name="metrics"></a>
## Performance Metrics
The metrics used in [test results][] are based on <span class="bibref">[[1](#ref1)]</span>. This section briefly describes some of the metrics.

<a name="event_score"></a>
**Event Scores**

Event scores are assigned to [ground truth][] labels and also to [recognizer results](#recognizer_results). This table provides summary of score types described in <span class="bibref">[[1](#ref1)]</span>: 

- `D` - Deletion
- `F` - Fragmented
- `M` - Merged
- `FM` - Fragmented and merged
- `C` - Correct
- `I` - Insertion
- `F'` - Fragmenting return
- `M'` - Merging return
- `FM'` - Fragmenting and merging return

<a name="segment_score"></a>
**Segment Scores**

Scores are also assigned to segments as described in <span class="bibref">[[1](#ref1)]</span>. Segments are scored with one of the following four types:

- `TP` - True Positive
- `TN` - True negative
- `FP` - False Positive
- `FN` - False Negative

For `FP` and `FN` segments, an error type field `error` is also present with one of the following eight error types:

- `Us` - Underflow start
- `Ue` - Underflow end
- `Os` - Overflow start
- `Oe` - Overflow end
- `F`  - Fragmenting
- `M`  - Merging
- `I`  - Insertion
- `D`  - Deletion

[raw data]: #raw_data 
[ground truth]: #ground_truth
[recognizer interface]: #recognizer_interface
[test results]: #test_results
[json]: http://www.json.org/
[python]: http://python.org
[isotime]: http://en.wikipedia.org/wiki/ISO_8601

## References
<a name="ref1"></a>
<span class="bibref">[1]</span> Ward, J. A., Lukowicz, P., & Gellersen, H. W. (2011). Performance metrics for activity recognition. ACM Transactions on Intelligent Systems and Technology (TIST), 2(1), 1-23. doi:10.1145/1889681.1889687. [PDF](http://gtubicomp.pbworks.com/w/file/fetch/48480476/Ward2011-Performance%20metrics%20for%20activity%20recognition.pdf)

## Powered by
This project is based o
<br/>

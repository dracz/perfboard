./perfboard.py --recognizers=test.recognizers.DummyWalkingDetector test/example_truth.json
./perfboard.py --recognizers=test.recognizers.DummyStandingDetector test/example_truth.json
./perfboard.py --recognizers=test.recognizers.DummyRunningDetector test/example_truth.json
./perfboard.py --recognizers=test.recognizers.DummyStandingDetector,test.recognizers.DummyRunningDetector,test.recognizers.DummyWalkingDetector test/example_truth.json

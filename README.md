# codex_study_logs

Repo for all the logs 

## fuzzing dir

This directory contains the script to parse all the logs in the repo subdir

In general you would call

`./fuzzer_collect_results.sh` which will use `fuzzer_parse_errors.py`


You might also wanna call: 

`fuzzer_collect_all_functs.py`

This script will go over all the results and collect all the functions that were 
called in the tests.  It will then print out a CSV file with the following columns:
1. Function name
2. Number of times the function was implemented correctly
3. The uuid of the students that correctly implemented the function


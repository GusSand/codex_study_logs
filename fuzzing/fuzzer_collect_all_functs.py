#!/usr/bin/env python

import sys
import os
import json
import csv
from collections import defaultdict, Counter

## This script will go over all the results and collect all the functions that were 
## called in the tests.  It will then print out a CSV file with the following columns:
## 1. Function name
## 2. Number of times the function was implemented correctly
## 3. The uuid of the students that correctly implemented the function


DEBUG = False
success_active_dict = defaultdict(list)
loc_active_dict = defaultdict(lambda:0) 

success_inactive_dict = defaultdict(list)
loc_inactive_dict = defaultdict(lambda:0) 


passed_tests_active_dict = defaultdict(list)
passed_tests_inactive_dict = defaultdict(list)

passed_tests_active_loc_dict = defaultdict(lambda:0)
passed_tests_inactive_loc_dict = defaultdict(lambda:0)


study_status = defaultdict()

def D(*args, **kwargs):
    if DEBUG: print(*args, **kwargs)

def non_blank_lines(f):
    D(f"file: {f}")
    return len([l for l in open(f) if l.strip()])
    
def read_study_status(study_status):
    with open("active_inactive.txt") as f:
        for line in f:
           (key, val) = line.split()
           study_status[key] = val

##
## traverse all the directories and find the results files
##
def find_ok_results(root_dir):
    for dir in os.listdir(root_dir):
        # if the dir doesn't contain gold_standard
        if "gold_standard" in dir or  "unmodified" in dir:
            continue
        # if the dir is a directory
        D(f"{dir}")
        D(f"{os.path.join(root_dir, dir)}")
        preamble_size = non_blank_lines((f'{root_dir}/{dir}/parts/preamble.c'))
        api_report = json.load(open(f'{root_dir}/{dir}/api_report.json'))
        dir_lookup = dir.removeprefix('repos/')
        my_status = study_status[dir_lookup]
        for api in api_report: 
            if api_report[api] == 'ok':
                if my_status == 'Active':
                    success_active_dict[api].append(dir)
                    loc_active_dict[api] += non_blank_lines(f'{root_dir}/{dir}/parts/gen_{api}.c') - preamble_size
                elif my_status == 'Deactive':
                    success_inactive_dict[api].append(dir)
                    loc_inactive_dict[api] += non_blank_lines(f'{root_dir}/{dir}/parts/gen_{api}.c') - preamble_size
                else:
                    assert False, f"{my_status} Houston we have a problem: is not Active or Deactive"

##
## print all the reults to stdout
##
def print_results(success_dict, loc_dict):
    print("Function,#times correct, LOC")
    for api in success_dict:
        num_succesful = len(success_dict[api])
        #uuids = ",".join(success_dict[api])
        total_loc = loc_dict[api]
        print(f"{api},{num_succesful},{total_loc}")

##
## Write the results to a CSV file
## 
def write_csvs(success_active_dict, loc_active_dict, success_inactive_dict, loc_inactive_dict, active_csv, inactive_csv):
    # save to csv file
    with open(active_csv, "w") as f:
        writer = csv.writer(f)
        writer.writerow(["Function", "times correct", "LOC"])
        for api in success_active_dict:
            num_succesful = len(success_active_dict[api])
        #uuids = ",".join(success_dict[api])
            total_loc = loc_active_dict[api]
            writer.writerow([api, num_succesful, total_loc])


    with open(inactive_csv, "w") as f:
        writer = csv.writer(f)
        writer.writerow(["Function", "times correct", "LOC"])
        for api in success_inactive_dict:
            num_succesful = len(success_inactive_dict[api])
        #uuids = ",".join(success_dict[api])
            total_loc = loc_inactive_dict[api]
            writer.writerow([api, num_succesful, total_loc])
        f.close()


def find_passed_tests(root_dir):
    for dir in os.listdir(root_dir):
        # if the dir doesn't contain gold_standard
        if "gold_standard" in dir or  "unmodified" in dir:
            continue
        # if the dir is a directory
        D(f"{dir}")
        D(f"{os.path.join(root_dir, dir)}")
        preamble_size = non_blank_lines((f'{root_dir}/{dir}/parts/preamble.c'))
        api_report = json.load(open(f'{root_dir}/{dir}/api_report.json'))
        results = json.load(open(f'{root_dir}/{dir}/orig_testsuite.json'))


        dir_lookup = dir.removeprefix('repos/')
        my_status = study_status[dir_lookup]
        for api in api_report: 
            key = f"test_{api}"
            if results['results'][key]['passed'] == True:
                if my_status == 'Active':
                    passed_tests_active_dict[api].append(dir)
                    passed_tests_active_loc_dict[api] += non_blank_lines(f'{root_dir}/{dir}/parts/gen_{api}.c') - preamble_size

                elif my_status == 'Deactive':
                    passed_tests_inactive_dict[api].append(dir)
                    passed_tests_inactive_loc_dict[api] += non_blank_lines(f'{root_dir}/{dir}/parts/gen_{api}.c') - preamble_size

                else:
                    assert False, f"{my_status} Houston we have a problem: is not Active or Deactive"



# check that we have the correct number of arguments
if len(sys.argv) != 2:
    print("Usage: python3 fuzzer_collect_all_functs.py <root_dir>")
    sys.exit(1)


## read whether students are active or inactive
read_study_status(study_status)


##
## Find all the functions that compiled successfully
##
find_ok_results(sys.argv[1])

print("ACTIVE STUDY")
print_results(success_active_dict, loc_active_dict)
print("\n\n")

print("INACTIVE STUDY")
print_results(success_inactive_dict, loc_inactive_dict)
print("\n")


write_csvs(success_active_dict, loc_active_dict, success_inactive_dict, loc_inactive_dict, 
    "all_ok_functs_active_loc.csv", "all_ok_functs_inactive_loc.csv")


##
## Find all the functions that passed tests successfully
##
find_passed_tests(sys.argv[1])

print("ACTIVE and PASSED Tests")
print_results(passed_tests_active_dict, passed_tests_active_loc_dict)
print("\n\n")

print("INACTIVE and PASSED Tests")
print_results(passed_tests_inactive_dict, passed_tests_inactive_loc_dict)
print("\n")

write_csvs(passed_tests_active_dict, passed_tests_active_loc_dict, 
    passed_tests_inactive_dict, passed_tests_inactive_loc_dict, 
    "all_passed_tests_active_loc.csv", "all_passed_tests_inactive_loc.csv")



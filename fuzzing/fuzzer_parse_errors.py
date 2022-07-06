#!/usr/bin/env python

import sys
import re
import os
import json
import csv
from collections import defaultdict, Counter

DEBUG = False

def D(*args, **kwargs):
    if DEBUG: print(*args, **kwargs)


# read the input file passed as the first argument when launching the script
input_file = sys.argv[1]
uuid = os.path.basename(os.getcwd())

# second argument is whether we print a header in the output file
add_csv_header = sys.argv[2]

# Search for errors in the input file
gen_list_str = 'gen_list_'
began_parse_stack = False
error_dict = defaultdict(list)

# Parsing the input file
#  Errors look as follows:
#
# ==4168842==ERROR: AddressSanitizer: heap-use-after-free on address 0x602000006f50 at pc 0x555db1987286 bp 0x7fffb75553a0 sp 0x7fffb7554b68
# READ of size 2 at 0x602000006f50 thread T0
#     #0 0x555db1987285 in __interceptor_strdup (/home/gustavo/git/codex_study_grading/repos/3533dacf-349b-4581-bc32-6b9f015199c1/fuzzers/listfuzzer_list_deduplicate.bin+0xc6285) (BuildId: 31a0ae26da410b79d0cde6d1eaece1a18767b1e1)
#     #1 0x555db19d9adb in ref_list_update_item_at_pos /home/gustavo/git/codex_study_grading/repos/3533dacf-349b-4581-bc32-6b9f015199c1/reflist.c:164:23
#     #2 0x555db19dc62f in list_deduplicate /home/gustavo/git/codex_study_grading/repos/3533dacf-349b-4581-bc32-6b9f015199c1/parts/gen_list_deduplicate.c:43:17
#     #3 0x555db19d8bfd in LLVMFuzzerTestOneInput /home/gustavo/git/codex_study_grading/repos/3533dacf-349b-4581-bc32-6b9f015199c1/fuzzers/listfuzzer_list_deduplicate.c:154:17
#     #4 0x555db1900513 in fuzzer::Fuzzer::ExecuteCallback(unsigned char const*, unsigned long) (/home/gustavo/git/codex_study_grading/repos/3533dacf-349b-4581-bc32-6b9f015199c1/fuzzers/listfuzzer_list_deduplicate.bin+0x3f513) (BuildId: 31a0ae26da410b79d0cde6d1eaece1a18767b1e1)
#     #5 0x555db18ffc69 in fuzzer::Fuzzer::RunOne(unsigned char const*, unsigned long, bool, fuzzer::InputInfo*, bool, bool*) (/home/gustavo/git/codex_study_grading/repos/3533dacf-349b-4581-bc32-6b9f015199c1/fuzzers/listfuzzer_list_deduplicate.bin+0x3ec69) (BuildId: 31a0ae26da410b79d0cde6d1eaece1a18767b1e1)
#     #6 0x555db19018d8 in fuzzer::Fuzzer::ReadAndExecuteSeedCorpora(std::vector<fuzzer::SizedFile, std::allocator<fuzzer::SizedFile> >&) (/home/gustavo/git/codex_study_grading/repos/3533dacf-349b-4581-bc32-6b9f015199c1/fuzzers/listfuzzer_list_deduplicate.bin+0x408d8) (BuildId: 31a0ae26da410b79d0cde6d1eaece1a18767b1e1)
#     #7 0x555db1901dc2 in fuzzer::Fuzzer::Loop(std::vector<fuzzer::SizedFile, std::allocator<fuzzer::SizedFile> >&) (/home/gustavo/git/codex_study_grading/repos/3533dacf-349b-4581-bc32-6b9f015199c1/fuzzers/listfuzzer_list_deduplicate.bin+0x40dc2) (BuildId: 31a0ae26da410b79d0cde6d1eaece1a18767b1e1)
#     #8 0x555db18f0052 in fuzzer::FuzzerDriver(int*, char***, int (*)(unsigned char const*, unsigned long)) (/home/gustavo/git/codex_study_grading/repos/3533dacf-349b-4581-bc32-6b9f015199c1/fuzzers/listfuzzer_list_deduplicate.bin+0x2f052) (BuildId: 31a0ae26da410b79d0cde6d1eaece1a18767b1e1)
#     #9 0x555db1919b82 in main (/home/gustavo/git/codex_study_grading/repos/3533dacf-349b-4581-bc32-6b9f015199c1/fuzzers/listfuzzer_list_deduplicate.bin+0x58b82) (BuildId: 31a0ae26da410b79d0cde6d1eaece1a18767b1e1)
#     #10 0x7f6322c15fcf in __libc_start_call_main csu/../sysdeps/nptl/libc_start_call_main.h:58:16
#     #11 0x7f6322c1607c in __libc_start_main csu/../csu/libc-start.c:409:3
found_error = False
with open(input_file, 'r') as f:
    for line in f:
        # Search for the line that contains the error
        if 'ERROR: ' in line:
            # Extract the error message
            found_error = True # we found at least one error
            parts = line.split()
            #D(len(parts))
            error_msg = parts[2] + ' ' + parts[3]
            began_parse_stack = True
        elif began_parse_stack:
            # Extract the stack trace
            idx = line.find(gen_list_str)
            if idx != -1:
                error_line = line[idx + len(gen_list_str):]
                error_dict[error_line.strip()].append(error_msg.strip())
                began_parse_stack = False
                error_msg = ''



if not found_error:
    D(f'No errors found. File: {input_file}')
    exit(0)


# Get the study status (Acttive or Inactive)
study_status = defaultdict()
with open("../../active_inactive.txt") as f:
    for line in f:
       (key, val) = line.split()
       study_status[key] = val

my_status = study_status[uuid]


def get_dict_from_file(file_name):
    dict = defaultdict()
    with open(file_name, 'r') as f:
        for line in f:
            (key, val, _) = line.split(",")
            dict[key] = val

    return dict


def get_lines_of_code(function_name, study):
    """
    Get the lines of code for both types of functions:
    1. Compiling
    2. Passing Tests

    Returns: 
        loc_compiling: lines of code for compiling
        loc_passing_tests: lines of code for passing tests
    """
    success_dict = defaultdict()
    passed_tests_dict = defaultdict()
    
    if study == 'Inactive':
        D(f'Study is inactive.')
        success_file = f'../../all_ok_functs_inactive_loc.csv'
        passed_tests_file = f'../../all_passed_tests_inactive_loc.csv'
    else:
        D(f'Study is Active.')
        success_file = f'../../all_ok_functs_active_loc.csv'
        passed_tests_file = f'../../all_passed_tests_active_loc.csv'

    success_dict = get_dict_from_file(success_file)
    passed_tests_dict = get_dict_from_file(passed_tests_file)

    # get the lines of code
    loc_compiling = success_dict[function_name]
    loc_passing_tests = passed_tests_dict[function_name]
    # convert  to int
    return int(loc_compiling), int(loc_passing_tests)

        


# Get the lines of code for the file
# it's basically the number of lines in the parts/gen_list_deduplicate.c file
filename = input_file.removesuffix('_noleak.log')
filename = filename.removeprefix('listfuzzer_')
lines_of_code = 0
input_file = "parts/" + filename + ".c"
input_file_exists = os.path.isfile(input_file)
if input_file_exists:
    with open(input_file, 'r') as f:
        for line in f:
            # if the line is not a comment in C++
            if  not line.startswith('//'):
                lines_of_code += 1

else: 
    assert False, f'{input_file} does not exist'


assert lines_of_code > 0

csvfilename = 'fuzzer_results.csv'
file_exists = os.path.isfile(csvfilename)

E_ij = 0
l = 0
for key, value in error_dict.items():
    myset = Counter(value)
    l = len(myset)
    E_ij += l
    
D(f"Filename: {filename}, error_dict Counter: {Counter(error_dict)} E_ij: {E_ij}")

# write values to a csv file
with open(csvfilename, 'a', newline='') as f:
    fieldnames = ['uuid', 'study', 'function', 'error_line', 'error_message', 'L_ij', 'E_ij', 'K_ij', 
        'F_ij compiling', 'F_ij passing tests']
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    if not file_exists and  (add_csv_header == True):
        writer.writeheader()

    for error_line, error_messages in error_dict.items():
        ctr = Counter(error_messages)
        # sum the total number of errors for this line

        for key, value in ctr.items():
            #print(f"filename: {filename}")
            users_compiling, users_passing_tests = get_lines_of_code(filename, my_status)
            kij = E_ij/lines_of_code
            writer.writerow({'uuid': uuid, 
                'study': my_status, 
                'function':filename, 
                'error_line': error_line, 
                'error_message': key, 
                'L_ij': lines_of_code,  # L_ij = Lines of code contributed by user j in function i
                'E_ij': E_ij,       # E_ij = unique errors found in function i and user j
                'K_ij': round(kij, 4),  # K_ij = Errors per line of code for function i and user j
                'F_ij compiling': users_compiling,# F_ij = indicator function value = 1 if user j compiles function i
                'F_ij passing tests': users_passing_tests}) # F_ij = indicator function value = 1 if user j passes tests in  function i


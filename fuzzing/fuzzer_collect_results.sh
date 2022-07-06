#!/bin/bash
MAG='\033[0;35m'
RESET='\033[0m'



noleak_files="listfuzzer_list_add_item_at_pos_noleak.log 
listfuzzer_list_cost_sum_noleak.log 
listfuzzer_list_deduplicate_noleak.log 
listfuzzer_list_find_highest_price_item_position_noleak.log 
listfuzzer_list_init_noleak.log
listfuzzer_list_item_to_string_noleak.log
listfuzzer_list_load_noleak.log
listfuzzer_list_print_noleak.log
listfuzzer_list_remove_item_at_pos_noleak.log 
listfuzzer_list_save_noleak.log
listfuzzer_list_swap_item_positions_noleak.log
listfuzzer_list_update_item_at_pos_noleak.log
listfuzzer_list_add_item_at_pos_noleak.log"

echo "Start time: $(date)"

echo -e "${MAG} Deleting old results files ... ${RESET}"

# recursively delete all the current results files
csvfilename="fuzzer_results.csv"
for d in repos/*; do
    if [ "$dirname" != "gold_standard" ] && [ "$dirname" != "unmodified" ]; then
        cd "$d" || exit
        if [ -e $csvfilename ]; then
            rm $csvfilename
        fi
        cd - > /dev/null || exit
    fi
done

echo -e "${MAG} Collecting Fuzzing Results into one error file... ${RESET}"

for d in repos/*; do
    # Append the results to the file
    dirname=$(basename $d)
    if [ "$dirname" != "gold_standard" ] && [ "$dirname" != "unmodified" ]; then
        cd "$d" || exit
        #echo -e "Collecting results for $d"
        for f in $noleak_files; do
            python ../../fuzzer_parse_errors.py "$f" 0
        done
        cd - > /dev/null || exit
    fi
done

echo -e "${MAG} Summarizing Fuzzing Results ... ${RESET}"

# # join all the files together
resultsfile="fuzzer_results_all.csv"
if [ -e $resultsfile ]; then
    rm $resultsfile
fi


# Note this is a hack to get the header to be the first line of the file
# This is because the header is not included in the file created by the fuzzer
# It should be the same as the header in fuzzer_parse_errors.py
echo "uuid, study, function, error_line, error_message, L_ij, E_ij, K_ij, F_ij compiling, F_ij passing tests" > $resultsfile

for d in repos/*; do
    dirname=$(basename $d)
    if [ "$dirname" != "gold_standard" ] && [ "$dirname" != "unmodified" ]; then
        # Append the results to the file
        cd "$d" || exit
        if [ -e "fuzzer_results.csv" ]; then
            #echo -e "Appending results for $d"  
            cat fuzzer_results.csv >> ../../$resultsfile
        else
            echo -e "No results for $d"
        fi
        cd - > /dev/null || exit
    fi
done


# Fuzzer results per user


echo -e "${MAG} Fuzzing Results per function in $resultsfile ... ${RESET}"

# now just use command line hackery to get the results per user
user_results_file_tmp="user_results_file.tmp"
user_results_file="fuzzer_results_per_user.csv"
if [ -e $user_results_file ]; then
    rm $user_results_file
fi


cat $resultsfile | awk -F',' '{print $1, $2, $3, $6, $7, $8, $9, $10}' | sort | uniq > $user_results_file_tmp
head -n -1 $user_results_file_tmp > user_temp2.tmp 
sed 'y/ /,/' user_temp2.tmp > $user_results_file_tmp

# sed '$d' fuzzer_results_users.csv # remove the last line that contains the header
echo "uuid, study, function, L_ij, E_ij, K_ij, F_ij compiling, F_ij passing tests" > $user_results_file
cat $user_results_file_tmp >> $user_results_file
rm $user_results_file_tmp user_temp2.tmp 

# rm user_results_file_tmp

echo -e "${MAG} Fuzzing Results per user in $user_results_file ... ${RESET}"

echo "End time: $(date)"
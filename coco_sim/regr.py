import subprocess
from itertools import product
from check_result import check_test_failures
# Define parameter sets as tuples
fc = ((1,0), (1,1), (5,1), (1,5) , (5,5))
delay = ('0', 'short')
pkt_num = (10, 50, 100)

# Generate all possible combinations
combinations = tuple(product(fc, delay,))

# Define the result file
result_file = "result.txt"

# Clear the result file at the beginning
with open(result_file, "w") as file:
    file.write("")  # Optional header

# Iterate through each combination
for combo in combinations:
    # Run the test with the given combination
    print(combo[1])
    cmd = ["python3", "rs_decoder.py", "-l", "RsBlockRecovery", "-s", "1", "-f", str(combo[0]) , "-d", combo[1], "-t", "min_max_test" ]
    subprocess.run(cmd)

    # Check test result (returns a list of failed test names or an empty list)
    failed_tests = check_test_failures("sim_build/results.xml")

    # Determine test status
    if failed_tests:
        test_status = "FAIL"
        failed_tests_str = ", ".join(failed_tests)  # Convert list to string
    else:
        test_status = "PASS"
        failed_tests_str = ""

    # Append the result to the file
    with open(result_file, "a") as file:  # Use "a" mode to append instead of overwriting
        file.write(f"{test_status} : {combo}\n")
        if failed_tests:  # Append failed test names if there were failures
            file.write(f"FAILED TESTS: {failed_tests_str}\n")

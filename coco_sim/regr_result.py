import sys

def check_test_results(result_file):
    """
    Parses result.txt and raises an error if any test failed.

    Args:
        result_file (str): Path to the result file.

    Raises:
        SystemExit: Exits with an error code if failures are found.
    """
    with open(result_file, "r") as file:
        lines = file.readlines()

    # Check for failures
    failed_tests = [line.strip() for line in lines if line.startswith("FAIL")]

    if failed_tests:
        print("Test failures detected!")
        for fail in failed_tests:
            print(fail)  # Print the failed test entry
        sys.exit(1)  # Exit with error code 1 (indicating failure)
    else:
        print("All tests passed successfully.")
        sys.exit(0)  # Exit with code 0 (indicating success)

# Run the function
if __name__ == "__main__":
    check_test_results("result.txt")

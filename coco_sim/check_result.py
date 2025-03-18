# ----------------------------------------------------------------------
#  Copyright (c) 2024 Egor Smirnov
#
#  Licensed under terms of the MIT license
#  See https://github.com/egorman44/Reed-Solomon/blob/main/LICENSE
#    for license terms
# ----------------------------------------------------------------------

import sys
import xml.etree.ElementTree as ET

def check_test_failures(xml_file):
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()

        # Find all <testcase> elements that contain a <failure> tag
        failed_tests = [
            testcase.get("name") for testcase in root.findall(".//testcase[failure]")
        ]

        if failed_tests:
            print(f"{len(failed_tests)} test(s) failed: {failed_tests}")
            return failed_tests  # Return a list of failed test names
        else:
            print("All tests passed.")
            return []  # Return an empty list if no failures
    except ET.ParseError as e:
        print(f"Error parsing XML: {e}")
        sys.exit(2)  # Exit code 2 for XML parsing issues
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(3)  # Exit code 3 for other unexpected errors

if __name__ == "__main__":
    xml_file_path = "sim_build/results.xml"  # Change this to your actual file path
    check_test_failures(xml_file_path)

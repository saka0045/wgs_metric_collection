#!/usr/bin/env python3

import argparse
import os
import sys


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-s", "--sampleTextFile", dest="sample_text_file", required=True
    )
    parser.add_argument(
        "-o", "--outputDirectory", dest="output_directory", required=True
    )

    args = parser.parse_args()

    sample_text_file_path = os.path.abspath(args.sample_text_file)
    output_directory = os.path.abspath(args.output_directory)

    # Parse out the sample name
    sample_text_file = open(sample_text_file_path, "r")
    sample_information_dict = parse_sample_text_file(sample_text_file)
    # If there are case IDs already present in the samples.txt file, abort
    if "caseId" in sample_information_dict.keys():
        sys.exit()

    # Write just the sample names to sample_names.txt for easier bash handling
    sample_name_file = open(output_directory + "/sample_names.txt", "w")

    for key, val in sample_information_dict.items():
        sample_name_file.write(val)
        sample_name_file.write("\n")

    sample_text_file.close()
    sample_name_file.close()


def parse_sample_text_file(sample_text_file):
    """
    Parses the samples.txt file information
    :param sample_text_file:
    :return:
    """
    sample_information_dict = {}
    for line in sample_text_file:
        line = line.rstrip()
        if ":" in line:
            line_item = line.split(":")
            sample_information_dict[line_item[0]] = line_item[1]
        else:
            sample_information_dict["NA"] = line
    return sample_information_dict


if __name__ == "__main__":
    main()

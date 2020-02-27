#!/usr/bin/env python3

import argparse
import os


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-i", "--inputDirectory", dest="input_directory", required=True
    )
    parser.add_argument(
        "-s", "--sampleTextFile", dest="sample_text_file", required=True
    )

    args = parser.parse_args()

    sample_text_file_path = os.path.abspath(args.sample_text_file)
    input_directory = os.path.abspath(args.input_directory)

    # Gather sample information
    sample_text_file = open(sample_text_file_path, "r")
    sample_information_dict = {}
    for line in sample_text_file:
        line = line.rstrip()
        line_item = line.split(":")
        sample_information_dict[line_item[0]] = line_item[1]

    # Initialize the WGS metric dict
    wgs_metric_dict = {}

    for key in sample_information_dict.keys():
        # Loop through the samples and gather metrics for the sample
        if key != "caseId":
            sample_name = sample_information_dict[key]
            # Initialize each sample entry for wgs_metric_dict
            wgs_metric_dict[sample_name] = {}
            # Gather metrics for each sample
            wgs_metric_dict = gather_metrics_for_sample(input_directory, sample_name, wgs_metric_dict)
        else:
            continue

    # Collect the joint metrics after all of the samples on the run has individual metrics collected
    # If joint metric collection is not done after all of the samples individual metrics hasn't been collected,
    # not all samples' joint metrics will be collected
    case_id = sample_information_dict["caseId"]
    joint_snv_metric_file_path = input_directory + "/" + case_id + "-joint-snv.vc_metrics.csv"
    collect_metrics(joint_snv_metric_file_path, "NA", wgs_metric_dict, "JOINT CALLER POSTFILTER")

    print(wgs_metric_dict)


def gather_metrics_for_sample(input_directory, sample_name, wgs_metric_dict):
    """
    Function to collect mapping, coverage and individual vc metric for sample
    :param input_directory:
    :param sample_name:
    :param wgs_metric_dict:
    :return:
    """
    # Gather the file path for the metric files
    mapping_metric_file_path = create_metric_file_path(input_directory, sample_name, "mapping_metrics.csv")
    wgs_coverage_metric_file_path = create_metric_file_path(input_directory, sample_name, "wgs_coverage_metrics.csv")
    individual_vc_metric_file_path = create_metric_file_path(input_directory, sample_name, "vc_metrics.csv")
    # Collect mapping metric
    collect_metrics(mapping_metric_file_path, sample_name, wgs_metric_dict, "MAPPING/ALIGNING SUMMARY")
    # Collect wgs coverage metric
    collect_metrics(wgs_coverage_metric_file_path, sample_name, wgs_metric_dict, "COVERAGE SUMMARY")
    # Collect individual vc metric
    collect_metrics(individual_vc_metric_file_path, sample_name, wgs_metric_dict, "VARIANT CALLER POSTFILTER")
    return wgs_metric_dict


def create_metric_file_path(input_directory, sample_name, file_name):
    """
    Creates the file path to the specific metric file
    :param input_directory:
    :param sample_name:
    :param file_name: String of the metric file name
    :return:
    """
    metric_file_path = input_directory + "/" + sample_name + "." + file_name
    return metric_file_path


def collect_metrics(metric_file_path, sample_name, wgs_metric_dict, string_match):
    """
    Function to gather the metrics from a given metric file
    :param metric_file_path:
    :param sample_name:
    :param wgs_metric_dict:
    :param string_match: String for metric_group to pull the metric from the given file
    :return:
    """
    metric_file = open(metric_file_path, "r")
    # Collect metrics
    for line in metric_file:
        line = line.rstrip()
        line_item = line.split(",")
        metric_group = line_item[0]
        if line_item[1] != "":
            sample_name_for_dict = line_item[1]
        else:
            sample_name_for_dict = sample_name
        metric_item = line_item[2]
        metric_count = line_item[3]
        try:
            metric_percent = line_item[4]
        except IndexError:
            metric_percent = ""
        if metric_group == string_match:
            if metric_group not in wgs_metric_dict[sample_name_for_dict]:
                wgs_metric_dict[sample_name_for_dict][metric_group] = {}
            wgs_metric_dict[sample_name_for_dict][metric_group][metric_item] = \
                [metric_count, metric_percent]
    metric_file.close()


if __name__ == "__main__":
    main()

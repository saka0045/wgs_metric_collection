#!/usr/bin/env python3

import argparse
import os
from process_samples_file import parse_sample_text_file


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-i", "--inputDirectory", dest="input_directory", required=True
    )
    parser.add_argument(
        "-s", "--sampleTextFile", dest="sample_text_file", required=True
    )
    parser.add_argument(
        "-m", "--metricFile", dest="config_metric_file", required=True
    )

    args = parser.parse_args()

    sample_text_file_path = os.path.abspath(args.sample_text_file)
    input_directory = os.path.abspath(args.input_directory)
    config_metric_file_path = os.path.abspath(args.config_metric_file)

    # Gather sample information
    sample_text_file = open(sample_text_file_path, "r")
    sample_information_dict = parse_sample_text_file(sample_text_file)

    # Initialize the WGS metric dict
    wgs_metric_dict = {}
    sample_list = []

    for key in sample_information_dict.keys():
        # Loop through the samples and gather metrics for the sample
        if key != "caseId":
            sample_name = sample_information_dict[key]
            sample_list.append(sample_name)
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

    # Calculate the trio concordance if appropriate
    if "mother" in sample_information_dict.keys() or "father" in sample_information_dict.keys():
        calculate_trio_concordance(sample_information_dict, wgs_metric_dict)
    else:
        for sample in sample_list:
            wgs_metric_dict[sample]["JOINT CALLER POSTFILTER"]["Trio Concordance"] = ["NA", ""]

    # Write the desired metrics out to a file
    result_file = open(input_directory + "/" + case_id + "_wgs_metrics.csv", "w")
    # Write header
    for sample in sample_list:
        result_file.write("," + sample)
    result_file.write("\nPedigree Status")
    for sample in sample_list:
        for key, val in sample_information_dict:
            if val == sample:
                result_file.write("," + key)
    result_file.write("\n")
    # Fill out the file with desire metrics
    # Open the metric file to gather which metrics need to be written to the result file
    config_metric_file = open(config_metric_file_path, "r")
    for line in config_metric_file:
        line = line.rstrip()
        config_metric_line_item = line.split(",")
        metric_header = config_metric_line_item[0]
        metric_category = config_metric_line_item[1]
        metric = config_metric_line_item[2]
        metric_type = config_metric_line_item[3]
        write_metric_to_result_file(result_file, sample_list, wgs_metric_dict, metric_header, metric_category, metric,
                                    metric_type)

    config_metric_file.close()
    result_file.close()

    print("script is finished running")


def calculate_trio_concordance(sample_information_dict, wgs_metric_dict):
    """
    Calculates the trio concordance from the joint vc metric file
    Current TSSS version doesn't account for DeNovo chr X and chr Y SNPs but will in the future
    This script will take into account the DeNovo chr X and chr Y SNP counts
    :param sample_information_dict:
    :param wgs_metric_dict:
    :return:
    """
    # Identify the proband, mother and father samples
    proband_sample_list = []
    for key in sample_information_dict.keys():
        if key == "proband":
            proband_sample_list.append(sample_information_dict[key])
        elif key == "mother":
            mother_sample = sample_information_dict[key]
        elif key == "father":
            father_sample = sample_information_dict[key]
    for proband in proband_sample_list:
        try:
            joint_post_filter_denovo_count = (
                    int(wgs_metric_dict[proband]["JOINT CALLER POSTFILTER"]["DeNovo Autosome SNPs"][0]) +
                    int(wgs_metric_dict[proband]["JOINT CALLER POSTFILTER"]["DeNovo chrX SNPs"][0]) +
                    int(wgs_metric_dict[proband]["JOINT CALLER POSTFILTER"]["DeNovo chrY SNPs"][0])
            )
            joint_post_filter_snp_count = int(wgs_metric_dict[proband]["JOINT CALLER POSTFILTER"]["SNPs"][0])
            trio_concordance = (1 - (joint_post_filter_denovo_count / joint_post_filter_snp_count)) * 100
            # Write the trio concordance results to wgs_metric_dict
            wgs_metric_dict[proband]["JOINT CALLER POSTFILTER"]["Trio Concordance"] = [str(trio_concordance), ""]
        # If no "DeNovo ..." key exists:
        except KeyError:
            wgs_metric_dict[proband]["JOINT CALLER POSTFILTER"]["Trio Concordance"] = ["NA", ""]
    # Fill out parents trio concordance as "NA"
    try:
        wgs_metric_dict[mother_sample]["JOINT CALLER POSTFILTER"]["Trio Concordance"] = ["NA", ""]
    except UnboundLocalError:
        pass
    try:
        wgs_metric_dict[father_sample]["JOINT CALLER POSTFILTER"]["Trio Concordance"] = ["NA", ""]
    except UnboundLocalError:
        pass


def write_metric_to_result_file(result_file, sample_list, wgs_metric_dict, metric_header, metric_category, metric,
                                metric_type):
    """
    Parses the wgs_metric_dict and creates the result file
    :param result_file:
    :param sample_list:
    :param wgs_metric_dict:
    :param metric_header: String, the metric name to use for the file
    :param metric_category: String, the metric category found in the metric cvs file the metric belongs to
    :param metric: String, the metric to be pulled
    :param metric_type: String, count or percent. Count is the first number stored in the list and percent is stored
    second
    :return:
    """
    result_file.write(metric_header)
    if metric_type == "count":
        metric_type = 0
    elif metric_type == "percent":
        metric_type = 1
    for sample in sample_list:
        result_file.write("," + wgs_metric_dict[sample][metric_category][metric][metric_type])
    result_file.write("\n")


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

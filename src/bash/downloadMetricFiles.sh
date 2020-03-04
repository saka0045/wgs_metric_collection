#!/usr/bin/env bash

##################################################
# MANIFEST
##################################################

read -r -d '' MANIFEST <<MANIFEST
*******************************************
`readlink -m $0` ${@}
was called by: `whoami` on `date`
*******************************************
MANIFEST
echo "${MANIFEST}"

read -r -d '' DOCS <<DOCS

Script to download metric files from TSSS and process the files to create a single metric file

<DEFINE PARAMETERS>
Parameters:
	-s [required] sample-text-file - full path to the samples.txt file
	-o [required] output-dir - local output directory to save files
	-r [required] remote-path - output directory to TSSS case with the metric files
	-h [optional] debug - option to print this menu option

Usage:
$0 -s {sample_txt_file} -o {output_dir}
DOCS

#Show help when no parameters are provided
if [ $# -eq 0 ];
then
    echo "${DOCS}" ; exit 1 ;
fi

##################################################
#GLOBAL VARIABLES
##################################################

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT_FILE="${SCRIPT_DIR}/$(basename "${BASH_SOURCE[0]}")"
SCRIPT_NAME="$(basename ${0})"
ROOT="$(cd "${SCRIPT_DIR}/../../" && pwd)"
PYTHON_SCRIPTS="${ROOT}/src/python"
PROFILE="${ROOT}/config/downloadMetricFile.profile"
SAMPLE_TEXT_FILE=""
OUTPUT_DIR=""
CMD=""
CASE_ID=""
REMOTE_PATH=""
MAPPING_METRIC_FILE=""
WGS_COVERAGE_METRIC_FILE=""
INDIVIDUAL_VC_METRIC_FILE=""
FILE_DOWNLOAD_JOBS=()

##################################################
#Source Pipeline Profile
##################################################

echo "Using configuration file at ${PROFILE}"
source ${PROFILE}

##################################################
#Source Common Function
##################################################

if [[ ! -f ${COMMON_FUNC} ]]; then
    echo -e "\nERROR: The common functions were not found in ${COMMON_FUNC}\n"
    exit 1
fi

echo "Using common functions: ${COMMON_FUNC}"
source ${COMMON_FUNC}

##################################################
#Bash handling
##################################################

set -o errexit
set -o pipefail
set -o nounset

##################################################
#BEGIN PROCESSING
##################################################

while getopts "hs:o:r:" OPTION
do
    case $OPTION in
        h) echo "${DOCS}" ;  exit ;;
        s) SAMPLE_TEXT_FILE=${OPTARG} ;;
        o) OUTPUT_DIR=${OPTARG} ;;
        r) REMOTE_PATH=${OPTARG} ;;
        ?) echo "${DOCS}" ; exit ;;
    esac
done

# Remove any trailing "/" from OUTPUT_DIR and REMOTE_PATH
OUTPUT_DIR=${OUTPUT_DIR%/}
REMOTE_PATH=${REMOTE_PATH%/}

# Process the samples.txt file to create sample_names.txt and caseId.txt files
CMD="${PYTHON} ${PYTHON_SCRIPTS}/process_samples_file.py -s ${SAMPLE_TEXT_FILE} -o ${OUTPUT_DIR}"
echo "Executing command: ${CMD}"
${CMD}

CASE_ID_FILE="${OUTPUT_DIR}/caseId.txt"
SAMPLE_NAMES_FILE="${OUTPUT_DIR}/sample_names.txt"

source ${CASE_ID_FILE}
echo "Case ID for case to download from TSSS is: ${CASE_ID}"

# Download metric files for each sample
while IFS= read -r SAMPLE; do
    MAPPING_METRIC_FILE="${REMOTE_PATH}/${SAMPLE}/dragen/${SAMPLE}.mapping_metrics.csv"
    WGS_COVERAGE_METRIC_FILE="${REMOTE_PATH}/${SAMPLE}/dragen/${SAMPLE}.wgs_coverage_metrics.csv"
    INDIVIDUAL_VC_METRIC_FILE="${REMOTE_PATH}/${SAMPLE}/dragen/${SAMPLE}.vc_metrics.csv"
    CMD="${QSUB} ${QSUB_ARGS} ${ILLUMINA_WRAPPER_SCRIPT} -c download -r ${MAPPING_METRIC_FILE} -o ${OUTPUT_DIR}"
    echo "Executing command: ${CMD}"
    JOB_ID=$(${CMD})
    FILE_DOWNLOAD_JOBS+=("${JOB_ID}")
    CMD="${QSUB} ${QSUB_ARGS} ${ILLUMINA_WRAPPER_SCRIPT} -c download -r ${WGS_COVERAGE_METRIC_FILE} -o ${OUTPUT_DIR}"
    echo "Executing command: ${CMD}"
    JOB_ID=$(${CMD})
    FILE_DOWNLOAD_JOBS+=("${JOB_ID}")
    CMD="${QSUB} ${QSUB_ARGS} ${ILLUMINA_WRAPPER_SCRIPT} -c download -r ${INDIVIDUAL_VC_METRIC_FILE} -o ${OUTPUT_DIR}"
    echo "Executing command: ${CMD}"
    JOB_ID=$(${CMD})
    FILE_DOWNLOAD_JOBS+=("${JOB_ID}")
done < "${SAMPLE_NAMES_FILE}"

for JOB_ID in ${FILE_DOWNLOAD_JOBS[@]:-}; do
    waitForJob ${JOB_ID} 3600 20
done

echo "All files downloaded"
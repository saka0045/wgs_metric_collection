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

while getopts "hs:o:" OPTION
do
    case $OPTION in
        h) echo "${DOCS}" ;  exit ;;
        s) SAMPLE_TEXT_FILE=${OPTARG} ;;
        o) OUTPUT_DIR=${OPTARG} ;;
        ?) echo "${DOCS}" ; exit ;;
    esac
done

CMD="${PYTHON} ${PYTHON_SCRIPTS}/process_samples_file.py -s ${SAMPLE_TEXT_FILE} -o ${OUTPUT_DIR}"
echo "Executing command: ${CMD}"
${CMD}

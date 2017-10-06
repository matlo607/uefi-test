#!/usr/bin/env bash

export PS4="+${BASH_SOURCE[0]}:${LINENO}:${FUNCNAME}: "

set -o errexit
set -o pipefail
#set -o nounset
#set -o xtrace

__dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
__file="${__dir}/$(basename "${BASH_SOURCE[0]}")"
__base="$(basename ${__file} .bash)"
__root="$(cd "$(dirname "${__dir}")" && pwd)"

__img_name="disk.img"
__to_copy=()
__img_force_dd=false
__img_force_format=false
__img_force_copy=false
__cache_clean=false


function __parse_args() {
    if [[ $# -eq 0 ]]; then
        __usage
        exit 1
    fi

    while :; do
        case ${1} in
            -h|-\?|--help)
                __usage
                exit 0
                ;;
            -o|--output)
                if [ -n "${2}" ]; then
                    __img_name=${2}
                    shift
                else
                    printf 'ERROR: "--output" requires a non-empty option argument.\n' >&2
                    exit 1
                fi
                ;;
            --output=?*)
                __img_name=${1#*=} # Delete everything up to "=" and assign the remainder.
                ;;
            --output=) # Handle the case of an empty --prefix=
                printf 'ERROR: "--output" requires a non-empty option argument.\n' >&2
                exit 1
                ;;
            --force-dd)
                __img_force_dd=true
                ;;
            --force-format)
                __img_force_format=true
                ;;
            --force-copy)
                __img_force_copy=true
                ;;
            --cache-clean)
                __cache_clean=true
                ;;
            [[:alnum:]\./]*)
                if [[ !( -f ${1} || -d ${1} ) ]]; then
                    printf 'ERROR: %s is not a file or a directory.\n' "${1}" >&2
                    exit 1
                else
                    __to_copy+=("${1}")
                fi
                ;;
            --)              # End of all options.
                break
                ;;
            -?*)
                printf 'WARN: Unknown option (ignored): %s\n' "$1" >&2
                ;;
            *)               # Default case: If no more options then break out of the loop.
                break
        esac

        shift
    done

    if [[ -z ${__img_name+1} || ${#__to_copy[@]} -eq 0 ]]; then
        if [[ ${#__to_copy[@]} -eq 0 ]]; then
            printf 'ERROR: which file do you want to copy onto the disk file?\n' >&2
        fi
        __usage
        exit 1
    fi

    __cache_clean=${__img_force_dd}
    __img_force_format=${__img_force_dd}
    __img_force_copy=${__img_force_format}

    if [[ ! -f "${__img_name}" ]]; then
        __img_force_dd=true
        __img_force_format=true
    fi

    #echo "__img_name = ${__img_name}"
    #echo "__to_copy = ${__to_copy[@]}"
    #echo "__img_force_dd = ${__img_force_dd}"
    #echo "__img_force_format = ${__img_force_format}"
    #echo "__img_force_copy = ${__img_force_copy}"
    #echo "__cache_clean = ${__cache_clean}"
}

function __usage ()
{
    cat <<-USAGE_HELP
Usage: ${__base} [options] [-o output] PATHS

Create a disk file with the files or directories passed in arguments.

Options:
    -h|--help        : Display this help
    -o|--output file : Place output in file file
    --cache-clean    : Clean cache
    --force-dd       : Force creation of an empty (zeroed) disk
    --force-format   : Force formatting of the EFI partition
    --force-copy     : Force replacing all files and cache update
USAGE_HELP
}

function __cache_get_outdatedOrAbsent()
{
    local outdatedOrAbsent=()
    for f in ${__to_copy[@]}; do
        local path_cache_file="${__cache_dir}/$(basename ${f})"
        if [[ -f "${path_cache_file}" ]]; then
            local date_cache="$(cat ${path_cache_file})"
            local date_file="$(date -r ${f})"
            if [[ "${date_cache}" != "${date_file}" ]]; then
                outdatedOrAbsent+=(${f})
            fi
        else
            # new file not in cache yet
            outdatedOrAbsent+=(${f})
        fi
    done
    __to_copy=( "${outdatedOrAbsent[@]}" )
    if [[ ${#__to_copy[@]} -eq 0 ]]; then
        echo "[${__base}] cache up to date, nothing to do"
    fi
}

function __main () {
    __parse_args $@

    __cache_dir="$(dirname ${__img_name})/.cache"
    if [[ "${__cache_clean}" = "true" ]]; then
        rm -rf "${__cache_dir}"
    fi
    # create cache directory if it does not exist
    if [[ ! -d ${__cache_dir} ]]; then
        mkdir -p "${__cache_dir}"
        echo "[${__base}] create cache: ${__cache_dir}"
    fi

    if [[ "${__img_force_dd}" = "true" ]]; then
        # create empty image
        dd if="/dev/zero" of="${__img_name}" bs=512 count=93750
        gdisk "${__img_name}" <<EOF
o
y
n



ef00
w
y
EOF
    fi

    __cache_get_outdatedOrAbsent
    if [[ ${#__to_copy[@]} -ne 0 ]]; then
        # mount the EFI partition on loopback device and format it to FAT32
        _loop_device=$(losetup -f)
        sudo losetup --offset 1048576 --sizelimit 46934528 "${_loop_device}" "${__img_name}"

        if [[ "${__img_force_dd}" = "true" || "${__img_force_format}" = "true" ]]; then
            sudo mkfs.fat -I -F 32 "${_loop_device}"
        fi

        # mount the newly formatted EFI partition and copy the files or directories
        sudo mount "${_loop_device}" "/mnt"

        for f in ${__to_copy[@]}; do
            if [[ -d "${f}" ]]; then
                sudo cp -r "${f}" "/mnt"
            else
                sudo cp "${f}" "/mnt"
            fi
            echo "[${__base}] copy ${f} to $(basename ${__img_name})"

            # update cache
            echo $(date -r ${f}) >"${__cache_dir}/$(basename ${f})"
        done

        sudo umount "/mnt"
        sudo losetup -d "${_loop_device}"
    fi
    exit 0
}

__main $@

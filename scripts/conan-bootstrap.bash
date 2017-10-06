#!/usr/bin/env bash

export PS4="+${BASH_SOURCE[0]}:${LINENO}:${FUNCNAME}: "

set -o errexit
set -o pipefail
#set -o xtrace
set -o nounset

__dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
__file="${__dir}/$(basename "${BASH_SOURCE[0]}")"
__base="$(basename ${__file} .bash)"
__root="$(cd "$(dirname "${__dir}")" && pwd)"

_EXPORTED=()
_IGNORE=("gnu-binutils" "edk2")

function in_array()
{
    declare -a array=("${!1}")
    local match=${2}

    for i in ${array[@]}; do
        if [[ "${i}" = "${match}" ]]; then
            echo "true"
            return
        fi
    done
    echo "false"
}

pushd . >/dev/null
cd ${__root}
for conanfile in $(find "${__root}/conan-recipes" -type f -name "conanfile.py"); do
    _pkgname=$(sed -n -e 's/^[[:space:]]*name = ["'\'']\(.*\)["'\'']$/\1/p' "${conanfile}")
    _version=$(sed -n -e 's/^[[:space:]]*version = ["'\'']\(.*\)["'\'']$/\1/p' "${conanfile}")

    _dir_conanfile=$(dirname ${conanfile})
    _basedir_conanfile=$(basename ${_dir_conanfile})
    echo " * found conanfile.py in ${_dir_conanfile}"
    if [[ "$(in_array _IGNORE[@] "${_basedir_conanfile}")" = "true" ]]; then
        echo -e "\tblacklisted: ignore ${_basedir_conanfile}"
        continue
    fi

    _conan_export_pkgname="${_pkgname}/${_version}@${USER}/testing"
    pushd . >/dev/null
    cd ${_dir_conanfile}
    echo -e "\tconan export --file conanfile.py ${_conan_export_pkgname}"
    conan export --file "conanfile.py" "${_conan_export_pkgname}"
    popd >/dev/null

    _EXPORTED+=("${_conan_export_pkgname}")
done
popd >/dev/null

########################
# Create conanfile.txt #
########################
echo " * create ${__root}/conanfile.txt"
echo "----------------------------------------------------"
echo "[requires]" >"${__root}/conanfile.txt"
for p in ${_EXPORTED[@]}; do
    # don't export mingw64-toolchain, it's already exported with conan's profile
    if [[ "${p}" != "mingw64-toolchain"* ]]; then
        echo "${p}" >>"${__root}/conanfile.txt"
    fi
done
cat <<<'
[generators]
cmake
virtualenv' >>"${__root}/conanfile.txt"
cat "${__root}/conanfile.txt"

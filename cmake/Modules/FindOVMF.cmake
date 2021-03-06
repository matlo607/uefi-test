# - Try to find OVMF
#
# The following variables are optionally searched for defaults
#  OVMF_ROOT_DIR:    Base directory where all GNU efi components are found
#
# The following are set after configuration is done:
#  OVMF_FOUND
#  OVMF_DISK_IMG

include(FindPackageHandleStandardArgs)

set(OVMF_ROOT_DIR "" CACHE PATH "Folder contains OVMF disk image")

find_file(OVMF_DISK_IMG "OVMF.fd"
    PATHS "${OVMF_ROOT_DIR}" "/usr/share"
    PATH_SUFFIXES "ovmf" "qemu" "share")

find_package_handle_standard_args(OVMF DEFAULT_MSG
    OVMF_DISK_IMG)

if(OVMF_FOUND)
    mark_as_advanced(OVMF_ROOT_DIR OVMF_DISK_IMG)

    if(NOT TARGET Ovmf::Ovmf)
        add_library(Ovmf::Ovmf UNKNOWN IMPORTED)
    endif()
endif()

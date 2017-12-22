# - Try to find GNUefi
#
# The following variables are optionally searched for defaults:
#  CONAN_GNU-EFI_ROOT:    Base directory where all GNU efi components are found
#
# The following are set after configuration is done:
#  GNUefi_FOUND
#  GNUEFI_INCLUDE_DIRS    --> GNU-efi's include directories
#  GNUEFI_LIBRARIES       --> GNU-efi's static libraries
#  CMAKE_EXE_LINKER_FLAGS --> prepend parameter for the linker script

include(FindPackageHandleStandardArgs)

if (CONAN_GNU-EFI_ROOT)
    message(STATUS "CONAN_GNU-EFI_ROOT: ${CONAN_GNU-EFI_ROOT}")
    set(CONAN_GNU-EFI_ROOT "" CACHE PATH "Folder contains GNU efi")
endif()

find_path(GNUEFI_INCLUDE_DIR_efi "efi.h"
    PATHS ${CONAN_GNU-EFI_ROOT} "/usr/include"
    PATH_SUFFIXES "efi")

find_path(GNUEFI_INCLUDE_DIR_efiarch "efibind.h"
    PATHS ${CONAN_GNU-EFI_ROOT} "/usr/include"
    PATH_SUFFIXES "efi/${CMAKE_HOST_SYSTEM_PROCESSOR}")

find_path(GNUEFI_INCLUDE_DIR_efiprotocol "efivar.h"
    PATHS ${CONAN_GNU-EFI_ROOT} "/usr/include"
    PATH_SUFFIXES "efi/protocol")

if (NOT MINGW)
    find_file(GNUEFI_LIBRARY_crt0 "crt0-efi-${CMAKE_HOST_SYSTEM_PROCESSOR}.o"
        PATHS ${CONAN_GNU-EFI_ROOT} "/usr/lib"
        PATH_SUFFIXES "lib" "lib64")

    find_file(GNUEFI_LINKER_SCRIPT "elf_${CMAKE_HOST_SYSTEM_PROCESSOR}_efi.lds"
        PATHS ${CONAN_GNU-EFI_ROOT} "/usr/lib"
        PATH_SUFFIXES "lib" "lib64")

    find_library(GNUEFI_LIBRARY_gnuefi "gnuefi"
        PATHS ${CONAN_GNU-EFI_ROOT} "/usr/lib"
        PATH_SUFFIXES "lib" "lib64")
endif()

find_library(GNUEFI_LIBRARY_efi "efi"
    PATHS ${CONAN_GNU-EFI_ROOT} "/usr/lib"
    PATH_SUFFIXES "lib" "lib64")

if (MINGW)
    find_package_handle_standard_args(GNUefi DEFAULT_MSG
        GNUEFI_INCLUDE_DIR_efi
        GNUEFI_INCLUDE_DIR_efiarch
        GNUEFI_INCLUDE_DIR_efiprotocol
        GNUEFI_LIBRARY_efi)
else()
    find_package_handle_standard_args(GNUefi DEFAULT_MSG
        GNUEFI_INCLUDE_DIR_efi
        GNUEFI_INCLUDE_DIR_efiarch
        GNUEFI_INCLUDE_DIR_efiprotocol
        GNUEFI_LIBRARY_efi
        GNUEFI_LIBRARY_gnuefi
        GNUEFI_LIBRARY_crt0
        GNUEFI_LINKER_SCRIPT)
endif()

if(GNUefi_FOUND)
    set(GNUEFI_INCLUDE_DIRS ${GNUEFI_INCLUDE_DIR_efi} ${GNUEFI_INCLUDE_DIR_efiarch} ${GNUEFI_INCLUDE_DIR_efiprotocol})
    set(GNUEFI_LIBRARIES ${GNUEFI_LIBRARY_efi})
    if (NOT MINGW)
        set(GNUEFI_LIBRARIES ${GNUEFI_LIBRARIES} ${GNUEFI_LIBRARY_crt0} ${GNUEFI_LIBRARY_gnuefi})

        message(STATUS "Found GNUefi\n"
            " * include: ${GNUEFI_INCLUDE_DIRS}\n"
            " * libraries: ${GNUEFI_LIBRARIES}\n"
            " * linker script: ${GNUEFI_LINKER_SCRIPT}\n")
        mark_as_advanced(CONAN_GNU-EFI_ROOT
            GNUEFI_INCLUDE_DIR_efi
            GNUEFI_INCLUDE_DIR_efiarch
            GNUEFI_INCLUDE_DIR_efiprotocol
            GNUEFI_LIBRARY_efi
            GNUEFI_LIBRARY_gnuefi
            GNUEFI_LIBRARY_crt0
            GNUEFI_LINKER_SCRIPT)
    else()
        message(STATUS "Found GNUefi\n"
            " * include: ${GNUEFI_INCLUDE_DIRS}\n"
            " * libraries: ${GNUEFI_LIBRARIES}\n")
        mark_as_advanced(CONAN_GNU-EFI_ROOT
            GNUEFI_INCLUDE_DIR_efi
            GNUEFI_INCLUDE_DIR_efiarch
            GNUEFI_INCLUDE_DIR_efiprotocol
            GNUEFI_LIBRARY_efi)
    endif()

    if(NOT TARGET GnuEfi::GnuEfi)
        add_library(GnuEfi::GnuEfi UNKNOWN IMPORTED)
        set_target_properties(GnuEfi::GnuEfi PROPERTIES
            INTERFACE_INCLUDE_DIRECTORIES "${GNUEFI_INCLUDE_DIRS}")
        set_target_properties(GnuEfi::GnuEfi PROPERTIES
            IMPORTED_LOCATION ${GNUEFI_LIBRARIES})

        set(GNUEFI_COMPILE_DEFINITION "-D_GNU_EFI")
        if(CMAKE_BUILD_TYPE MATCHES "Debug")
            set(GNUEFI_COMPILE_DEFINITION "${GNUEFI_COMPILE_DEFINITION} -DEFI_DEBUG")
        endif()

        if (MINGW)
            set_target_properties(GnuEfi::GnuEfi PROPERTIES
                INTERFACE_COMPILE_DEFINITIONS "CONFIG_${CMAKE_HOST_SYSTEM_PROCESSOR} -DGNU_EFI_USE_MS_ABI ${GNUEFI_COMPILE_DEFINITION}")
        else()
            set_target_properties(GnuEfi::GnuEfi PROPERTIES
                INTERFACE_COMPILE_DEFINITIONS "EFI_FUNCTION_WRAPPER ${GNUEFI_COMPILE_DEFINITION}")

            set(CMAKE_EXE_LINKER_FLAGS "-Wl,-T${GNUEFI_LINKER_SCRIPT} ${CMAKE_EXE_LINKER_FLAGS}")
            set(CMAKE_SHARED_LINKER_FLAGS "-Wl,-T${GNUEFI_LINKER_SCRIPT} ${CMAKE_SHARED_LINKER_FLAGS}")
        endif()
    endif()
endif()

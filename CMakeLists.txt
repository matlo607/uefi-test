cmake_minimum_required(VERSION 3.2)
project(uefi-application)

#if(NOT CMAKE_BUILD_TYPE)
#    #set(CMAKE_BUILD_TYPE Release)
#    set(CMAKE_BUILD_TYPE Debug)
#endif(NOT CMAKE_BUILD_TYPE)
#
#if(CMAKE_BUILD_TYPE MATCHES "Debug" OR CMAKE_BUILD_TYPE MATCHES "Release")
#    message(STATUS "CMake build type: ${CMAKE_BUILD_TYPE}")
#else()
#    message(FATAL_ERROR "CMake build type \"${CMAKE_BUILD_TYPE}\" is not supported")
#endif()

message(STATUS "CMAKE_SOURCE_DIR: ${CMAKE_SOURCE_DIR}")

###############
# Conan support
###############

find_program (CONANBIN conan)
if(CONANBIN)
    message (STATUS "conan C++ package manager: installed")
    find_file (CONANFILE "${CMAKE_SOURCE_DIR}/conanfile.txt")
    if (CONANFILE)
        message (STATUS "conanfile.txt: found")
    endif()
endif()

if (EXISTS "${CMAKE_BINARY_DIR}/conanbuildinfo.cmake")
    include(${CMAKE_BINARY_DIR}/conanbuildinfo.cmake)
    message(STATUS "conan_basic_setups()")
    conan_basic_setup()
endif()

if (EXISTS "${CMAKE_SOURCE_DIR}/cmake/Modules/")
    set(CMAKE_MODULE_PATH ${CMAKE_MODULE_PATH} "${CMAKE_SOURCE_DIR}/cmake/Modules/")
endif()

if (NOT CMAKE_RUNTIME_OUTPUT_DIRECTORY)
    set(CMAKE_RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/bin")
endif()
message(STATUS "CMAKE_RUNTIME_OUTPUT_DIRECTORY: ${CMAKE_RUNTIME_OUTPUT_DIRECTORY}")

###############################
# Check compiler's capabilities
###############################

include (CheckCCompilerFlag)

message(STATUS "system name: ${CMAKE_SYSTEM_NAME}")
message(STATUS "system processor: ${CMAKE_SYSTEM_PROCESSOR}")
message(STATUS "host system name: ${CMAKE_HOST_SYSTEM_NAME}")
message(STATUS "host system processor: ${CMAKE_HOST_SYSTEM_PROCESSOR}")

if(CMAKE_COMPILER_IS_GNUCC AND ("${CMAKE_SYSTEM_NAME}" STREQUAL "Windows"))
    set (GNUCC_IS_MINGW true)
elseif(CMAKE_C_COMPILER_ID MATCHES "Clang")
    set (CMAKE_COMPILER_IS_CLANG true)
endif()

if(CMAKE_COMPILER_IS_GNUCC OR CMAKE_COMPILER_IS_CLANG)
    CHECK_C_COMPILER_FLAG("-std=c11" COMPILER_SUPPORTS_C11)
endif()

if(COMPILER_SUPPORTS_C11)
    #set(CMAKE_C_STANDARD "11")
    set (CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -std=c11")
else()
    message(FATAL_ERROR "The compiler ${CMAKE_C_COMPILER} has no C11 support.
    Please use a different C compiler.")
endif()

if(CMAKE_COMPILER_IS_GNUCC OR CMAKE_COMPILER_IS_CLANG)
    CHECK_C_COMPILER_FLAG("-fuse-ld=gold" USE_LINKER_GOLD)
    if(USE_LINKER_GOLD)
        set (CMAKE_SHARED_LINKER_FLAGS "-fuse-ld=gold ${CMAKE_SHARED_LINKER_FLAGS}")
    endif(USE_LINKER_GOLD)

    set (CMAKE_C_COMPILE_FLAGS ${CMAKE_C_COMPILE_FLAGS} -W -Wall -Wextra)
    set (CMAKE_C_COMPILE_FLAGS ${CMAKE_C_COMPILE_FLAGS} -ffreestanding)
    set (CMAKE_C_COMPILE_FLAGS ${CMAKE_C_COMPILE_FLAGS} -mno-red-zone)
    set (CMAKE_C_COMPILE_FLAGS ${CMAKE_C_COMPILE_FLAGS} -fno-stack-protector)
    set (CMAKE_C_COMPILE_FLAGS ${CMAKE_C_COMPILE_FLAGS} -fno-strict-aliasing)
    set (CMAKE_C_COMPILE_FLAGS ${CMAKE_C_COMPILE_FLAGS} -fshort-wchar)

    set (CMAKE_SHARED_LINKER_FLAGS "${CMAKE_SHARED_LINKER_FLAGS} -nostdlib")
    set (CMAKE_SHARED_LINKER_FLAGS "${CMAKE_SHARED_LINKER_FLAGS} -Wl,--no-undefined")
    set (CMAKE_SHARED_LINKER_FLAGS "${CMAKE_SHARED_LINKER_FLAGS} -Wl,--no-allow-shlib-undefined")
    set (CMAKE_SHARED_LINKER_FLAGS "${CMAKE_SHARED_LINKER_FLAGS} -Wl,-Bsymbolic")
    if(MINGW)
        set (CMAKE_SHARED_LINKER_FLAGS "${CMAKE_SHARED_LINKER_FLAGS} -Wl,-dll")
        set (CMAKE_SHARED_LINKER_FLAGS "${CMAKE_SHARED_LINKER_FLAGS} -Wl,--subsystem,10")
        set (CMAKE_SHARED_LINKER_FLAGS "${CMAKE_SHARED_LINKER_FLAGS} -Wl,-eefi_main")
        set (CMAKE_C_STANDARD_LIBRARIES_INIT "")
    else()
        set (CMAKE_SHARED_LINKER_FLAGS "${CMAKE_SHARED_LINKER_FLAGS} -Wl,-znocombreloc")
    endif()
endif()

find_package(OVMF REQUIRED)
if (NOT OVMF_DISK_IMG)
    if (NOT "$ENV{OVMF_ROOT_DIR}" STREQUAL "")
        set(OVMF_ROOT_DIR "$ENV{OVMF_ROOT_DIR}" CACHE INTERNAL "Copied from environment variable")
        set(OVMF_DISK_IMG "${OVMF_ROOT_DIR}/OVMF.fd")
        message(STATUS "OVMF_ROOT_DIR = ${OVMF_ROOT_DIR}")
        message(STATUS "OVMF_DISK_IMG = ${OVMF_DISK_IMG}")
    else()
        message(FATAL_ERROR "Please set OVMF_ROOT_DIR so that we can retrieve OVMF files")
    endif()
endif()

find_package(GNUefi REQUIRED)

set(TARGET_NAME "hello-world")

add_library("${TARGET_NAME}" SHARED
    "${CMAKE_SOURCE_DIR}/src/main.c"
    )

message(STATUS "CMAKE_C_COMPILE_FLAGS=${CMAKE_C_COMPILE_FLAGS}")
target_compile_definitions("${TARGET_NAME}" PUBLIC _DEBUG)
target_compile_options("${TARGET_NAME}" PUBLIC ${CMAKE_C_COMPILE_FLAGS})
target_link_libraries("${TARGET_NAME}" PUBLIC GnuEfi::GnuEfi PRIVATE ${GNUEFI_LIBRARIES})
set_target_properties("${TARGET_NAME}" PROPERTIES
             LIBRARY_OUTPUT_DIRECTORY "${CMAKE_RUNTIME_OUTPUT_DIRECTORY}")

if(MINGW)
    add_custom_command(TARGET "${TARGET_NAME}" POST_BUILD
        COMMAND ${CMAKE_COMMAND} -E copy
        "${CMAKE_RUNTIME_OUTPUT_DIRECTORY}/lib${TARGET_NAME}.dll"
        "${CMAKE_RUNTIME_OUTPUT_DIRECTORY}/${TARGET_NAME}.efi")
else()
    add_custom_command(TARGET "${TARGET_NAME}" POST_BUILD
        COMMAND ${CMAKE_OBJCOPY}
        -j .text
        -j .sdata
        -j .data
        -j .dynamic
        -j .dynsym
        -j .rel
        -j .rela
        -j .reloc
        --target=efi-app-x86_64
        "${CMAKE_RUNTIME_OUTPUT_DIRECTORY}/lib${TARGET_NAME}.so"
        "${CMAKE_RUNTIME_OUTPUT_DIRECTORY}/${TARGET_NAME}.efi")
endif()

#######################
## CREATE DISK IMAGE ##
#######################
set(DISK_NAME "uefi.img")
set(TARGET_DISK_UEFI_QEMU_READY "${DISK_NAME}")
add_custom_target(${TARGET_DISK_UEFI_QEMU_READY}
    COMMAND "${CMAKE_SOURCE_DIR}/scripts/create_disk.bash" -o "${CMAKE_RUNTIME_OUTPUT_DIRECTORY}/${DISK_NAME}"
    "${CMAKE_RUNTIME_OUTPUT_DIRECTORY}/${TARGET_NAME}.efi"
    "${CMAKE_SOURCE_DIR}/efi_scripts/startup.nsh"
    DEPENDS "${TARGET_NAME}"
    WORKING_DIRECTORY ${CMAKE_RUNTIME_OUTPUT_DIRECTORY})

##########
## QEMU ##
##########
set(QEMU_CMD_COMMON qemu-system-x86_64
    -enable-kvm
    -drive if=pflash,format=raw,unit=0,file="${OVMF_DISK_IMG}",readonly=on
    -drive if=ide,format=raw,file=uefi.img)

add_custom_target("run-qemu" COMMAND ${QEMU_CMD_COMMON}
    DEPENDS "${TARGET_DISK_UEFI_QEMU_READY}"
    WORKING_DIRECTORY ${CMAKE_RUNTIME_OUTPUT_DIRECTORY})

add_custom_target("run-qemu-nographic-tty" COMMAND ${QEMU_CMD_COMMON}
    -nographic
    -watchdog ib700 -watchdog-action shutdown
    DEPENDS "${TARGET_DISK_UEFI_QEMU_READY}"
    WORKING_DIRECTORY ${CMAKE_RUNTIME_OUTPUT_DIRECTORY})

add_custom_target("run-qemu-nographic-file" COMMAND ${QEMU_CMD_COMMON}
    -nographic
    -serial file:"/tmp/uefi.log"
    DEPENDS "${TARGET_DISK_UEFI_QEMU_READY}"
    WORKING_DIRECTORY ${CMAKE_RUNTIME_OUTPUT_DIRECTORY})

#add_subdirectory(src)
#add_subdirectory(test)

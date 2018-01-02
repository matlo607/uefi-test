## Installation

### Conan C/C++ package manager

![conan logo](https://www.conan.io/images/logo/jfrog_conan.png)

```bash
pip install conan
```

Create profiles for the available compilers.
```
# GCC is commonly the default compiler on Linux distributions
conan profile new --detect default
# Set properly CC and CXX to point respectively to the C and C++ compilers
CC=clang-5.0 CXX=clang++-5.0 conan profile new --detect clang
CC=x86_64-w64-mingw32-gcc CXX=x86_64-w64-mingw32-g++ conan profile new --detect mingw-w64
```

### Dependencies

See .travis.yml

## Build

Once you have configured the profiles, clone the repository.

```
cd test-uefi
mkdir build-dir && cd build-dir

# Run this script to export the conanfiles
../scripts/conan-bootstrap.bash
# You can list the available profiles you previously configured
conan profile list
# Build the dependencies
conan install --profile=default .. --build=missing
# Run CMake & Make
cmake ..
make
make uefi.img (need root's rights to mount disk on loopback device)
make run-qemu-nographics-tty
```

### MINGW-W64
```
cmake -DCMAKE_TOOLCHAIN_FILE="../cmake/toolchains/mingw64.cmake" ..
```

### CLANG
```
CC=clang-5.0 CXX=clang++-5.0 cmake ..
```

## Debugging

Debugging EFI applications has only been tested with GCC on Linux.
It doesn't work with MINGW.
It wasn't tested with Clang.

### First terminal
Start Qemu with the EFI binary without debug symbols.
It will wait for a tcp connection on port 5555 before running OVMF.
```
make run-qemu-gdbstab
```

### Second terminal
Start socat on port 5555.
```
make debug-tty
...
Image base: 0x<IMAGE_BASE>
```

### Third terminal
Run gdb and load the image with debug symbols to a relocated address
```
make gdb
> efidebug -f binary-debug.efi -b 0x<IMAGE_BASE>
```

## Resources

* [conan.io/Doc](http://docs.conan.io/en/latest/)
* [OS-Dev.org/UEFI](http://wiki.osdev.org/UEFI)
* [OS-Dev.org/Debugging UEFI applications with GDB](http://wiki.osdev.org/Debugging_UEFI_applications_with_GDB)
* [mjg59 - Getting started with UEFI development](https://mjg59.dreamwidth.org/18773.html)

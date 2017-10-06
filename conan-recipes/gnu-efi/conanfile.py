#!/usr/bin/env python3

import os
from conans import ConanFile, tools
from conans.client.build.autotools_environment import AutoToolsBuildEnvironment

class GNUefiConan(ConanFile):
    name = "gnu-efi"
    version = "3.0.6"
    description = """Develop EFI applications for ARM-64, ARM-32, x86_64, IA-64 (IPF),
                     IA-32 (x86), and MIPS platforms using the GNU toolchain and the
                     EFI development environment."""
    url = "https://sourceforge.net/projects/gnu-efi/"
    license = "check in the repo"
    settings = "os", "compiler", "build_type", "arch"
    generators = "cmake"
    sources = "https://git.code.sf.net/p/gnu-efi/code"
    source_dir = "{:s}-{:s}".format(name, version)

    def source(self):
        self.run("git clone {:s} {:s}".format(self.sources, self.source_dir))
        with tools.chdir(self.source_dir):
            self.run("git checkout tags/{:s}".format(self.version))

    def build(self):
        with tools.chdir(self.source_dir):
            env_build = AutoToolsBuildEnvironment(self)
            make_args = list()
            make_args.append("INSTALLROOT={:s}".format(self.package_folder))
            make_args.append("PREFIX=")
            make_args.append("ARCH={:s}".format(str(self.settings.arch)))

            if tools.cross_building(self.settings):
                c_compiler = os.environ['CC']
                prefix = "-".join(c_compiler.split('-')[:-1]) + "-"
                self.output.info("CROSS BUILDING: CC={:s}".format(c_compiler))
                make_args.append("CROSS_COMPILE={:s}".format(prefix))

            # On Windows x86_64, we don't need to build crt0-* and libgnuefi.a
            if self.settings.os == "Windows":
                env_build.make(make_args + ["lib"])
            else:
                env_build.make(make_args)

            env_build.make(make_args + ["install"])

    def package(self):
        # already done by 'make install'
        pass

    def package_info(self):
        self.cpp_info.includedirs = ['include/efi', 'include/efi/' + str(self.settings.arch)]
        self.cpp_info.libdirs = ['lib']

#!/usr/bin/env python3

from conans import ConanFile
from conans import tools

class MinGW64ToolchainConan(ConanFile):
    name = "mingw64-toolchain"
    version = "1.0"
    description = """
                  """
    settings = "os", "compiler", "arch"

    def package_info(self):
        if self.settings.arch == "x86_64":
            mingw64_cc = "x86_64-w64-mingw32-gcc"
            mingw64_cxx = "x86_64-w64-mingw32-g++"
            cc_paths = tools.which(mingw64_cc)
            cxx_paths = tools.which(mingw64_cxx)
            if not cc_paths:
                self.output.error("mingw64 C compiler {:s}: not found"
                                  .format(mingw64_cc))
            else:
                self.env_info.CC = mingw64_cc
                self.output.info("CC={:s}".format(mingw64_cc))

            if not cxx_paths:
                self.output.warn("mingw64 CXX compiler {:s}: not found"
                                 .format(mingw64_cxx))
            else:
                self.env_info.CXX = mingw64_cxx
                self.output.info("CXX={:s}".format(mingw64_cxx))
        else:
            raise Exception("Not supported architecture")

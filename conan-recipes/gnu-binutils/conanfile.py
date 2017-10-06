#!/usr/bin/env python3

from os import path
from conans import ConanFile, tools, AutoToolsBuildEnvironment

class GNUbinutilsConan(ConanFile):
    name = "binutils"
    version = "2.29.1"
    description = """The GNU Binutils are a collection of binary tools.
                     More information are available at https://www.gnu.org/software/binutils/"""
    url = "http://ftp.gnu.org/gnu/binutils/"
    license = "GNU GPL"
    settings = "os", "compiler", "build_type", "arch"
    generators = "cmake"
    sources = "http://ftp.gnu.org/gnu/binutils/"
    source_dir = "{:s}-{:s}".format(name, version)

    def source(self):
        archive_name = self.source_dir + '.tar.gz'
        tools.ftp_download('ftp.gnu.org', 'gnu/binutils/{:s}'.format(archive_name))
        tools.unzip(archive_name)

    def build(self):
        tools.mkdir("build-dir")
        with tools.chdir("build-dir"):
            env_build = AutoToolsBuildEnvironment(self)
            with tools.environment_append(env_build.vars):
                self.run("{:s} --prefix={:s}"
                         .format(path.join('..', self.source_dir, 'configure'),
                                 self.package_folder))
                self.run("make -j {:d}".format(tools.cpu_count()))
                self.run("make install")

    def package(self):
        # already done by 'make install'
        pass

    def package_info(self):
        self.cpp_info.includedirs = ['include']
        self.cpp_info.libdirs = ['lib']
        self.cpp_info.bindirs = ['bin']
        self.env_info.path.append(path.join(self.package_folder, "bin"))

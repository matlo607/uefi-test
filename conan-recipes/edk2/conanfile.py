#!/usr/bin/env python3

from os import path, environ
from conans import ConanFile, tools

class Edk2Conan(ConanFile):
    name = "edk2"
    version = "master"
    description = """A modern, feature-rich, cross-platform firmware development environment
                     for the UEFI and PI specifications from www.uefi.org."""
    url = "https://sourceforge.net/projects/gnu-efi/"
    license = "https://github.com/tianocore/edk2/blob/master/License.txt"
    settings = "os", "compiler", "build_type", "arch"
    generators = "cmake"
    sources = "https://github.com/tianocore/edk2.git"
    source_dir = "{:s}-{:s}".format(name, version)

    def source(self):
        # EDK2@master seems to be broken. OVMF image does not boot anymore.
        # Get an old version so that the EFI shell works.

        # copy the repository but without the history (depth of 1)
        self.run("git clone --depth 1 --branch {:s} {:s} {:s}"
                 .format(self.version, self.sources, self.source_dir))
        #self.run("git clone --branch {:s} {:s} {:s}"
        #         .format(self.version, self.sources, self.source_dir))
        #with tools.chdir(self.source_dir):
        #    self.run("git checkout ba30d5f")


    def build(self):
        with tools.chdir(self.source_dir):
            self.output.info("[EDK2] build BaseTools")
            self.output.info("make -C BaseTools")
            self.run("make -C BaseTools")

            self.output.info("[EDK2] source edksetup.sh")
            self.run("bash -ex -c 'source edksetup.sh'")

            # toolchain settings
            _compiler_name = '{}'.format(self.settings.compiler).upper()
            _compiler_major_ver = '{}'.format(self.settings.compiler.version).split('.')[0]

            _chain_tag = _compiler_name + _compiler_major_ver
            tools.replace_in_file("Conf/target.txt",
                                  "MYTOOLS",
                                  _chain_tag)
            self.output.info("[EDK2] chaintag = {:s}".format(_chain_tag))
            tools.replace_in_file("Conf/target.txt", "IA32", "X64")
            self.output.info("[EDK2] target architecture = X64")

            _workspace = path.join(self.build_folder, self.source_dir)
            _edk_tools_path = path.join(_workspace, 'BaseTools')
            _conf_path = path.join(_workspace, 'Conf')
            _basetools_bin_path = path.join(_edk_tools_path, 'BinWrappers/PosixLike')

            with tools.environment_append({"EDK_TOOLS_PATH": _edk_tools_path,
                                           "CONF_PATH": _conf_path,
                                           "WORKSPACE": _workspace,
                                           "PATH": environ['PATH'] + ':' + _basetools_bin_path
                                          }):
                self.output.info("PATH={:s}".format(environ['PATH']))

                # build MdeModulePkg
                tools.replace_in_file("Conf/target.txt",
                                      "Nt32Pkg/Nt32Pkg.dsc",
                                      "MdeModulePkg/MdeModulePkg.dsc")
                self.output.info("[EDK2] build MdeModulePkg")
                self.run("build")
                # build OvmfPkg
                tools.replace_in_file("Conf/target.txt",
                                      "MdeModulePkg/MdeModulePkg.dsc",
                                      "OvmfPkg/OvmfPkgX64.dsc")
                self.output.info("[EDK2] build OvmfPkgX64")
                self.run("build")

    def package(self):
        _compiler_name = '{}'.format(self.settings.compiler).upper()
        _compiler_major_ver = '{}'.format(self.settings.compiler.version).split('.')[0]
        _ovmf_bin_path = "Build/OvmfX64/DEBUG_{:s}/FV/".format(_compiler_name + _compiler_major_ver)
        self.copy("OVMF_VARS.fd", dst="share", src=path.join(self.source_dir, _ovmf_bin_path))
        self.copy("OVMF_CODE.fd", dst="share", src=path.join(self.source_dir, _ovmf_bin_path))
        self.copy("OVMF.fd", dst="share", src=path.join(self.source_dir, _ovmf_bin_path))

    def package_info(self):
        self.cpp_info.resdirs = ['share']
        self.env_info.OVMF_ROOT_DIR = self.package_folder

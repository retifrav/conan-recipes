import pathlib

from conan import ConanFile
from conan.tools.files import (
    apply_conandata_patches,
    #collect_libs,
    copy,
    export_conandata_patches,
    rm
)
from conan.tools.scm import Git
from conan.tools.cmake import (
    CMake,
    cmake_layout,
    CMakeToolchain
)

class pkgConan(ConanFile):
    name = "zlib"
    version = "1.3.1"

    url = "https://github.com/madler/zlib"
    description = "A massively spiffy yet delicately unobtrusive compression library"
    license = "Zlib"

    user = "decovar"
    channel = "public"

    options = {
        "shared": [True, False]
    }
    default_options = {
        "shared": False
    }

    settings = "os", "compiler", "build_type", "arch"

    def export_sources(self):
        export_conandata_patches(self)

        copy(
            self,
            "*", # or do it with explicit files names in several `copy()` calls
            src=pathlib.Path(self.recipe_folder) / ".." / ".." / "common" / "cmake",
            # trying to "export" additional files directly into `src` folder
            # will prevent `git.clone()` from cloning the repository,
            # because `src` folder will already exist by that moment
            #dst=pathlib.Path(self.export_sources_folder) / "src"
            dst=pathlib.Path(self.export_sources_folder) / "_additional-files"
        )

    def source(self):
        git = Git(self)
        git.clone(
            url="git@github.com:madler/zlib.git",
            hide_url=False,
            target="src"
        )
        git.folder = "src"
        git.checkout("51b7f2abdade71cd9bb0e7a373ef2610ec6f9daf")

        apply_conandata_patches(self)

        # since one cannot export additional files directly to `src`,
        # they need to be copied over via an intermediate location
        copy(
            self,
            "*", # or do it with explicit files names in several `copy()` calls
            src=pathlib.Path(self.export_sources_folder) / "_additional-files",
            dst=pathlib.Path(self.export_sources_folder) / "src"
        )

        # that's how it is with zlib, one is supposed to delete
        # the original header and use the generated header instead
        rm(self, "zconf.h", "src")

    def layout(self):
        cmake_layout(self)

    def generate(self):
        tc = CMakeToolchain(self, generator="Ninja")
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure(
            build_script_folder="src",
            variables={
                "ZLIB_BUILD_EXAMPLES": "NO"
            }
        )
        cmake.build()

    def package(self):
        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        # is this even needed for anything?
        #self.cpp_info.libs = collect_libs(self)

        # do not let Conan try to be smarter than CMake or/and maintainer,
        # otherwise it will generate some bizarre CMake configs of its own
        # based on god knows what
        self.cpp_info.set_property("cmake_find_mode", "none")
        # this is required too, otherwise consumers won't be able to find CMake configs,
        # and obviously if you are installing package configs to a different path,
        # then you will need to replace `share` with whichever you are using
        self.cpp_info.builddirs.append("share")


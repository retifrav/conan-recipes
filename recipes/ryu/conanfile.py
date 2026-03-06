import pathlib

from conan import ConanFile
from conan.tools.files import (
    apply_conandata_patches,
    copy,
    export_conandata_patches
)
from conan.tools.scm import Git
from conan.tools.cmake import (
    CMake,
    cmake_layout,
    CMakeToolchain
)

class pkgConan(ConanFile):
    name = "ryu"
    version = "2024.2.19"

    url = "https://github.com/ulfjack/ryu"
    description = "Converts floating point numbers to decimal strings"
    license = "Apache-2.0 OR BSL-1.0"

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
            "Config.cmake.in",
            src=pathlib.Path(self.recipe_folder) / ".." / ".." / "common" / "cmake",
            dst=pathlib.Path(self.export_sources_folder) / "_additional-files"
        )

    #def config_options(self):
    #    if self.settings.os == "Windows" and self.options.shared:
    #        # setting it to `False` has no effect here (and is not allowed in `configure()`),
    #        # as it will still build SHARED with `-o *:shared=True`, so apparently one must
    #        # delete the `shared` option (here too? And then also) in `configure()`
    #        # (and hardcode `-DBUILD_SHARED_LIBS=0`?)
    #        #self.options.shared = False
    #        del self.options.shared

    def configure(self):
        if self.settings.os == "Windows" and self.options.shared:
            # does not export symbols for making a DLL
            self.options.rm_safe("shared")

    def layout(self):
        cmake_layout(self)

    def source(self):
        git = Git(self)
        git.clone(
            url="git@github.com:ulfjack/ryu.git",
            hide_url=False,
            target="src"
        )
        git.folder = "src"
        git.checkout("1264a946ba66eab320e927bfd2362e0c8580c42f")

        apply_conandata_patches(self)

        copy(
            self,
            "*",
            src=pathlib.Path(self.export_sources_folder) / "_additional-files",
            dst=pathlib.Path(self.export_sources_folder) / "src"
        )

    def generate(self):
        tc = CMakeToolchain(self, generator="Ninja")
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure(
            build_script_folder="src"
        )
        cmake.build()

    def package(self):
        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        self.cpp_info.set_property("cmake_find_mode", "none")
        self.cpp_info.builddirs.append("share")

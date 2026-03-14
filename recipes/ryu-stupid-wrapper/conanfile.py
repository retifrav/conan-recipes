import pathlib

from conan import ConanFile
from conan.tools.files import copy
from conan.tools.cmake import (
    CMake,
    cmake_layout,
    CMakeToolchain
)

class pkgConan(ConanFile):
    name = "ryu-stupid-wrapper"
    version = "2026.3.12"

    description = "A pointless package made merely for testing Conan peculiarities"
    license = "GPL-3.0-or-later"

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
        copy(
            self,
            "*",
            src=pathlib.Path(self.recipe_folder) / "src",
            dst=pathlib.Path(self.export_sources_folder) / "src"
        )

    def requirements(self):
        self.requires(
            "ryu/2024.2.19@decovar/public",
            no_skip=(
                self.settings.os == "Windows"
                and
                self.options.shared
            )
        )

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
                "THINGY_VERSION": self.version
            }
        )
        cmake.build()

    def package(self):
        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        self.cpp_info.set_property("cmake_find_mode", "none")
        self.cpp_info.builddirs.append("share")

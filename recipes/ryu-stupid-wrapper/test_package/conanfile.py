import os

from conan import ConanFile
from conan.tools.cmake import (
    CMake,
    cmake_layout,
    CMakeToolchain
)
from conan.tools.build import can_run

class testConan(ConanFile):
    settings = "os", "compiler", "build_type", "arch"

    def requirements(self):
        self.requires(self.tested_reference_str)

    def generate(self):
        tc = CMakeToolchain(self, generator="Ninja")
        tc.user_presets_path = False
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def layout(self):
        cmake_layout(self)

    def test(self):
        if can_run(self):
            cmd = "tst"
            # with non-Ninja generators executable might be in a subfolder, which is/should be
            # stored in `self.cpp.build.bindir` value, but the fucking thing has the value
            # at all times (or at least that is the case on Windows), so even if you have set
            # Ninja generator, `self.cpp.build.bindir` will still contain `Debug`/`Release` values,
            # which will never exist, so this "joined" path will be doomed to fail
            if os.path.isdir(self.cpp.build.bindir):
                cmd = os.path.join(self.cpp.build.bindir, "tst")
            self.run(cmd, env="conanrun")

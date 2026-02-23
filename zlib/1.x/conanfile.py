from conans import ConanFile
from conan.tools.files import (
    apply_conandata_patches,
    collect_libs,
    export_conandata_patches,
    get,
    rm
)
from conan.tools.cmake import (
    CMake,
    cmake_layout,
    CMakeToolchain
)

class zlibConan(ConanFile):
    name = "zlib"
    version = "1.3.1"

    scm = {
        "type": "git",
        "url": "git@github.com:madler/zlib.git",
        "revision": "51b7f2abdade71cd9bb0e7a373ef2610ec6f9daf"
    }

    license = "http://zlib.net/zlib_license.html"
    author = name
    url = "https://github.com/madler/zlib"
    description = "A massively spiffy yet delicately unobtrusive compression library"

    settings = "os", "compiler", "build_type", "arch"

    user = "some"
    channel = "public"

    def export_sources(self):
        export_conandata_patches(self)
        self.copy(
            "*",
            src=f"{self.recipe_folder}/../../_cmake"
        )

    def source(self):
        # if you'll want to download snapshot archives (using URLs from `conandata.yml`)
        # instead of cloning Git repositories, then uncomment this and comment the `scm` thing above
        #get(
        #    self,
        #    **self.conan_data["sources"][self.version],
        #    strip_root=True
        #)

        # if you'd like to check that it did try to use the patches from `conandata.yml`
        #patches = self.conan_data["patches"][self.version]
        apply_conandata_patches(self)
        # that's how it is with zlib, one is supposed to delete this one
        # and use the generated header instead
        rm(self, "zconf.h", ".")

    def layout(self):
        cmake_layout(self)

    def generate(self):
        tc = CMakeToolchain(self, generator="Ninja")
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure(
            variables={
                "ZLIB_BUILD_EXAMPLES": "NO"
            }
        )
        cmake.build()

    def package(self):
        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        self.cpp_info.libs = collect_libs(self)

from conan import ConanFile
from conan.tools.files import (
    apply_conandata_patches,
    collect_libs,
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

class zlibConan(ConanFile):
    name = "zlib"
    version = "1.3.1"

    license = "http://zlib.net/zlib_license.html"
    author = name
    url = "https://github.com/madler/zlib"
    description = "A massively spiffy yet delicately unobtrusive compression library"

    user = "some"
    channel = "public"

    settings = "os", "compiler", "build_type", "arch"

    def export_sources(self):
        # the paths in `conandata.yml` might need to be adjusted, but anyway, don't use that,
        # as exporting patches is supposed to be done with `export_conandata_patches()`
        #copy(
        #    self,
        #    "*.patch",
        #    src=f"{self.recipe_folder}/../patches/{self.version}",
        #    dst=f"{self.export_sources_folder}/patches"
        #)
        export_conandata_patches(self)

        copy(
            self,
            "*", # or do it with explicit files names in several `copy()` calls
            src=f"{self.recipe_folder}/../../_cmake",
            # trying to "export" additional files directly into `src` folder
            # will prevent `git.clone()` from cloning the repository,
            # because `src` folder will already exist by that moment
            #dst=f"{self.export_sources_folder}/src"
            dst=self.export_sources_folder
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
            self.export_sources_folder,
            f"{self.export_sources_folder}/src"
        )
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
        self.cpp_info.libs = collect_libs(self)

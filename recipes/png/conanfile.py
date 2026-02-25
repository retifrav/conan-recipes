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

class pngConan(ConanFile):
    name = "png"
    version = "1.6.53"

    url = "https://libpng.sourceforge.io/"
    description = "PNG reference library"
    license = "libpng-2.0"

    user = "decovar"
    channel = "public"

    options = {
        "shared": [True, False]
    }
    default_options = {
        "shared": False
    }

    settings = "os", "compiler", "build_type", "arch"

    def requirements(self):
        self.requires("zlib/1.3.1@decovar/public")

    def export_sources(self):
        export_conandata_patches(self)

        copy(
            self,
            "Installing.cmake",
            src=f"{self.recipe_folder}/../../common/cmake",
            dst=f"{self.export_sources_folder}/_additional-files",
        )
        copy(
            self,
            "Config.cmake.in",
            src=self.recipe_folder,
            dst=f"{self.export_sources_folder}/_additional-files",
        )

    def source(self):
        git = Git(self)
        git.clone(
            url="git@github.com:pnggroup/libpng.git",
            hide_url=False,
            target="src"
        )
        git.folder = "src"
        git.checkout("4e3f57d50f552841550a36eabbb3fbcecacb7750")

        apply_conandata_patches(self)

        copy(
            self,
            "*",
            src=f"{self.export_sources_folder}/_additional-files",
            dst=f"{self.export_sources_folder}/src"
        )

    def layout(self):
        cmake_layout(self)

    def generate(self):
        tc = CMakeToolchain(self, generator="Ninja")
        tc.generate()

    def build(self):
        cmakeConfigurationVariables = {
            "PNG_TESTS": 0,
            "PNG_TOOLS": 0
        }

        PNG_STATIC = 1
        PNG_SHARED = 0
        if self.options["shared"] is True:
            PNG_STATIC = 0
            PNG_SHARED = 1

        cmakeConfigurationVariables["PNG_STATIC"] = PNG_STATIC
        cmakeConfigurationVariables["PNG_SHARED"] = PNG_SHARED

        if self.settings.os == "iOS":
            cmakeConfigurationVariables["PNG_HARDWARE_OPTIMIZATIONS"] = 0

        if self.settings.os == "Android":
            cmakeConfigurationVariables["ld-version-script"] = 0

            # there is no `armv7a` architecture in https://docs.conan.io/2/reference/config_files/settings.html#settings-yml,
            # so maybe it should be `startswith("armv7")` instead?
            if self.settings.arch == "armv7a":
                cmakeConfigurationVariables["PNG_ARM_NEON"] = "check"

        cmake = CMake(self)
        cmake.configure(
            build_script_folder="src",
            variables=cmakeConfigurationVariables
        )
        cmake.build()

    def package(self):
        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        self.cpp_info.set_property("cmake_find_mode", "none")
        self.cpp_info.builddirs.append("share")

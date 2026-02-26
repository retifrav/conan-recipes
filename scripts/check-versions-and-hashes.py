import logging
from datetime import datetime
import pathlib
import argparse
import sys
import subprocess
import json
import re
import pandas
from pandera import pandas as pandera
from tabulate import tabulate
from colorama import Fore, Style

import typing

loggingLevel: int = logging.INFO
loggingFormat: str = "[%(levelname)s] %(message)s"

argParser = argparse.ArgumentParser(
    prog="check-versions-and-hashes",
    description="".join((
        "-= %(prog)s =-\n",
        "Verifies currently stated recipe versions ",
        "and their rev-parse hashes.\n\n",
        f"Copyright (C) 2026-{datetime.now().year} ",
        "Declaration of VAR\n",
        "License: GPLv3"
    )),
    formatter_class=argparse.RawDescriptionHelpFormatter,
    allow_abbrev=False
)
argParser.add_argument(
    "repositoryPath",
    type=pathlib.Path,
    nargs="?",
    default=pathlib.Path("."),
    metavar="/path/to/conan-recipes/",
    help="path to the repository with Conan recipes"
)
argParser.add_argument(
    "--debug",
    action='store_true',
    help="enable debug/dev mode (default: %(default)s)"
)
cliArgs = argParser.parse_args()

repositoryPath: pathlib.Path = cliArgs.repositoryPath
debugMode: bool = cliArgs.debug

if debugMode:
    loggingLevel = logging.DEBUG
    # 8 is the length of "CRITICAL" - the longest log level name
    loggingFormat = "%(asctime)s | %(levelname)-8s | %(message)s"

logging.basicConfig(
    format=loggingFormat,
    level=loggingLevel,
    stream=sys.stdout
)

logging.debug(f"CLI arguments: {cliArgs}")
logging.debug("-")

versionRegEx = re.compile(r"version = \"(\d+\.\d+\.\d+)\"")
recipeVersionRegEx = re.compile(r"recipe_version = (\d+)")

def getRevParseHash(
    pathToRepository: pathlib.Path,
    commitHash: str,
    pathInRepository: str
) -> str:
    logging.debug(
        f"- getting rev-parse hash value of [{pathInRepository}]"
    )
    cmdResult = subprocess.run(
        [
            "git",
            "-C",
            pathToRepository.as_posix(),
            "rev-parse",
            f"{commitHash}:{pathInRepository}"
        ],
        # check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )
    if cmdResult.returncode != 0:
        logging.error(
            "".join((
                f"The command was: {' '.join(cmdResult.args)}\n",
                f"Output: {cmdResult.stdout.strip()}"
            ))
        )
        raise OSError(
            "Failed to get rev-parse hash"
        )
    else:
        revParsedHash = cmdResult.stdout.strip()
        if len(revParsedHash) != 40:
            raise ValueError(
                " ".join((
                    "The rev-parsed value doesn't look like",
                    f"a valid Git hash: [{revParsedHash}]",
                    "(must be a string of 40 symbols length",
                    "without newlines)"
                ))
            )
        else:
            logging.debug(f"- {revParsedHash}")
            return revParsedHash


# --- do some checks first

if not repositoryPath.is_dir():
    logging.error(f"Registry path [{repositoryPath.resolve()}] doesn't exist")
    raise SystemExit(2)

recipesPath: pathlib.Path = repositoryPath / "recipes"
if not recipesPath.is_dir():
    logging.error(
        " ".join((
            "There is no [recipes] folder inside the registry,",
            "you might have provided a wrong path to the registry"
        ))
    )
    raise SystemExit(3)

if not (repositoryPath / "versions" / "baseline.json").is_file():
    logging.error(
        " ".join((
            "There is no [versions/baseline.json] file inside the registry,",
            "you might have provided a wrong path to the registry"
        ))
    )
    raise SystemExit(4)

# ---

valueErrorTemplateString = "".join((
    Fore.RED,
    Style.BRIGHT,
    "{errorval}",
    Style.RESET_ALL
))
valueSuccessTemplateString = "".join((
    Fore.GREEN,
    Style.BRIGHT,
    "{successval}",
    Style.RESET_ALL
))

recipesSchema = pandera.DataFrameSchema(
    {
        "version": pandera.Column(str),
        "stated-hash": pandera.Column(str),
        "actual-hash": pandera.Column(str)
    },
    index=pandera.Index(str, unique=True),
    strict=True,
    coerce=False
)

recipes: pandas.DataFrame = pandas.DataFrame()
problematicRecipes: typing.Set[str] = set()

for p in sorted([p.name for p in recipesPath.iterdir() if p.is_dir()]):
    version: typing.Optional[str] = None
    statedHash: typing.Optional[str] = None
    actualHash: typing.Optional[str] = None
    recipeVersion: int = 0

    logging.debug(f"Processing recipe [{p}]")

    conanfile: pathlib.Path = recipesPath / p / "conanfile.py"
    if not conanfile.is_file():
        problematicRecipes.add(p)
        logging.error(f"Recipe [{p}] has no conanfile")
    else:
        conanfileContent: typing.Dict[str, typing.Any] = {}
        with open(conanfile, "r") as f:
            conanfileContent = f.read()

            searchResultVersion = versionRegEx.search(conanfileContent)
            if searchResultVersion: # and len(searchResultVersion.groups()) > 0:
                version = searchResultVersion.group(1)
                logging.debug(f"- found version value: {version}")
            else:
                problematicRecipes.add(p)
                logging.error("Could not find a version value")

            searchResultRecipeVersion = recipeVersionRegEx.search(conanfileContent)
            if searchResultRecipeVersion: # and len(searchResultRecipeVersion.groups()) > 0:
                recipeVersion = int(searchResultRecipeVersion.group(1))
                logging.debug(f"- also found recipe version value: {recipeVersion}")

    if version is not None:
        versionsFile: pathlib.Path = (
            repositoryPath / "versions" / f"{p[0]}-" / f"{p}.json"
        )
        if not versionsFile.is_file():
            problematicRecipes.add(p)
            logging.error(f"Recipe [{p}] has no versions file")
        else:
            versionsFileContent: typing.Dict[str, typing.Any] = {}
            with open(versionsFile, "r") as f:
                versionsFileContent = json.load(f)

            for v in versionsFileContent["versions"]:
                versionsFileVersion: str = v.get("version")
                versionsFilerecipeVersion: typing.Optional[int] = 0
                foundMatchingVersion: bool = False
                if versionsFileVersion is None:
                    logging.warning(
                        " ".join((
                            f"Recipe [{p}] is missing one of the version values",
                            "in its versions file"
                        ))
                    )
                else:
                    versionsFilerecipeVersion = v.get("recipe-version", 0)
                if (
                    version == versionsFileVersion
                    and
                    recipeVersion == versionsFilerecipeVersion
                ):
                    foundMatchingVersion = True

                    # stated hash is read from the recipe versions file
                    statedHash = v.get("git-tree", statedHash)

                    # actual hash is calculated with a bare `git rev-parse`
                    try:
                        actualHash = getRevParseHash(
                            repositoryPath,
                            "HEAD",
                            f"recipes/{p}"
                        )
                        # both stated and actual hash values can be None,
                        # so comparing them not only will be useless
                        # but also incorrect, as None == None
                        if actualHash is None:
                            problematicRecipes.add(p)
                        elif (
                            actualHash != statedHash
                        ):
                            problematicRecipes.add(p)
                            actualHash = valueErrorTemplateString.format(
                                errorval=actualHash
                            )
                    except Exception as ex:
                        problematicRecipes.add(p)
                        logging.error(ex)

                    break
            if not foundMatchingVersion:
                problematicRecipes.add(p)
                logging.error(
                    " ".join((
                        f"Version [{version}#{recipeVersion}] for the recipe",
                        f"[{p}] is not present in its versions file"
                    ))
                )

    if version is not None and recipeVersion != 0:
        version = f"{version}#{recipeVersion}"
    recipe: pandas.DataFrame = pandas.DataFrame(
        {
            "version": (
                f"{Style.DIM}{version}{Style.RESET_ALL}"
                if version is not None
                else valueErrorTemplateString.format(
                    errorval="could not get version"
                )
            ),
            "stated-hash": (
                f"{Style.DIM}{statedHash}{Style.RESET_ALL}"
                if statedHash is not None
                else valueErrorTemplateString.format(
                    errorval="could not get stated hash"
                )
            ),
            "actual-hash": (
                valueSuccessTemplateString.format(
                    successval=actualHash
                )
                if actualHash is not None
                else valueErrorTemplateString.format(
                    errorval="could not get actual hash"
                )
            )
        },
        index=[f"{Style.DIM}{p}{Style.RESET_ALL}"]
    )
    recipes = pandas.concat([recipes, recipe])

recipesSchema.validate(recipes)

print(
    tabulate(
        recipes,
        headers=[
            f"{Style.DIM}{header.replace('-', ' ')}{Style.RESET_ALL}"
            for header
            in recipes.columns.values.tolist()
        ],
        tablefmt="psql",
        floatfmt="g"
    )
)

problematicRecipesCnt: int = len(problematicRecipes)
if problematicRecipesCnt > 0:
    print(
        "".join((
            f"Problematic recipes (total {problematicRecipesCnt}): ",
            ", ".join(
                [
                    f"{Fore.RED}{p}{Style.RESET_ALL}"
                    for p in sorted(problematicRecipes)
                ]
            )
        ))
    )
    raise SystemExit(1)

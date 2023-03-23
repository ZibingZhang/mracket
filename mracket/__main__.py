import argparse
import json
import logging
import os
import shutil
import sys
import traceback

from mracket import runner
from mracket.mutation import generator, mutator
from mracket.runner import logger


def parse_arguments() -> argparse.Namespace:
    parser = build_parser()
    arguments = parser.parse_args()
    if arguments.output is None:
        arguments.output = os.path.join(
            os.getcwd(), f"{os.path.splitext(os.path.basename(arguments.filepath))[0]}-analysis.json"
        )
    if arguments.verbose:
        logger.LOGGER.setLevel(logging.DEBUG)
    return arguments


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("filepath")
    parser.add_argument("-c", "--config", required=True)
    parser.add_argument("-o", "--output", default=None)
    parser.add_argument("-f", "--force", action="store_true", default=False)
    parser.add_argument("-v", "--verbose", action="store_true", default=False)
    return parser


def check_preconditions(arguments: argparse.Namespace) -> None:
    if not os.path.isfile(arguments.filepath):
        raise FileNotFoundError(f"Input file not found: {arguments.filepath}")
    if not os.path.isfile(arguments.config):
        raise FileNotFoundError(f"Config file not found: {arguments.config}")
    if not arguments.force and os.path.exists(arguments.output):
        raise FileExistsError(f"Output file already exists: {arguments.output}")
    if shutil.which("racket") is None:
        raise FileNotFoundError("Cannot find the Racket executable")


def build_mutator(arguments: argparse.Namespace) -> mutator.Mutator:
    with open(arguments.config) as f:
        config = json.load(f)
    generators: list[generator.MutationGenerator] = []
    for generator_config in config["generators"]:
        if generator_config["type"] == "procedure replacement":
            generators.append(generator.ProcedureReplacement(generator_config["replacements"]))
        elif generator_config["type"] == "procedure application replacement":
            generators.append(generator.ProcedureApplicationReplacement(generator_config["replacements"]))
        # TODO: raise an error
    return mutator.Mutator(generators)


def build_runner(arguments: argparse.Namespace, mutator_: mutator.Mutator) -> runner.Runner:
    return runner.Runner(mutator_, arguments.filepath)


if __name__ == "__main__":
    try:
        arguments = parse_arguments()
        check_preconditions(arguments)
        mutator_ = build_mutator(arguments)
        runner_ = build_runner(arguments, mutator_)
        runner_.run()
        result_dict = runner_.result.to_dict()
        logger.LOGGER.debug("Writing analysis to file")
        with open(arguments.output, mode="w", encoding="utf-8") as f:
            f.write(json.dumps(result_dict, indent=2))
    except (FileExistsError, FileNotFoundError) as e:
        logger.LOGGER.debug(traceback.format_exc())
        logger.LOGGER.info(e)
        sys.exit(1)
    except BaseException as e:
        logger.LOGGER.debug(traceback.format_exc())
        logger.LOGGER.info(e)
        sys.exit(2)

"""
This module shows an example of developing a cli with `typer`
Learn more [here](https://typer.tiangolo.com/tutorial/printing/#rich-markup)
"""

import typer
from rich import print
from typing import Annotated
from bci.ui.cli import cli as ui_cli

import os
import logging
logger = logging.getLogger(__name__)

_PROJECT_NAME = os.environ["PROJECT_NAME"]

# adding command
cli = typer.Typer(no_args_is_help=True)
cli.add_typer(typer_instance=ui_cli, name="ui")

@cli.command()
def command_1():
    """
    This is the default command. You can find this command in `src/bci/cli.py`.
    """
    logger.debug("Calling `command_1`")
    print(f"Welcome to {_PROJECT_NAME}")

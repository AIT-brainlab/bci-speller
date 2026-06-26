from dotenv import load_dotenv
from pathlib import Path


_ENVFILE:Path = Path(".env")
load_dotenv(dotenv_path=_ENVFILE)


# We do this to load the logger (which will config the logger for this module)
import project.logger # type: ignore

# This is how you do logging
import logging
logging.debug("App start")

# Start loading modules
from project.cli import cli # typer: ignore



"""Top-level package for shaberookie."""

from importlib import metadata

__all__ = ["__version__"]


def __version__() -> str:
    """Return the current package version."""
    try:
        return metadata.version("shaberookie")
    except metadata.PackageNotFoundError:
        return "0.0.0"
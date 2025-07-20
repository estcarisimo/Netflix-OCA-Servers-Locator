"""
Main entry point for Netflix OCA Locator.

This module serves as the entry point when running the package
as a module with `python -m netflix_oca_locator`.
"""

from .cli.interface import app

if __name__ == "__main__":
    app()

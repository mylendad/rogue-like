"""Точка входа curses-игры."""

import curses

from datalayer.json_storage import JsonProgressStorage
from presentation.app import run


def main() -> None:
    curses.wrapper(run, storage=JsonProgressStorage())


if __name__ == "__main__":
    main()

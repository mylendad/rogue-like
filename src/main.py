"""Точка входа curses-игры."""

import curses

from presentation.app import run


def main() -> None:
    curses.wrapper(run)


if __name__ == "__main__":
    main()

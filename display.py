import curses

import requests

ORIENTATIONS = [
    (('702', '698', '696', '662')),
    (
        ('831-U', '689-U'),
        ('831-L', '689-L')
    )
]

screen = curses.initscr()

screen.addstr('hey whats up')
screen.refresh()

curses.napms(2000)

screen.clear()
screen.refresh()

curses.napms(2000)
curses.endwin()

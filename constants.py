#!/usr/bin/env python
# encoding=utf-8

# author        : seongcheol jeon
# created date  : 2024.03.01
# modified date : 2024.03.01
# description   : 

import typing

from PySide2 import QtWidgets


class Constant:
    # read-only로 만들기 위함.
    __slots__ = ()
    # bit index
    RUNNING:    typing.Final[int] = 0x01
    WAITING:    typing.Final[int] = 0x02
    STOPPED:    typing.Final[int] = 0x04
    ERROR:      typing.Final[int] = 0x08
    STARTED:    typing.Final[int] = 0x10
    FINISHED:   typing.Final[int] = 0x20


Constant = Constant()


class Color:
    status = {
        Constant.RUNNING: '#34eb62',
        Constant.WAITING: '#ebcc34',
        Constant.FINISHED: '#8000ff',
        Constant.STOPPED: '#1c51ff',
        Constant.ERROR: '#eb4034'
    }

    @staticmethod
    def set_color_progressbar(progress: QtWidgets.QProgressBar, color: str):
        progress.setStyleSheet(
            '''
            QProgressBar {
                text-align: center;
                height: 15px;
            }

            QProgressBar::chunk {
                background-color: %s;
                width: 10px;
                margin: 1px;
            }
            ''' % color
        )


if __name__ == '__main__':
    pass

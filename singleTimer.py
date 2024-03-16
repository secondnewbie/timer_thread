#!/usr/bin/env python
# -*- coding: utf-8 -*-

# author        : Seongcheol Jeon
# created date  : 2024.02.15
# modified date : 2024.02.15
# description   :

import sys
import uuid
import typing
import pathlib
import importlib

import qdarktheme
from pydantic import BaseModel
from PySide2 import QtWidgets, QtGui, QtCore

from resources.ui import timer_ui
from libs.system import library as sys_lib
from libs.qt import library as qt_lib
from libs.qt import stylesheet
from libs.algorithm.library import BitMask
from constants import Constant, Color

importlib.reload(timer_ui)
importlib.reload(sys_lib)
importlib.reload(qt_lib)
importlib.reload(stylesheet)


# data class
class Data(BaseModel):
    # seconds
    sec: int
    ste: int
    accum_num: int
    ratio: float
    jid: str
    msg: str = ''


class KillThreadException(Exception): ...


class Signals(QtCore.QObject):
    sig_data = QtCore.Signal(Data)
    changed_link = QtCore.Signal(str, int)


class WorkThread(QtCore.QThread):
    def __init__(self, jid, parent=None):
        super().__init__(parent)
        self.__jid: str = jid
        self.__signals: Signals = Signals()
        self.__bitfield: BitMask = BitMask()
        self.__total_num: int = 0
        self.__condition = QtCore.QWaitCondition()
        self.__mutex = QtCore.QMutex()

        # init
        self.__bitfield.activate(Constant.STOPPED)

    @property
    def signals(self):
        return self.__signals

    @property
    def bitfield(self):
        return self.__bitfield

    def resume(self):
        self.__condition.wakeAll()

    def run(self):
        num = 0
        ratio = 0
        seconds = 0
        self.signals.sig_data.emit(
            Data(sec=-1, ste=Constant.STARTED, accum_num=-1, ratio=-1, jid=self.__jid, msg='Started...'))
        try:
            while num <= self.__total_num:
                seconds = self.__total_num - num
                if self.bitfield.confirm(Constant.STOPPED):
                    raise KillThreadException(f'Killed Thread: {self.__jid}')

                self.__mutex.lock()
                if self.bitfield.confirm(Constant.WAITING):
                    self.signals.sig_data.emit(Data(sec=seconds, ste=Constant.RUNNING,
                                                    accum_num=num, ratio=ratio, jid=self.__jid, msg='Waiting...'))
                    self.__condition.wait(self.__mutex)
                self.__mutex.unlock()

                try:
                    ratio = int((num / self.__total_num) * 100)
                except ZeroDivisionError as err:
                    ratio = 0
                self.signals.sig_data.emit(Data(sec=seconds, ste=Constant.RUNNING,
                                                accum_num=num, ratio=ratio, jid=self.__jid, msg='Running...'))
                self.sleep(1)
                num += 1
        except KillThreadException as err:
            self.set_ste_stopped()
            self.signals.sig_data.emit(Data(sec=seconds, ste=Constant.STOPPED,
                                            accum_num=num, ratio=ratio, jid=self.__jid, msg='Stopped...'))
            sys.stderr.write(str(err) + '\n')
        except Exception as err:
            self.set_ste_error()
            self.signals.sig_data.emit(Data(sec=seconds, ste=Constant.ERROR,
                                            accum_num=num, ratio=ratio, jid=self.__jid, msg='Error...' + str(err)))
            sys.stderr.write(str(err) + '\n')
        else:
            self.set_ste_finished()
            self.signals.sig_data.emit(Data(sec=seconds, ste=Constant.FINISHED,
                                            accum_num=num, ratio=ratio, jid=self.__jid, msg='Finished...'))

    def stop(self):
        self.bitfield.activate(Constant.STOPPED)
        if self.bitfield.confirm(Constant.WAITING):
            self.resume()
        self.set_ste_stopped()
        self.quit()
        self.wait(10000)

    def run_start(self, total_num: int):
        self.set_ste_running()
        self.__total_num = total_num
        self.start()

    def set_ste_started(self) -> None:
        self.bitfield.empty()
        self.bitfield.activate(Constant.STARTED)

    def set_ste_running(self) -> None:
        if self.bitfield.confirm(Constant.RUNNING | Constant.WAITING):
            self.bitfield.toggle(Constant.RUNNING | Constant.WAITING)
        else:
            if not self.bitfield.confirm(Constant.RUNNING):
                self.bitfield.activate(Constant.RUNNING)
                self.bitfield.deactivate(Constant.STARTED | Constant.WAITING | Constant.STOPPED | Constant.FINISHED)

    def set_ste_waiting(self) -> None:
        if self.bitfield.confirm(Constant.RUNNING | Constant.WAITING):
            self.bitfield.toggle(Constant.RUNNING | Constant.WAITING)
        else:
            self.bitfield.activate(Constant.WAITING)
            self.bitfield.deactivate(Constant.RUNNING | Constant.STOPPED | Constant.FINISHED)

    def set_ste_stopped(self) -> None:
        self.bitfield.empty()
        self.bitfield.activate(Constant.STOPPED)

    def set_ste_error(self) -> None:
        self.bitfield.empty()
        self.bitfield.activate(Constant.STOPPED | Constant.ERROR)

    def set_ste_finished(self) -> None:
        self.bitfield.empty()
        self.bitfield.activate(Constant.FINISHED)


class ComboBoxItem(QtWidgets.QListWidgetItem):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.combobox = QtWidgets.QComboBox()
        self.setSizeHint(self.combobox.sizeHint())
        self.__curt_text = ''
        self.__curt_index = -1
        self.combobox.currentIndexChanged.connect(self.slot_combobox_changed)

    def __hash__(self):
        return id(self)

    @QtCore.Slot(int)
    def slot_combobox_changed(self, index):
        self.__curt_text = self.combobox.currentText()
        self.__curt_index = index

    @property
    def current_text(self):
        return self.__curt_text

    @property
    def current_index(self):
        return self.__curt_index


class SingleTimer(QtWidgets.QWidget, timer_ui.Ui_Form__timer):
    CMDS_SET = {
        'Run Firefox':          '/usr/bin/firefox',
        'Run Terminal':         '/usr/bin/gnome-terminal',
        'Run File Browser':     '/usr/bin/nautilus',
        'Run Houdini':          '/opt/hfs19.5/bin/houdini'
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        qdarktheme.setup_theme()
        self.setAutoFillBackground(True)
        self.__jid = uuid.uuid4().hex
        self.signals = Signals()

        # init
        self.__init_set_ui()
        self.__init_set()
        self.__work_thread = WorkThread(jid=self.__jid, parent=self)

        # connections
        self.pushButton__start.clicked.connect(self.slot_start_timer)
        self.pushButton__stop.clicked.connect(self.slot_stop_timer)
        self.__work_thread.signals.sig_data.connect(self.slot_update_ui)
        self.comboBox__link.currentIndexChanged.connect(self.slot_idx_changed_cmb_link)

        self.pushButton__add_item.clicked.connect(self.slot_add_item)
        self.pushButton__del_item.clicked.connect(self.slot_del_item)
        self.listWidget__command.doubleClicked.connect(self.slot_double_clk_item)

    @QtCore.Slot(str, int)
    def slot_idx_changed_cmb_link(self, idx):
        self.signals.changed_link.emit(self.jid, idx)

    def closeEvent(self, event):
        if self.__work_thread.isRunning():
            self.__work_thread.stop()
        event.accept()

    def __init_set_ui(self):
        self.progressBar__remaining.setValue(0)
        self.lcdNumber__remaining.display('00:00:00')
        self.label__jid.setText(self.__jid)
        self.label__status.setText('')
        self.listWidget__command.setAlternatingRowColors(True)
        self.lcdNumber__remaining.setDigitCount(8)

    def __init_set(self):
        self.pushButton__start.setText('Start')
        self.timeEdit__timer.setEnabled(True)

    @property
    def work_thread(self):
        return self.__work_thread

    @property
    def jid(self) -> str:
        return self.__jid

    def append2textbrowser(self, msg) -> None:
        self.textEdit__debug.append(msg)
        self.textEdit__debug.moveCursor(QtGui.QTextCursor.End)

    @QtCore.Slot(QtCore.QModelIndex)
    def slot_double_clk_item(self, item: QtCore.QModelIndex):
        if not item.isValid():
            return
        print(item.data())

    @QtCore.Slot()
    def slot_add_item(self):
        item = ComboBoxItem()
        item.combobox.addItems(list(SingleTimer.CMDS_SET.keys()))
        item.combobox.currentIndexChanged.connect(
            lambda: self.slot_lstwdg_cmb_changed(self.listWidget__command.currentIndex()))

        self.listWidget__command.setSpacing(3)
        self.listWidget__command.addItem(item)
        self.listWidget__command.setItemWidget(item, item.combobox)

    def slot_lstwdg_cmb_changed(self, index: QtCore.QModelIndex):
        if not index.isValid():
            return
        item: ComboBoxItem = self.listWidget__command.itemFromIndex(index)
        print(f'[changed combobox item] : {item.current_text}')

    def slot_del_item(self):
        idx = self.listWidget__command.currentIndex()
        if not idx.isValid():
            return
        item: ComboBoxItem = self.listWidget__command.itemFromIndex(idx)
        if not qt_lib.QtLibs.question_dialog(
                'Remove Run Command', f'Should I remove the {item.current_text} command?', self):
            return
        self.listWidget__command.takeItem(idx.row())

    @QtCore.Slot(Data)
    def slot_update_ui(self, data: Data) -> None:
        if self.__work_thread.bitfield.confirm(Constant.STARTED | Constant.RUNNING):
            if self.__work_thread.bitfield.confirm(Constant.STARTED):
                self.label__status.setText(data.msg)
            elif self.__work_thread.bitfield.confirm(Constant.RUNNING):
                self.progressBar__remaining.setValue(data.ratio)
                Color.set_color_progressbar(self.progressBar__remaining, Color.status.get(Constant.RUNNING))
                self.lcdNumber__remaining.display(SingleTimer.sec2qtime(data.sec).toString())
                self.listWidget__command.setEnabled(False)
        elif self.__work_thread.bitfield.confirm(Constant.WAITING):
            Color.set_color_progressbar(self.progressBar__remaining, Color.status.get(Constant.WAITING))
        elif self.__work_thread.bitfield.confirm(Constant.STOPPED | Constant.ERROR):
            Color.set_color_progressbar(self.progressBar__remaining, Color.status.get(Constant.STOPPED))
            if self.__work_thread.bitfield.confirm(Constant.ERROR):
                Color.set_color_progressbar(self.progressBar__remaining, Color.status.get(Constant.ERROR))
            self.listWidget__command.setEnabled(True)
            self.__init_set()
        elif self.__work_thread.bitfield.confirm(Constant.FINISHED):
            self.listWidget__command.setEnabled(True)
            self.__init_set()
            Color.set_color_progressbar(self.progressBar__remaining, Color.status.get(Constant.FINISHED))
            if data.sec <= 0:
                self.run_commands()
        self.label__status.setText(data.msg)
        if self.__work_thread.bitfield.confirm(Constant.ERROR):
            self.append2textbrowser(f'{data.msg} {int(data.ratio)}%')
        else:
            self.append2textbrowser(f'{data.msg} {int(data.ratio)}%')

    def run_commands(self):
        cmds = self.get_commands()
        if not len(cmds):
            return
        for cmd in cmds:
            sys_lib.System.open_file_using_thread(
                pathlib.Path(SingleTimer.CMDS_SET.get(cmd)), None, False)
            self.append2textbrowser(f'{SingleTimer.CMDS_SET.get(cmd)} 명령 실행!')

    def get_commands(self):
        cnt_items = self.listWidget__command.count()
        return [self.listWidget__command.item(i).current_text for i in range(cnt_items)]

    def is_set_timer(self) -> bool:
        return SingleTimer.qtime2sec(self.timeEdit__timer.time()) > 0

    def slot_start_timer(self):
        if not self.is_set_timer():
            QtWidgets.QMessageBox.warning(self, 'Warning', '타이머 설정을 해야 합니다.')
            return
        if not self.__work_thread.isRunning():
            self.__work_thread.set_ste_started()
            # start
            self.__work_thread.run_start(self.qtime2sec(self.timeEdit__timer.time()))
            self.timeEdit__timer.setEnabled(False)
            if self.__work_thread.bitfield.confirm(Constant.RUNNING | Constant.WAITING):
                self.pushButton__start.setText('Pause')
                if self.__work_thread.bitfield.confirm(Constant.WAITING):
                    self.pushButton__start.setText('Start')
        else:
            self.__work_thread.set_ste_waiting()
            if not self.__work_thread.bitfield.confirm(Constant.WAITING):
                self.__work_thread.resume()
                self.pushButton__start.setText('Pause')
            else:
                self.pushButton__start.setText('Resume')

    def slot_stop_timer(self):
        if self.__work_thread.isRunning():
            self.__work_thread.stop()

    @staticmethod
    def qtime2sec(qtime) -> int:
        h, m, s = qtime.hour(), qtime.minute(), qtime.second()
        total_sec = h * 3600 + m * 60 + s
        return total_sec

    @staticmethod
    def sec2qtime(sec: int) -> QtCore.QTime:
        h, m = divmod(sec, 3600)
        m = m // 60
        s = sec % 60
        return QtCore.QTime(h, m, s)


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    timer = SingleTimer()
    timer.show()
    sys.exit(app.exec_())

#!/usr/bin/env python
# -*- coding: utf-8 -*-

# author        : Seongcheol Jeon
# created date  : 2024.02.28
# modified date : 2024.02.28
# description   :

# HOME WORK
# link (group)
# total progress

import sys
import importlib

from PySide2 import QtWidgets, QtGui, QtCore
from libs.qt import stylesheet, library as qt_lib
from libs.algorithm.library import SingletonBitMask

from constants import Constant, Color
import singleTimer

importlib.reload(singleTimer)


class MultipleTimer(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        w = QtWidgets.QWidget()
        self.__vbox_layout = QtWidgets.QVBoxLayout()
        self.__grid_layout = QtWidgets.QGridLayout()

        # vars
        self.__widget_data = dict()
        self.__menubar = self.menuBar()
        self.__statusbar = self.statusBar()
        self.__total_progress = QtWidgets.QProgressBar()
        self.__total_progress.setValue(30)
        self.__total_progress.setStyleSheet(stylesheet.ProgressBar.ORANGE_PROGRESS_STYLE)
        self.__statusbar.addPermanentWidget(self.__total_progress)
        self.__st_bitfield = SingletonBitMask()
        self.__st_bitfield.empty()

        self.__setup_ui()
        self.__setup_widgets_ui()
        self.__vbox_layout.addLayout(self.__grid_layout)

        w.setLayout(self.__vbox_layout)
        self.setCentralWidget(w)
        qt_lib.QtLibs.center_on_screen(self)

    def closeEvent(self, event):
        for w in self.__widget_data.values():
            w: singleTimer.SingleTimer
            if w.work_thread.isRunning():
                w.work_thread.stop()
        event.accept()

    def __setup_menu_actions(self):
        # menu
        __menu_file = QtWidgets.QMenu('File')
        __menu_help = QtWidgets.QMenu('Help')

        # actions
        self.__action_quit = QtWidgets.QAction('Quit')
        self.__action_about = QtWidgets.QAction('About')

        # action trigger
        self.__action_quit.triggered.connect(self.__slot_act_quit)
        self.__action_about.triggered.connect(self.__slot_act_about)

        # action shortcut
        quit_shortcut_key = QtGui.QKeySequence('Ctrl+Q')
        pref_shortcut_key = QtGui.QKeySequence('Shift+F4')
        self.__action_quit.setShortcut(quit_shortcut_key)

        __menu_file.addAction(self.__action_quit)
        __menu_help.addAction(self.__action_about)

        self.__menubar.addMenu(__menu_file)
        self.__menubar.addMenu(__menu_help)

    def __slot_act_about(self):
        _ = QtWidgets.QMessageBox.information(self, 'Multiple Timer APP', '다중 타이머 실행 어플리케이션')

    def __slot_act_quit(self):
        self.close()

    def __setup_ui(self):
        self.__setup_menu_actions()
        label_cnt = QtWidgets.QLabel('Count Work Threads:')
        self.__spinbox_thread_cnt = QtWidgets.QSpinBox()
        self.__spinbox_thread_cnt.setValue(3)
        self.__spinbox_thread_cnt.valueChanged.connect(self.__slot_spinbox_value_changed)
        # button
        btn_refresh_layout = QtWidgets.QPushButton('Refresh Layout')
        btn_refresh_layout.setStatusTip('WorkThread 개수에 맞춰 레이아웃 갱신')
        btn_refresh_layout.clicked.connect(self.__refresh_layout)

        # 일괄 적용 관련 버튼
        self.__btn_batch_start = QtWidgets.QPushButton('Batch Start')
        self.__btn_batch_start.setIcon(QtGui.QIcon(':/icons/icons/timer-play.png'))
        self.__btn_batch_start.setStyleSheet(stylesheet.PushButton.get_round_style())
        self.__btn_batch_start.clicked.connect(self.__slot_clicked_batch_start)
        self.__btn_batch_stop = QtWidgets.QPushButton('Batch Stop')
        self.__btn_batch_stop.setIcon(QtGui.QIcon(':/icons/icons/stop.png'))
        self.__btn_batch_stop.setStyleSheet(stylesheet.PushButton.get_round_style())
        self.__btn_batch_stop.clicked.connect(self.__slot_clicked_batch_stop)
        hbox_batch_btns = QtWidgets.QHBoxLayout()
        hbox_batch_btns.addWidget(self.__btn_batch_start)
        hbox_batch_btns.addWidget(self.__btn_batch_stop)

        hbox_thread = QtWidgets.QHBoxLayout()
        hbox_thread.addLayout(hbox_batch_btns)
        hbox_thread.addItem(MultipleTimer.get_spacer_item())
        hbox_thread.addWidget(label_cnt)
        hbox_thread.addWidget(self.__spinbox_thread_cnt)
        hbox_thread.addWidget(btn_refresh_layout)
        self.__vbox_layout.addLayout(hbox_thread)

    @QtCore.Slot(int)
    def __slot_clicked_batch_start(self):
        for w in self.__widget_data.values():
            w: singleTimer.SingleTimer
            if not w.is_set_timer():
                QtWidgets.QMessageBox.warning(self, 'Warning', f'{w.jid} 타이머 설정을 해야 합니다.')
                return

        cnt_threads = self.__spinbox_thread_cnt.value()
        if not self.__st_bitfield.confirm(Constant.STARTED):
            if self.__st_bitfield.confirm(Constant.WAITING):
                if not qt_lib.QtLibs.question_dialog(
                        'Batch Start All Threads', f'{cnt_threads}개의 스레드를 일괄적으로 재시작할까요?', self):
                    return
            else:
                if not qt_lib.QtLibs.question_dialog(
                        'Batch Start All Threads', f'{cnt_threads}개의 스레드를 일괄적으로 시작할까요?', self):
                    return
            self.__st_bitfield.activate(Constant.STARTED)
            self.__btn_batch_start.setText('Batch Pause')
            self.__btn_batch_start.setIcon(QtGui.QIcon(':/icons/icons/pause.png'))
        else:
            self.__st_bitfield.toggle(Constant.STARTED | Constant.WAITING)
            if not qt_lib.QtLibs.question_dialog(
                    'Batch Pause All Threads', f'{cnt_threads}개의 스레드를 일괄적으로 일시정지할까요?', self):
                return
            self.__btn_batch_start.setText('Batch Resume')
            self.__btn_batch_start.setIcon(QtGui.QIcon(':/icons/icons/restart.png'))
        for w in self.__widget_data.values():
            w: singleTimer.SingleTimer
            w.slot_start_timer()

    @QtCore.Slot(int)
    def __slot_clicked_batch_stop(self):
        cnt_threads = self.__spinbox_thread_cnt.value()
        if not qt_lib.QtLibs.question_dialog(
                'Batch Stop All Threads', f'{cnt_threads}개의 스레드를 일괄적으로 중지할까요?', self):
            return
        for w in self.__widget_data.values():
            w: singleTimer.SingleTimer
            w.slot_stop_timer()

    def __setup_widgets_ui(self):
        cnt_threads = self.__spinbox_thread_cnt.value()
        for i in range(cnt_threads):
            widget = singleTimer.SingleTimer(parent=self)

            widget.comboBox__link.addItems(list(map(lambda x: chr(x + 65), range(cnt_threads))))

            widget.adjustSize()
            self.__widget_data[widget.jid] = widget
            self.__grid_layout.addWidget(widget, int(i // 3), int(i % 3))

        self.adjustSize()
        self.setMinimumWidth(800)

        self.pro_dict = dict()
        self.combo_dict = dict()
        self.get_combo_link_num()
        self.combo_link_btn()
        self.get_signle_ratio()

    # progress 시그널 연결
    def get_signle_ratio(self):
        for widget in self.__widget_data.values():
            widget.work_thread.signals.sig_data.connect(self.average_progress)

    # total_progress 설정
    @QtCore.Slot(singleTimer.Data)
    def average_progress(self, data):
        # print('id::', data.jid, 'ratio::', data.ratio)
        self.pro_dict[data.jid] = data.ratio
        count = len(self.pro_dict)
        res = 0
        for i, num in self.pro_dict.items():
            res += num
        self.__total_progress.setValue(res//count)

    # combo_link 시그널 연결
    def get_combo_link_num(self):
        for widget in self.__widget_data.values():
            widget.signals.changed_link.connect(self.make_link)

            if widget.comboBox__link.currentIndex() == 0:
                self.combo_dict[widget] = 0

    # combo_link 시그널을 combo_dict으로 제작
    @QtCore.Slot(str, int)
    def make_link(self, wid_id, idx):
        self.combo_dict[self.__widget_data[wid_id]] = idx

    # combo_dict에서 실제로 link된 것만 추려서 filter_dict으로 제작
    @property
    def filter_combo_link(self):
        filter_widget_dict = {}
        for it, idx in enumerate(list(self.combo_dict.values())):
            if list(self.combo_dict.values()).count(idx) > 1:
                filter_widget_dict[list(self.__widget_data.values())[it]] = idx
        return filter_widget_dict

    # combo_link와 관련한 시그널
    def combo_link_btn(self):
        for widget in self.__widget_data.values():
            widget.pushButton__start.clicked.connect(self.set_combo_link_btn_start)
            widget.pushButton__stop.clicked.connect(self.set_combo_link_btn_stop)
            widget.timeEdit__timer.timeChanged.connect(self.set_combo_link_timer)

    # link된 타이머 시간 설정
    def set_combo_link_timer(self):
        sender_widget_timer = self.sender()
        # print('timer', sender_widget_timer)

        for widget in self.__widget_data.values():
            if widget.timeEdit__timer == sender_widget_timer:
                if widget not in self.filter_combo_link:
                    pass
                else:
                    for wid in self.filter_combo_link:
                        if self.filter_combo_link[wid] == self.filter_combo_link[widget]:
                            if wid.timeEdit__timer == sender_widget_timer:
                                pass
                            else:
                                wid.timeEdit__timer.setTime(widget.timeEdit__timer.time())
                    break

    # link된 타이머 start 버튼 연결
    def set_combo_link_btn_start(self):
        sender_widget_btn = self.sender()

        for widget in self.__widget_data.values():
            if widget.pushButton__start == sender_widget_btn:
                if widget not in self.filter_combo_link:
                    pass
                else:
                    for wid in self.filter_combo_link:
                        if self.filter_combo_link[wid] == self.filter_combo_link[widget]:
                            if wid.pushButton__start == sender_widget_btn:
                                pass
                            else:
                                wid.slot_start_timer()

    # link된 타이머 stop 버튼 연결
    def set_combo_link_btn_stop(self):
        sender_widget_btn = self.sender()

        for widget in self.__widget_data.values():
            if widget.pushButton__stop == sender_widget_btn:
                if widget not in self.filter_combo_link:
                    pass
                else:
                    for wid in self.filter_combo_link:
                        if self.filter_combo_link[wid] == self.filter_combo_link[widget]:
                            if wid.pushButton__stop == sender_widget_btn:
                                pass
                            else:
                                wid.slot_stop_timer()

    @staticmethod
    def get_spacer_item() -> QtWidgets.QSpacerItem:
        return QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

    def __refresh_layout(self):
        for w in self.__widget_data.values():
            w: singleTimer.SingleTimer
            if w.work_thread.isRunning():
                w.focusWidget()
                QtWidgets.QMessageBox.warning(
                    self, 'Warning', f'[{w.jid}] thread is running...')
                return

        for i in reversed(range(self.__grid_layout.count())):
            # print(i)
            w = self.__grid_layout.itemAt(i).widget()
            if w is None:
                continue
            w.setParent(None)
            w.deleteLater()

        self.__widget_data.clear()
        self.__setup_widgets_ui()

        self.pro_dict.clear()
        self.combo_dict.clear()
        self.get_combo_link_num()

    @QtCore.Slot(int)
    def __slot_spinbox_value_changed(self, val):
        self.__spinbox_thread_cnt.setValue(min(max(1, val), 12))


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    mt = MultipleTimer()
    mt.show()
    sys.exit(app.exec_())


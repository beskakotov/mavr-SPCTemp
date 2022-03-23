from SPCTemp import FanControl, Temperature
from PyQt5.QtWidgets import *
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QIcon
import sys
from random import randint, random
import pywinusb.hid as hid
from time import sleep, time
from datetime import datetime, date
from os.path import isfile
import pickle
from statistics import median

class TempControlGui(QMainWindow):
    def __init__(self, parent = None):
        QMainWindow.__init__(self, parent)

        self.setWindowTitle('Box temperature control')
        self.setFixedSize(500, 100)

        self.m_Widget = QWidget()
        self.m_Layout = QHBoxLayout()

        self.l_Speed = QLabel("Fan speed:")
        self.l_Speed.setAlignment(Qt.AlignCenter)
        self.l_Speed.setStyleSheet('font-size: 14pt;')
        self.v_Speed = QLCDNumber()
        self.v_Speed.setDigitCount(1)
        self.v_Speed.setFixedSize(50, 50)

        self.speedIcons = [
            QIcon('./ico/1.ico'),
            QIcon('./ico/2.ico'),
            QIcon('./ico/3.ico'),
            QIcon('./ico/4.ico'),
        ]
        
        self.l_Temp = QLabel("Temp (median):")
        self.l_Temp.setAlignment(Qt.AlignCenter)
        self.l_Temp.setStyleSheet('font-size: 14pt;')
        self.v_Temp = QLCDNumber()
        self.v_Temp.setDigitCount(5)
        self.v_Temp.setFixedSize(150, 50)

        self.m_Layout.addWidget(self.l_Speed)
        self.m_Layout.addWidget(self.v_Speed)
        self.m_Layout.addWidget(self.l_Temp)
        self.m_Layout.addWidget(self.v_Temp)

        self.m_Widget.setLayout(self.m_Layout)

        self.setCentralWidget(self.m_Widget)

        self.show()

        self.logname = str(date.today()) + '.tlog'
        self.WaitIter = 0
        self.temppath = 'BM1707.temp'
        self.FAN = FanControl()
        self.FAN.setSpeed(1)
        self.tray_icon = QSystemTrayIcon(self)
        self.v_Speed.display(1)

        self.tray_icon.setIcon(self.speedIcons[self.FAN.Speed-1])
        show_action = QAction("Show", self)
        quit_action = QAction("Exit", self)
        hide_action = QAction("Hide", self)
        show_action.triggered.connect(self.show)
        hide_action.triggered.connect(self.hide)
        quit_action.triggered.connect(qApp.quit)
        tray_menu = QMenu()
        tray_menu.addAction(show_action)
        tray_menu.addAction(hide_action)
        tray_menu.addAction(quit_action)
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

        if isfile(self.logname):
            self.LOG = pickle.load(open(self.logname, 'rb'))
        else:
            self.LOG = []
        self.TempLevels = [-100, 27, 30, 33, 100]
        # Скорость 1: от -101 до  27
        # Скорость 2: от   26 до  30
        # Скорость 3: от   29 до  33
        # Скорость 4: от   32 до 100

        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self._update)
        self.timer.start()
    
    def _update(self):
        self.newlogname = str(date.today())+'.tlog'
        if self.newlogname != self.logname:
            self.LOG = []
            self.logname = str(date.today())+'.tlog'
        self.LOG.append(Temperature(self.getTemperature(), datetime.now()))
        pickle.dump(self.LOG, open(self.logname, 'wb'))
        log_5min = self.getLast5MinLog()
        cur_t = median([i.value for i in log_5min])
        self.v_Temp.display('{:02.2f}'.format(cur_t))

        if self.WaitIter:
            self.WaitIter -= 1
        else:
            if cur_t > self.TempLevels[self.FAN.Speed]:
                self.FAN.speedUp()
                self.v_Speed.display(self.FAN.Speed)
                self.tray_icon.setIcon(self.speedIcons[self.FAN.Speed-1])
                self.tray_icon.showMessage(
                    "Fan speed up",
                    "New speed is {}".format(self.FAN.Speed),
                    QSystemTrayIcon.Information,
                    2000
                    )
            elif cur_t <= self.TempLevels[self.FAN.Speed-1] - 1:
                self.FAN.speedDown()
                self.v_Speed.display(self.FAN.Speed)
                self.tray_icon.setIcon(self.speedIcons[self.FAN.Speed-1])
                self.tray_icon.showMessage(
                    "Fan speed down",
                    "New speed is {}".format(self.FAN.Speed),
                    QSystemTrayIcon.Information,
                    2000
                    )
            if len(log_5min) < 150:
                self.WaitIter = 20
            else:
                self.WaitIter = 60

        self.timer.start()
    def closeEvent(self, event):
        event.ignore()
        self.hide()
        self.tray_icon.showMessage(
            "Super PC Temperature contoller",
            "Application was minimized to Tray",
            QSystemTrayIcon.Information,
            2000
            )

    def getTemperature(self):
        temp = float(open(self.temppath).read().split()[-1].split('=')[1].replace(',', '.'))
        return temp
    
    def getLast5MinLog(self):
        log = []
        curdt = datetime.now()
        for t in self.LOG:
            if (curdt - t.date).total_seconds() < 300:
                log.append(t)
        return log

if __name__ == '__main__':
    app = QApplication(sys.argv)
    gui = TempControlGui()
    app.exec_()
import pywinusb.hid as hid
# from time import sleep, time
# from datetime import datetime, date
# from os.path import isfile
# import pickle
from statistics import median

class FanControl:
    def __init__(self):
        self.Device = hid.HidDeviceFilter(vendor_id=0x16c0).get_devices()[0]
        self.Device.open()
        self.Speed = 1
        self.Report = self.Device.find_feature_reports()[0]

    def setSpeed(self, speed):
        if 1 <= speed <= 4:
            P = 8*(speed - 1)
        else:
            return 'Wrong speed'
        self.Report[4278190080] = [231, P, 0, 0, 0, 0, 0, 0]
        self.Report.send()

    def speedUp(self):
        if 1 <= self.Speed <= 3:
            self.Speed += 1
            self.setSpeed(self.Speed)
        else:
            return 'Max speed'
    
    def speedDown(self):
        if 2 <= self.Speed <= 4:
            self.Speed -= 1
            self.setSpeed(self.Speed)
        else:
            return 'Min speed'

class Temperature:
    def __init__(self, t, d):
        self.value  = t
        self.date   = d
        
    def __repr__(self):
        return '<Temperature class: VALUE: {}, DATE: {}>'.format(self.value, self.date)

class TemperatureControl:
    def __init__(self):
        self.Iteration = 0
        self.FAN = FanControl()
        self.temppath = 'BM1707.temp'
        self.logname = str(date.today()) + '.tlog'
        self.FAN.setSpeed(1)
        self.WaitIter = 0
        self.TempLevels = [-100, 26, 29, 32, 100]
        if isfile(self.logname):
            self.LOG = pickle.load(open(self.logname, 'rb'))
        else:
            self.LOG = []
        
    def getTemperature(self):
        temp = float(open(self.temppath).read().split()[-1].split('=')[1].replace(',', '.'))
        return temp

    def checkTemperature(self):
        log_5min = self.getLast5MinLog()
        print(self.WaitIter, ' '*10, end = '\r')
        if self.WaitIter:
            self.WaitIter -= 1
        else:
            cur_t = median([i.value for i in log_5min])
            print('[{}]'.format(self.Iteration), 'Медианная температура:', cur_t); self.Iteration += 1
            if cur_t > self.TempLevels[self.FAN.Speed]:
                self.FAN.speedUp()
                print('[{}]'.format(self.Iteration), 'Скорость повышена до', self.FAN.Speed); self.Iteration += 1
            elif cur_t <= self.TempLevels[self.FAN.Speed-1] - 1:
                self.FAN.speedDown()
                print('[{}]'.format(self.Iteration), 'Скорость понижена до', self.FAN.Speed); self.Iteration += 1
            if len(log_5min) < 150:
                self.WaitIter = 15
            else:
                self.WaitIter = 30
    
    def getLast5MinLog(self):
        log = []
        curdt = datetime.now()
        for t in self.LOG:
            if (curdt - t.date).total_seconds() < 300:
                log.append(t)
        return log

    def start(self):
        while True:
            start = time()
            self.newlogname = str(date.today())+'.tlog'
            if self.newlogname != self.logname:
                self.LOG = []
                self.logname = str(date.today())+'.tlog'
            self.LOG.append(Temperature(self.getTemperature(), datetime.now()))
            pickle.dump(self.LOG, open(self.logname, 'wb'))
            self.checkTemperature()
            sleep(1)

if __name__ == '__main__':
    MP1707 = TemperatureControl()
    MP1707.start()
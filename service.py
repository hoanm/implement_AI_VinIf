import numpy as np
import pylsl
import random
import time

LSL_ET_NAME                 = "Unity.ExampleStream"
LSL_EEG_DATA_NAME           = "EmotivDataStream-EEG"
LSL_EEG_DATA_QUALITY_NAME   = "EmotivDataStream-EEG-Quality"
LSL_RESULT_NAME             = "HMIResultData"

class ETReceive():
    """docstring for ETReceive"""

    def __init__(self):
        super(ETReceive, self).__init__()
        self.stt = False
        streams = pylsl.resolve_stream()
        for stream in streams:
            if stream.name() == LSL_ET_NAME:
                self.inlet = pylsl.StreamInlet(stream)
                self.stt = True

        if not hasattr(self, 'inlet'):
            print('Không kết nối được với chương trình thu.')

        self.lastSample = None
        self.lSample = []
        self.saving = False

    def update(self):
        try:
            timestamp, sample = None, None
            if self.stt:
                sample, timestamp = self.inlet.pull_sample(timeout=1000 / 30)

            if timestamp is not None:
                sp = sample[0].split(":")
                x, y, _ = sp[0][1:-1].split(",")
                if x != 'none':
                    x, y = float(x), float(y)
                else:
                    x, y = -1, -1
                formatted = [timestamp, x, y, sp[1].strip(), sp[2].strip()]
                self.lastSample = formatted
                if self.saving:
                    self.lSample.append(formatted)
        except Exception as e:
            print(e, "error in inlet ET")
            self.stt = False
        # print("update ET")

    def signalStt(self):
        return self.stt

    def updateSaving(self):
        self.saving = True

    def getSavingData(self):
        return self.lSample


class EEGReceive(object):
    """docstring for ETReceive"""

    def __init__(self, arg):
        super(EEGReceive, self).__init__()
        self.arg = arg
        streams = pylsl.resolve_stream()
        for stream in streams:
            if stream.name() == LSL_EEG_DATA_NAME:
                self.inlet = pylsl.StreamInlet(stream)
            if stream.name() == LSL_EEG_DATA_QUALITY_NAME:
                self.quality_inlet = pylsl.StreamInlet(stream)

        if not hasattr(self, 'inlet'):
            print('Không tìm thấy dữ liệu điện não.')
        if not hasattr(self, 'quality_inlet'):
            print('Không tìm thấy thông tin chất lượng dữ liệu điện não.')

        self.quality = 100
        self.listSaving = []
        self.lData = []
        self.lTimeStamp = []
        self.rcdTime = 0
        self.root = ET.fromstring(self.inlet.info().as_xml())
        self.errorUpdate = 0

    def update(self):
        try:
            samples, timestamps = self.inlet.pull_chunk()
            if len(timestamps) > 0:
                for idx, _ in enumerate(timestamps):
                    self.lData.append(samples[idx])
                    self.lTimeStamp.append(timestamps[idx])
            if len(self.lTimeStamp) > 0:
                self.rcdTime = self.lTimeStamp[-1] - self.lTimeStamp[0]

        except Exception as e:
            # print(e, "Error in inlet EEG Rec: ", self.errorUpdate)
            self.errorUpdate += 1

    def getQuality(self):
        try:
            samples, timestamps = self.quality_inlet.pull_chunk()
            if len(timestamps) > 0:
                self.quality = samples[-1][2]

        except Exception as e:
            print(e, "Error in inlet EEG quality: ")
        return self.quality

    def getSavingData(self):
        numPatch = int(len(self.lTimeStamp) / 128)
        supposedLen = numPatch * 128
        # if len(self.lData) > len(self.lTimeStamp):
        outputData = self.lData[: supposedLen]
        outputTS = self.lTimeStamp[: supposedLen]
        return [outputData, outputTS]

    def getLastRcdSample(self):
        return [self.lData[-1], self.lTimeStamp[-1]]

    def getFirstRcdSample(self):
        return [self.lData[0], self.lTimeStamp[0]]

    def getInfo(self):
        info = self.root[17][1]
        lInfo = []
        for x in info:
            lInfo.append(x[0].text)
        return lInfo

    def getRate(self):
        rate = self.root.find("nominal_srate").text
        return int(float(rate))

class ResultSend(object):
    def __init__(self):
        self.streamInfo = pylsl.StreamInfo(LSL_RESULT_NAME, 'Markers', 1, 0, 'string', 'myuidw43536')
        self.outlet = pylsl.StreamOutlet(self.streamInfo)


    def send_data(self, data):
        self.outlet.push_sample(data)

def AI():
    # TODO: AI algorithm implementation
    rs = int(random.random() * 3) % 10
    return rs

if __name__ == "__main__":
    # ET = ETReceive()
    # EEG = EEGReceive()

    sender = ResultSend()

    i = 1
    while True:
        sender.send_data(str(i%10))
        print("Sent ", str(i%10))
        time.sleep(2)
        i = i + 1
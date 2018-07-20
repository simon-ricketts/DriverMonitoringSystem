from PyQt5 import QtWidgets
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QPixmap
from PIL import Image
from VideoCapture import Device
import datetime
import os
import sys
import dmsGUI
import serial
import time
import requests
import cv2
import operator
import numpy as np
import random

class getSensorDataThread(QThread):
    sensorData = pyqtSignal(str)
    exception = pyqtSignal()

    def __init__(self):
        QThread.__init__(self)

    def __del__(self):
        self.wait()

    def run(self):
        try:
            self.ser = serial.Serial("COM7", 9600)
            time.sleep(2)
            while True:
                self.serialData = str(self.ser.readline().decode('utf8'))
                self.sensorData.emit(self.serialData)
        except serial.SerialException as e:
            print(e)
            self.exception.emit()

    def stop(self):
        self.terminate()
        self.ser.close()
        self.ser = None

class getEmotionDataThread(QThread):
    _url = 'https://westcentralus.api.cognitive.microsoft.com/face/v1.0/detect'
    _key = '6f290054c72e42dd9d7779f4da63b84f'
    _maxNumRetries = 10
    emotionData = pyqtSignal(str)
    exception = pyqtSignal()

    def __init__(self):
        QThread.__init__(self)
        try:
            self.webcam = Device()
        except Exception:
            self.webcam = None

    def run(self):
        if(self.webcam != None):
            while True:
                primaryEmotion = self.emotionCheck()
                self.emotionData.emit(primaryEmotion)
                self.sleep(5)
        else:
            self.exception.emit()

    def __del__(self):
        self.wait()

    def stop(self):
        self.terminate()
        self.webcam = None

    ##Send image to Microsoft Emotion API for analysing
    def processRequest(self, json, data, headers, params):
        self.retries = 0
        self.result = None
        while True:
            response = requests.request( 'post', self._url, json = json, data = data, headers = headers, params = params )
            if response.status_code == 429: 
                print( "Message: %s" % ( response.json()['error']['message'] ) )
                if self.retries <= self._maxNumRetries: 
                    time.sleep(1) 
                    self.retries += 1
                    continue
                else: 
                    print( 'Error: failed after retrying!' )
                    break
            elif response.status_code == 200 or response.status_code == 201:
                if 'content-length' in response.headers and int(response.headers['content-length']) == 0: 
                    self.result = None 
                elif 'content-type' in response.headers and isinstance(response.headers['content-type'], str): 
                    if 'application/json' in response.headers['content-type'].lower(): 
                        self.result = response.json() if response.content else None 
                    elif 'image' in response.headers['content-type'].lower(): 
                        self.result = response.content
            else:
                print( "Error code: %d" % ( response.status_code ) )
                print( "Message: %s" % ( response.json()['error']['message'] ) )
            break
        return self.result

    ##Capture, prep and upload local image for emotion analysing, upload it, and receive result
    def emotionCheck(self):
        presidingEmotion = "No Face Detected"
        self.webcam.saveSnapshot('userImage.jpg')
        with open( 'userImage.jpg', 'rb' ) as f:
            data = f.read()
        headers = dict()
        headers['Ocp-Apim-Subscription-Key'] = self._key
        headers['Content-Type'] = 'application/octet-stream'
        json = None
        params = {'returnFaceAttributes': 'emotion',}
        result = self.processRequest( json, data, headers, params )
        if result is not None:
            for currFace in result:
                print(currFace['faceAttributes']['emotion'].items())
                presidingEmotion = max(currFace['faceAttributes']['emotion'].items(), key=operator.itemgetter(1))[0]
        return presidingEmotion


class SensorReport():
    def __init__(self, sensorName, sensorReport, sensorFlag):
        self.sensorName = sensorName
        self.sensorReport = sensorReport
        self.sensorFlag = sensorFlag
        
class DriverMonitoringSystem(QtWidgets.QMainWindow, dmsGUI.Ui_MainWindow):
    def __init__(self, parent=None):
        super(DriverMonitoringSystem, self).__init__(parent)
        self.pulseReport = SensorReport("Pulse Sensor", "<span style=\" font-size:8pt; font-weight:600; color:#00ff00;\">""Good""</span>", False)
        self.gsrReport = SensorReport("GSR Sensor", "<span style=\" font-size:8pt; font-weight:600; color:#00ff00;\">""Good""</span>", False)
        self.muscleReport = SensorReport("Muscle Sensor", "<span style=\" font-size:8pt; font-weight:600; color:#00ff00;\">""Good""</span>", False)
        self.skinReport = SensorReport("Temperature Sensor", "<span style=\" font-size:8pt; font-weight:600; color:#00ff00;\">""Good""</span>", False)
        self.emotionReport = SensorReport("Emotion Sensor", "<span style=\" font-size:8pt; font-weight:600; color:#00ff00;\">""Good""</span>", False)
        self.initialisationLoop = 0
        self.gsrLoop = 0
        self.gsrAverage = 0
        self.muscleLoop = 0
        self.muscleAverage = 0
        self.flaggedSensors = []
        self.pulseReadings = []
        self.gsrReadings = []
        self.muscleReadings = []
        self.skinTemperatureReadings = []
        self.setupUi(self)
        self.connectButton.clicked.connect(self.startDataRetrieve)
        self.disconnectButton.clicked.connect(self.stopDataRetrieve)

    def startDataRetrieve(self, errorMessage):
        self.bluetoothStrengthLabel.setText("Connecting...");
        self.createSensorFolders()
        self.sensorThread = getSensorDataThread()
        self.sensorThread.sensorData.connect(self.updateSensorGUIValues)
        self.sensorThread.exception.connect(self.exceptionBluetoothLabel)
        self.sensorThread.start()
        self.emotionThread = getEmotionDataThread()
        self.emotionThread.emotionData.connect(self.updateEmotionGUIValue)
        self.emotionThread.exception.connect(self.exceptionWebcamLabel)
        self.healthBrowser.setText("Health Status: " + "<span style=\" font-size:8pt; font-weight:600; color:#00ff00;\">""Normal""</span>")
        
    def stopDataRetrieve(self):
        self.sensorThread.stop()
        self.emotionThread.stop()
        self.flaggedSensors.clear()
        self.initialisationLoop = 0
        self.gsrLoop = 0
        self.gsrAverage = 0
        self.muscleLoop = 0
        self.muscleAverage = 0
        self.pulseReport.sensorFlag = False;
        self.gsrReport.sensorFlag = False;
        self.muscleReport.sensorFlag = False;
        self.skinReport.sensorFlag = False;
        self.emotionReport.sensorFlag = False;
        self.bluetoothStrengthLabel.setText("<font color='red'>Disconnected</font>");
        self.connectButton.setEnabled(True)
        self.disconnectButton.setEnabled(False)

    def exceptionBluetoothLabel(self):
        self.bluetoothStrengthLabel.setText("<font color='red'>Connection not available</font>")

    def exceptionWebcamLabel(self):
        self.emotionalStateLabel.setText("<font color ='white'>Webcam N/A</font>")

    def createSensorFolders(self):
        currentDirectory = os.getcwd()
        sensorFolder = os.path.join(currentDirectory, r"Sensor Data")
        pulseFolder = os.path.join(currentDirectory, r"Sensor Data/Pulse Data")
        gsrFolder = os.path.join(currentDirectory, r"Sensor Data/GSR Data")
        muscleFolder = os.path.join(currentDirectory, r"Sensor Data/Muscle Data")
        skinTemperatureFolder = os.path.join(currentDirectory, r"Sensor Data/Skin Temperature Data")
        emotionFolder = os.path.join(currentDirectory, r"Sensor Data/Emotion Data")
        folderList = [sensorFolder, pulseFolder, gsrFolder, muscleFolder, skinTemperatureFolder, emotionFolder]
        for folder in folderList:
            if not os.path.exists(folder):
                os.makedirs(folder)           

    def updateSensorGUIValues(self, serialLine):
        self.emotionThread.start()
        self.bluetoothStrengthLabel.setText("<font color='green'>Connected</font>");
        self.connectButton.setEnabled(False)
        self.disconnectButton.setEnabled(True)
        if self.initialisationLoop == 30: 
            if serialLine[:1] == "P":
                self.pulseData = serialLine.split(":")[1]
                if(len(self.pulseReadings) == 30):
                   del self.pulseReadings[0]
                   self.pulseGraph.clear()
                self.pulseReadings.append(float(self.pulseData))
                self.pulseGraph.plot(self.pulseReadings, pen = 'g')
            elif serialLine[:1] == "B":
                self.bpmData = serialLine.split(":")[1]
                self.pulseRateLabel.setText(self.bpmData)
                self.writeData("Pulse Data", self.bpmData)
                if(float(self.bpmData) < 40 or float(self.bpmData) > 100):
                    self.pulseReport.sensorReport = "<span style=\" font-size:8pt; font-weight:600; color:#ff0000;\">""Bad""</span>"
                    self.pulseRateLabel.setStyleSheet('color: red')
                    if(self.pulseReport.sensorFlag == False):
                        self.flaggedSensors.append(self.pulseReport.sensorName)
                        self.pulseReport.sensorFlag = True
                    self.updateHealthReport()
                elif(float(self.bpmData) < 60 or float(self.bpmData) > 80):
                    self.pulseReport.sensorReport = "<span style=\" font-size:8pt; font-weight:600; color:#ffff00;\">""Okay""</span>"
                    self.pulseRateLabel.setStyleSheet('color: yellow')
                    self.updateHealthReport()
                else:
                    self.pulseReport.sensorReport = "<span style=\" font-size:8pt; font-weight:600; color:#00ff00;\">""Good""</span>"
                    self.pulseRateLabel.setStyleSheet('color: green')
                    self.updateHealthReport()
            elif serialLine[:1] == "G":
                self.gsrData = serialLine.split(":")[1]
                self.perspirationLevelLabel.setText(self.gsrData)
                if(len(self.gsrReadings) == 30):
                   del self.gsrReadings[0]
                   self.perspirationGraph.clear()
                self.gsrReadings.append(float(self.gsrData))
                self.perspirationGraph.plot(self.gsrReadings, pen = 'w')
                self.writeData("GSR Data", self.gsrData)
                if(self.gsrLoop == 5):
                    if(sum(self.gsrReadings[-5:])/5 < (self.gsrAverage - 6)):
                        self.gsrReport.sensorReport = "<span style=\" font-size:8pt; font-weight:600; color:#ff0000;\">""Bad""</span>"
                        self.perspirationLevelLabel.setStyleSheet('color: red')
                        if(self.gsrReport.sensorFlag == False):
                            self.flaggedSensors.append(self.gsrReport.sensorName)
                            self.gsrReport.sensorFlag = True
                        self.updateHealthReport()
                    elif(sum(self.gsrReadings[-5:])/5 < (self.gsrAverage - 4)):
                        self.gsrReport.sensorReport = "<span style=\" font-size:8pt; font-weight:600; color:#ffff00;\">""Okay""</span>"
                        self.perspirationLevelLabel.setStyleSheet('color: yellow')
                        self.updateHealthReport()
                    else:
                        self.gsrReport.sensorReport = "<span style=\" font-size:8pt; font-weight:600; color:#00ff00;\">""Good""</span>"
                        self.perspirationLevelLabel.setStyleSheet('color: green')
                        self.updateHealthReport()
                    self.gsrLoop = 0
                    self.gsrAverage = sum(self.gsrReadings[-5:])/5
                else:
                    self.gsrLoop = self.gsrLoop + 1
            elif serialLine[:1] == "M":
                self.muscleData = serialLine.split(":")[1]
                self.muscleTensionLabel.setText(self.muscleData)
                if(len(self.muscleReadings) == 30):
                   del self.muscleReadings[0]
                   self.muscleGraph.clear()
                self.muscleReadings.append(float(self.muscleData))
                self.muscleGraph.plot(self.muscleReadings, pen = 'c')
                self.writeData("Muscle Data", self.muscleData)
                if(self.muscleLoop == 5):
                    if(sum(self.muscleReadings[-5:])/5 < (self.muscleAverage - 10)):
                        self.muscleReport.sensorReport = "<span style=\" font-size:8pt; font-weight:600; color:#ff0000;\">""Bad""</span>"
                        self.muscleTensionLabel.setStyleSheet('color: red')
                        if(self.muscleReport.sensorFlag == False):
                            self.flaggedSensors.append(self.muscleReport.sensorName)
                            self.muscleReport.sensorFlag = True
                        self.updateHealthReport()
                    elif(sum(self.muscleReadings[-5:])/5 < (self.muscleAverage - 5)):
                        self.muscleReport.sensorReport = "<span style=\" font-size:8pt; font-weight:600; color:#ffff00;\">""Okay""</span>"
                        self.muscleTensionLabel.setStyleSheet('color: yellow')
                        self.updateHealthReport()
                    else:
                        self.muscleReport.sensorReport = "<span style=\" font-size:8pt; font-weight:600; color:#00ff00;\">""Good""</span>"
                        self.muscleTensionLabel.setStyleSheet('color: green')
                        self.updateHealthReport()
                    self.muscleLoop = 0
                    self.muscleAverage = sum(self.muscleReadings[-5:])/5
                else:
                    self.muscleLoop = self.muscleLoop + 1
            elif serialLine[:1] == "T":
                self.skinTemperatureData = serialLine.split(":")[1]
                self.skinTemperatureLabel.setText(self.skinTemperatureData)
                if(len(self.skinTemperatureReadings) == 30):
                   del self.skinTemperatureReadings[0]
                   self.skinGraph.clear()
                self.skinTemperatureReadings.append(float(self.skinTemperatureData))
                self.skinGraph.plot(self.skinTemperatureReadings, pen = 'r')
                self.writeData("Skin Temperature Data", self.skinTemperatureData)
                if(float(self.skinTemperatureData) < 30 or float(self.skinTemperatureData) > 36):
                    self.skinReport.sensorReport = "<span style=\" font-size:8pt; font-weight:600; color:#ff0000;\">""Bad""</span>"
                    self.skinTemperatureLabel.setStyleSheet('color: red')
                    if(self.skinReport.sensorFlag == False):
                        self.flaggedSensors.append(self.skinReport.sensorName)
                        self.skinReport.sensorFlag = True
                    self.updateHealthReport()
                elif(float(self.skinTemperatureData) < 31 or float(self.skinTemperatureData) > 35):
                    self.skinReport.sensorReport = "<span style=\" font-size:8pt; font-weight:600; color:#ffff00;\">""Okay""</span>"
                    self.skinTemperatureLabel.setStyleSheet('color: yellow')
                    self.updateHealthReport()
                else:
                    self.skinReport.sensorReport = "<span style=\" font-size:8pt; font-weight:600; color:#00ff00;\">""Good""</span>"
                    self.skinTemperatureLabel.setStyleSheet('color: green')
                    self.updateHealthReport()
            print(serialLine)
        else:
            self.initialisationLoop = self.initialisationLoop + 1

    def updateEmotionGUIValue(self, emotionData):
        img = Image.open('userImage.jpg')
        resizedImg = img.resize((161, 121))
        resizedImg.save('userimage.jpg', "JPEG", optimize=True)
        self.webcamPictureLabel.setPixmap(QPixmap('userImage.jpg'))
        self.emotionalStateLabel.setText(emotionData.title())
        self.writeData("Emotion Data", emotionData + "\n")
        if(emotionData in {"anger", "disgust", "fear", "contempt"}):
            self.emotionReport.sensorReport = "<span style=\" font-size:8pt; font-weight:600; color:#ff0000;\">""Bad""</span>"
            self.emotionalStateLabel.setStyleSheet('color: red')
            if(self.emotionReport.sensorFlag == False):
                self.flaggedSensors.append(self.emotionReport.sensorName)
                self.emotionReport.sensorFlag = True
            self.updateHealthReport()
        else:
            self.emotionReport.sensorReport = "<span style=\" font-size:8pt; font-weight:600; color:#00ff00;\">""Good""</span>"
            self.emotionalStateLabel.setStyleSheet('color: green')
            self.updateHealthReport()
        print(emotionData)

    def writeData(self, sensorType, sensorData):
        self.currentTime = str(datetime.datetime.now().strftime("[%d-%m-%Y] [%H_%M]"))
        self.file = open("Sensor Data/" + sensorType + "/" + sensorType + " " + self.currentTime + ".txt","a")
        self.file.write(sensorData.title())
        self.file.close()

    def updateHealthReport(self):
        self.sensorBrowser.clear()
        self.sensorBrowser.append("Heart Rate: " + self.pulseReport.sensorReport)
        self.sensorBrowser.append("Perspiration: " + self.gsrReport.sensorReport)
        self.sensorBrowser.append("Muscle Tenseness: " + self.muscleReport.sensorReport)
        self.sensorBrowser.append("Skin Temperature: " + self.skinReport.sensorReport)
        self.sensorBrowser.append("Emotional State: " + self.emotionReport.sensorReport)
        if self.flaggedSensors:
            self.healthBrowser.clear()
            self.healthBrowser.insertPlainText("Abnormal readings detected by: ")
            self.healthBrowser.insertPlainText(", ".join(map(str,self.flaggedSensors)))
            self.healthBrowser.append("Health Status: " + "<span style=\" font-size:8pt; font-weight:600; color:#ff0000;\">""At Risk""</span>")
            self.healthBrowser.append("<br/>""One or more Health Sensors have reported abnormal biometric readings since recording began, please consider pulling over and verifying you are in a suitable state to continue driving")


def exception_hook(exctype, value, traceback):
    print(exctype, value, traceback)
    sys._excepthook(exctype, value, traceback) 
    sys.exit(1)

def main():
    ##
    sys._excepthook = sys.excepthook
    sys.excepthook = exception_hook
    ##
    app = QtWidgets.QApplication(sys.argv)
    form = DriverMonitoringSystem()
    form.show()
    app.exec_() 

if __name__ == "__main__":
    main()





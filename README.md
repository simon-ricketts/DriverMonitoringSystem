# Driver Monitoring System

The Driver Monitoring System is a system used to aggregate biometric data from the attached user and determine whether they are in a medically fit state to drive. The system utilises five sensors: A Webcam to detect emotional status, a Pulse Sensor, an Electromyography sensor, a Temperature Sensor, and a Galvanic Skin Response sensor.

# Hardware

This system uses the following pieces of hardware, you may use substitutes but I cannot guarantee the system will work as intended. Please pay heed to which wires correspond to which devices in the [Arduino code](Arduino/Prototype/Prototype.ino) when setting up your system.

Hardware used:

- Elegoo UNO R3 Board
- Myoware Muscle Sensor
- Biomedical Sensor Pads
- Pulse/Heart Rate Sensor
- Seeed 101020052 Grove - GSR Galvanic Skin Response with Finger Sensors
- LM35DZ Precision Centrigrade Temperature Sensors
- HC-06 Wireless Bluetooth Serial Transceiver
- EkoBuy Bluetooth 4.0 USB Dongle
- Logitech C270 Webcam



# Software

Please ensure the following pre-requisites are met before attempting to run the system. Once all steps are completed, the application can be started by running 'Prototype.py'.



**1. Install Python-3 (IMPORTANT)** - The system was written using Python 3.6.4, any recent release of Python-3
should work fine, however many of the modules required to run the system do not exist on Python-2 and the
system will therefore not run correctly on it. 


**2. Install the following list of Python modules:**

- PyQt5
- Pillow
- VideoCapture (Download from lfd link below)
- pyqtgraph
- pyserial
- requests
- OpenCV (Download from lfd link below)

Installation of these modules can be done through the pip command (e.g. 'pip3 install PyQt5') or a .whl of the module can
be downloaded from the following link (https://www.lfd.uci.edu/~gohlke/pythonlibs/) and installed by navigating to the download folder
and using the same command format (e.g. pip3 install PyQt5.whl). If installing using the latter method, please ensure that the Python 
and OS version of the .whl file match your Python installation. 


**3. Navigate to the following file: [YOUR PYTHON INSTALLATION LOCATION]\Lib\site-packages\VideoCapture\__init__.py**

Go to Line 153 and change "fromstring" to "frombytes". fromstring() is a method which has been removed and will cause the system to crash
whenever the webcam takes a picture if not changed.


**4. Pair the HC-06 with your PC** - With the system powered on, pairing the HC-06 should be fairly straight forward. Find the "Add Bluetooth Device"
functionality on your operating system and select the HC-06, enter it's PIN (1234) and the pairing process should complete.


**5. (OPTIONAL) Ensure the COM port in 'Prototype.py' matches your PCs** - The default COM port that the system is set to read from may not match the 
one assigned by your system when you paired the HC-06, giving you the following error message: could not open port 'COM#': FileNotFoundError(2, 'The system cannot find the file specified.', None, 2)

If this is the case, find your system's COM port facing the "Outgoing" direction with the name "HC-06 'Dev B'" in your Bluetooth settings 
and update Line 30 in 'Prototype.py' with the new COM number.

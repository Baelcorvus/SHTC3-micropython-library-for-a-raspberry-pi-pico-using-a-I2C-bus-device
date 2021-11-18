'''
Code to use a SHTC3 - Temperature & Humidity Sensor with a pico microcontroller
in micropython using an I2C bus device.
'''

'''first we import the libraries'''
from machine import Pin, I2C
from time import sleep
import shtc3

'''Then we define the physical I2C that the sensor is connected to''' 
sdaPIN=machine.Pin(0)
sclPIN=machine.Pin(1)
i2c_bus = 0

i2c=machine.I2C(i2c_bus, sda=sdaPIN, scl=sclPIN, freq=400000)

sht_addr = 0x70

'''and finnaly set up the sensor object that will always talk to the sensor'''

try:
    sht = shtc3.SHTC3(i2c, sht_addr)
    chip_id = sht._chip_id
    if (chip_id == 0x807):
        identifier = "SHTC3"
    else:
        identifier = "other sensor"
except OSError:
    print ("SHTC3 not present")
    sht_attached = False
else:
    print('{} is present'.format(identifier))
        
while True:
    try:
        temperature, humidity = sht.measurements         #read both temperature and humidity at the same time. 
        print("temperature: {}  Relative_humidity {}  ".format(temperature, humidity), end = '\r')
    except OSError:      #if we get an error during I/O retry the connection
        temperature = 0
        humidity = 0
        print("SHTC3 I/O Error - retrying connection")

    sleep(0.1)                                           #read every half second - not necessary for the bus, just cosmetic, omit as needed

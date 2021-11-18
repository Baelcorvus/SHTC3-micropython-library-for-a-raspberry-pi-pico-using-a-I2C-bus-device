'''
Example of an integrated sensor system with multiple I2C devices on the same bus.
This example uses a potential of up to 4 sensors, a TSL2591 high precision light sensor
a SI7021 temperatur and humidity sensor, a SHTC3 temperature and humidity sensor and
a slave arduino microcontroller simply receiving the status of a button and reporting
the state of a button connected to it.
'''

'''first we import the libraries for the devics - if you do not have the libraries for unused
sensors put a # infront of a library
'''
from machine import Pin, I2C
from time import sleep
import TSL2591
import SI7021
import Ard_obj
import shtc3

'''
Then we define the I2C as it is physically connected to out pico
'''
sdaPIN=machine.Pin(0)
sclPIN=machine.Pin(1)
i2c_bus = 0

i2c=machine.I2C(i2c_bus, sda=sdaPIN, scl=sclPIN, freq=400000)

'set up the addresses of the sensors'
ard_addr = 0x09
lux_addr = 0x29
temp_addr = 0x40
sht_addr = 0x70

'tell the example program which devices are attached to the bus'
ard_attached = True
tsl_attached = True
si_attached = True
sht_attached = True
'''
now we create and intialise the objects.
ard will now always talk to the arduino slave, and similarly
tsl will always communicate with the tsl2591 light sensor,
si will always communicate with the si7021 sensor and
sht will always talk to the shtc3 sensor
'''
if (ard_attached):
    try:
        ard = Ard_obj.ard_obj(i2c, ard_addr)
    except OSError:
        print('Arduino is not present')
        ard_attached = False
    else:
        print("Arduino is present")
        
if (tsl_attached):
    try:
        tsl = TSL2591.TSL2591(i2c, lux_addr)
        chip_id = tsl._chip_id
        if (chip_id== 0x50):
            identifier = "TSL2591"
        else:
            identifier = "other sensor"
    except OSError:
        print ("TSL2591 not present")
        tsl_attached = False
    else:
        print('{} is present'.format(identifier))
        
if (si_attached):
    try:
        si = SI7021.SI7021(i2c, temp_addr)
        serial, identifier = si._get_device_info()
    except OSError:
        print ("SI7021 not present")
        si_attached = False
    else:
        print('{} is present'.format(identifier))
        
if (sht_attached):
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

'here we define an external LED (on pin 28) and a button (on pin 20) so we can communicate their states to the arduino.'
led = machine.Pin(28, Pin.OUT)
led.low()

but2 = Pin(20, Pin.IN, Pin.PULL_UP)


while True:
    if (ard_attached):       #if we have the arduino attached and it has been found send the button state and receive the arduino button state
        try:
            button = ard.read_write(but2.value())
            if (button == 1):
                led.high()
            else:
                led.low()
        except OSError:      #if we get an error during I/O retry the connection
            print("adrduino slave I/O Error - retrying")
            
    if(tsl_attached):        #if a TSL2591 light sensor is attached and had been found read the lux value
        try:
            lux = tsl.lux
            print("lux: {}  ".format(lux), end = '')
        except OSError:      #if we get an error during I/O retry the connection
            lux = 0
            print("TSL2591 I/O Error - retrying")
        
    if(si_attached):        #if a SI7021 temperatue and humidity sensor is present read both values.
        try:
            temperature, humidity = si.measurments 
            print("temperature: {}  Relative_humidity {}  ".format(temperature, humidity), end = '')
        except OSError:      #if we get an error during I/O retry the connection
            temperature = 0
            humidity = 0
            print("SI7021 I/O Error - retrying")

    if(sht_attached):                  #if a SHTC3 temperature and humidity sensor is present read both values.
        try:
            temperature2, humidity2 = sht.measurements
            print("temperature: {}  Relative_humidity {}  ".format(temperature2, humidity2), end = '')
        except OSError:      #if we get an error during I/O retry the connection
            temperature2 = 0
            humidity2 = 0
            print("SHTC3 I/O Error - retrying")
            
    print(end='\r')
    sleep(0.25)     #give the bus a rest before reading again. You can omit this for maximum data throughput.
    
    
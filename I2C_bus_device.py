'''
Micropython I2C bus device script for a Raspberry Pi Pico microcontroller in micropython

This library is designed to standardise I2C communication on a Pico microcontroller.
Usding this library creats a device that you can simply send or receive data over the I2C bus.
First you must put this library in the default directory of the Pico.
then import it into your project:

from machine import Pin, I2C
from I2C_bus_device import I2CDevice

To use you define which pins your I2C bus is connected to:

sdaPIN=machine.Pin(0)
sclPIN=machine.Pin(1)
i2c_bus = 0

i2c=machine.I2C(i2c_bus, sda=sdaPIN, scl=sclPIN, freq=400000)

Ths sets up an i2c bus with pin (0) as SDA and pin (1) as SCL. i2c_bus is designated by which pins you
choose for the bus. If you check the pinout for your Pico it will tell you which bus it is for the pins you choose.

Then create your device with the i2c address of the device on the bus.

device = I2CDevice(i2c, addr)

Then you can use device.write(buffer) to write to the device or device.readinto(buffer) to receive from the device.
You can also use devicece.write_then_readinto(out_buffer, in_buffer) to perform boht, for instance if you need to
send a command to the device before redaing from it.

'''
from time import sleep

class I2CDevice:
    def __init__(self, i2c, device_address, probe=True): #routine to initialize the device. If no probe=False is sent  
        self.i2c = i2c                                   #it is checked whether the deice exxists. If not an error is generated.
        self.device_address = device_address
        if probe:
            self.__probe_for_device()
            
    def readinto(self, buf, start=0, end=None):    #Function to read the data from the I2C device. The data will be put into
        if end is None:                               #the variable speciified by the calling rrutine.
            end = len(buf)                            #The buffer ssould be a bytearray. So to call we might use:
                                                      #data = byetarray()
        self.i2c.readfrom_into(self.device_address, buf)      #device.readinto(data)
        buf = buf[start:end]                      #if a start and/or end vvalue is specified then this data will be a subset of the aquired data.

    
    def write(self, buf, start=0, end=None):       #Function to write data to the I2C device. 
        if end is None:                               #put the data you wish to send in bytearray and call device.write, for example,
            end = len(buf)                                            #message = "hello"
                                                          #data = bytearray(message)
        self.i2c.writeto(self.device_address, buf[start:end])     #device.write (data)

    
    def write_then_readinto(                          #Function that writes to an I2C device, waits for a time and then reads he device.
        self,                                         #This may be useful if a device requires a command before sending the correct data.
        out_buffer,                                   #the command would be put in the out_buffer and is received into in_buffer.
        in_buffer,                                    #If delay is omitted then the default delay of 0s is used.
        delay = 0,                                    #In and out valuese can be used to slice the bytearray.
        out_start=0,                                  #Example:
        out_end=None,                                             #cmd = "read"
        in_start=0,                                               #out_buf = bytearray(cmd)
        in_end=None                                               #in_buf = bytearray()
    ):                                                            #delay = 0.2
                                                      #device.write_then_readinto(out_buf, in_buf, delay)
            if out_end is None:
                out_end = len(out_buffer)
            if in_end is None:
                in_end = len(in_buffer)
            self.i2c.writeto(self.device_address, out_buffer[out_start:out_end])
            sleep(delay)
            self.i2c.readfrom_into(self.device_address, in_buffer)
            in_buffer = in_buffer[in_start:in_end]
            

    def __probe_for_device(self):                            #Function to check if the device is present. If no device answers then
        try:                                                 #device.i2c_error is set to -1 and device.i2c_error_device is set to the device address that is not present.
            self.i2c.writeto(self.device_address, b"")
        except OSError:

            try:
                result = bytearray(1)
                self.i2c.readfrom_into(self.device_address, result)
            except OSError:
                #raise ValueError("No I2C device at address: 0x%x" % self.device_address) #enable this line if you wish the execution to stop if device is not present.
                return
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        return False

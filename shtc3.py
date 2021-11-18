"""
Driver for the SHTC3 - Temperature & Humidity Sensor in micropython using an I2C bus device for the raspberry pi pico microcontroller
Requires the presence of the I2C_bus_device librrary from:

https://github.com/Baelcorvus/I2C_Busdevice
"""
from time import sleep
from I2C_bus_device import I2CDevice
import struct

_SHTC3_DEFAULT_ADDR = 0x70  # SHTC3 I2C Address
_SHTC3_NORMAL_MEAS_TFIRST_STRETCH = (
    0x7CA2  # Normal measurement, temp first with Clock Stretch Enabled
)
_SHTC3_LOWPOW_MEAS_TFIRST_STRETCH = (
    0x6458  # Low power measurement, temp first with Clock Stretch Enabled
)
_SHTC3_NORMAL_MEAS_HFIRST_STRETCH = (
    0x5C24  # Normal measurement, hum first with Clock Stretch Enabled
)
_SHTC3_LOWPOW_MEAS_HFIRST_STRETCH = (
    0x44DE  # Low power measurement, hum first with Clock Stretch Enabled
)

_SHTC3_NORMAL_MEAS_TFIRST = (
    0x7866  # Normal measurement, temp first with Clock Stretch disabled
)
_SHTC3_LOWPOW_MEAS_TFIRST = (
    0x609C  # Low power measurement, temp first with Clock Stretch disabled
)
_SHTC3_NORMAL_MEAS_HFIRST = (
    0x58E0  # Normal measurement, hum first with Clock Stretch disabled
)
_SHTC3_LOWPOW_MEAS_HFIRST = (
    0x401A  # Low power measurement, hum first with Clock Stretch disabled
)

_SHTC3_READID = 0xEFC8  # Read Out of ID Register
_SHTC3_SOFTRESET = 0x805D  # Soft Reset
_SHTC3_SLEEP = 0xB098  # Enter sleep mode
_SHTC3_WAKEUP = 0x3517  # Wakeup mode
_SHTC3_CHIP_ID = 0x807


class SHTC3:
    '''SHTC3 - Temperature & Humidity Sensor.
    to use call the object with the i2C bus to use and the address of the sensor.
    If no address is given the default of 0x70 is used.

    To use the device, first you must import the library:
    
        from machine import Pin, I2C
        from I2C_bus_device import I2CDevice
        import sthc3
        
    then define the I2C bus the device is attached to:

        sdaPIN=machine.Pin(0)
        sclPIN=machine.Pin(1)
        i2c_bus = 0
        addr = 0x29

        i2c=machine.I2C(i2c_bus, sda=sdaPIN, scl=sclPIN, freq=400000)
    
    Will define an I2C bus on pin 0 for SDA and pin 1 for SCL. The actual pins will need to be changed
    to the specifics of your project. The i2c_bus will be designated by the pins used. A pinout
    of your pico will call the pins sda0 and scl0 for bus 0 and sda1 and scl1 for bus 1
    
    to define the sensor object we then use:

        sht = sshtc3.SHTC3(i2c, addr)
        
    if the address is the same as the deafult the addr can be omited (so: sht = sshtc3.SHTC3(i2c))
    you can then read the sesnore with the .measurments property.
    Both temperature and relative humidity are read at the same time. So you can use:
    
        temperature, humidity = sht..measurements

    '''
    def __init__(self, i2c, sht_addr = _SHTC3_DEFAULT_ADDR):
        self.device = I2CDevice(i2c, sht_addr)
        self._buffer = bytearray(6)
        self.low_power = False
        self.sleeping = False
        self.reset()
        self._chip_id = self._get_chip_id()
        
    def _write_command(self, command):
        """helper function to write a command to the i2c device"""
        self._buffer[0] = command >> 8
        self._buffer[1] = command & 0xFF
        self.device.write(self._buffer)

    def _get_chip_id(self):  #   readCommand(SHTC3_READID, data, 3);
        """Determines the chip id of the sensor"""
        self._write_command(_SHTC3_READID)
        sleep(0.001)
        self.device.readinto(self._buffer)
        return struct.unpack_from(">H", self._buffer)[0] & 0x083F
    
    def reset(self):
        """Perform a soft reset of the sensor, resetting all settings to their power-on defaults"""
        self.sleeping = False
        try:
            self._write_command(_SHTC3_SOFTRESET)

        except RuntimeError as run_err:
            if run_err.args and run_err.args[0] != "I2C device address was NACK'd":
                raise run_err
        sleep(0.001)
        
    @property
    def sleeping(self):
        """Determines the sleep state of the sensor"""
        return self._cached_sleep

    @sleeping.setter
    def sleeping(self, sleep_enabled):
        if sleep_enabled:
            self._write_command(_SHTC3_SLEEP)
        else:
            self._write_command(_SHTC3_WAKEUP)
        sleep(0.001)
        self._cached_sleep = sleep_enabled

    # lowPowerMode(bool readmode) { _lpMode = readmode

    @property
    def low_power(self):
        """Enables the less accurate low power mode, trading accuracy for power consumption"""
        return self._low_power

    @low_power.setter
    def low_power(self, low_power_enabled):
        self._low_power = low_power_enabled

    @property
    def relative_humidity(self):
        """The current relative humidity in % rH. This is a value from 0-100%."""
        return self.measurements[1]

    @property
    def temperature(self):
        """The current temperature in degrees Celsius"""
        return self.measurements[0]
    
    @property
    def measurements(self):
        """both `temperature` and `relative_humidity`, read simultaneously"""

        self.sleeping = False
        temperature = None
        humidity = None
        # send correct command for the current power state
        if self.low_power:
            self._write_command(_SHTC3_LOWPOW_MEAS_TFIRST)
            sleep(0.001)
        else:
            self._write_command(_SHTC3_NORMAL_MEAS_TFIRST)
            sleep(0.013)

        self._buffer = bytearray(6)
        # read the measured data into our buffer
        self.device.readinto(self._buffer)

        # separate the read data
        temp_data = self._buffer[0:2]
        temp_crc = self._buffer[2]
        humidity_data = self._buffer[3:5]
        humidity_crc = self._buffer[5]

        # check CRC of bytes
        if temp_crc != self._crc8(temp_data) or humidity_crc != self._crc8(
            humidity_data
        ):
            return

        # decode data into human values:
        # convert bytes into 16-bit signed integer
        # convert the LSB value to a human value according to the datasheet
        raw_temp = struct.unpack_from(">H", temp_data)[0]
        raw_temp = ((4375 * raw_temp) >> 14) - 4500
        temperature = raw_temp / 100.0

        # repeat above steps for humidity data
        raw_humidity = struct.unpack_from(">H", humidity_data)[0]
        raw_humidity = (625 * raw_humidity) >> 12
        humidity = raw_humidity / 100.0

        self.sleeping = True
        return (temperature, humidity)

    ## CRC-8 formula from page 14 of SHTC3 datasheet
    # https://media.digikey.com/pdf/Data%20Sheets/Sensirion%20PDFs/HT_DS_SHTC3_D1.pdf
    # Test data [0xBE, 0xEF] should yield 0x92

    @staticmethod
    def _crc8(buffer):
        """verify the crc8 checksum"""
        crc = 0xFF
        for byte in buffer:
            crc ^= byte
            for _ in range(8):
                if crc & 0x80:
                    crc = (crc << 1) ^ 0x31
                else:
                    crc = crc << 1
        return crc & 0xFF  # return the bottom 8 bits
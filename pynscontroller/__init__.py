# import useful modules
import serial
from time import sleep
import crc8


# define the class
class PyNSController:
    # the first byte of the command
    b0 = {
        'Minus': 0b0000_0001,
        'Plus': 0b0000_0010,
        'LClick': 0b0000_0100,
        'RClick': 0b0000_1000,
        'Home': 0b0001_0000,
        'Capture': 0b0010_0000,
        'SL': 0b0100_0000,
        'SR': 0b1000_0000,
    }

    # the second byte of the command
    b1 = {
        'Y': 0b0000_0001,
        'B': 0b0000_0010,
        'A': 0b0000_0100,
        'X': 0b0000_1000,
        'L': 0b0001_0000,
        'R': 0b0010_0000,
        'ZL': 0b0100_0000,
        'ZR': 0b1000_0000
    }

    # the third byte of the command
    b2 = {
        'D_C': 0x08,
        'D_U': 0x00,
        'D_UR': 0x01,
        'D_R': 0x02,
        'D_DR': 0x03,
        'D_D': 0x04,
        'D_DL': 0x05,
        'D_L': 0x06,
        'D_UL': 0x07,
    }

    # initialize the class
    def __init__(self, port, gap=0.045):
        # the time interval between two commands
        self.gap = gap

        # try to initialize the serial port
        try:
            self.ser = serial.Serial(port, baudrate=19200, timeout=0.5)
        except:
            print('Cannot open the serial port.')
            return None

        # try to comuunicate with the esp32 chip
        if not self.connect_to_esp32():
            print('Cannot connect to the esp32 chip.')
            return None
        else:
            print('Connected to the esp32 chip.')

    # connect to the esp32 chip
    def connect_to_esp32(self):
        # simply send a command to the esp32 chip
        # if the esp32 chip replies, then the connection is established already
        if self.push_stick():
            return True

        # if the esp32 chip does not reply, then we need to establish the connection
        # use the "Chocolate" handshake mode to establish the connection

        # send 0xFF and wait for 0xFF
        self.ser.write(b'\xFF')
        data = self.ser.read(size=1)
        if data.hex() != 'ff':
            return False

        # send 0x44 and wait for 0xEE
        self.ser.write(b'\x44')
        data = self.ser.read(size=1)
        if data.hex() != 'ee':
            return False

        # send 0xEE and wait for 0x03
        self.ser.write(b'\xEE')
        data = self.ser.read(size=1)
        if data.hex() != '03':
            return False
        return True

    # the function to calculate the crc8 checksum
    def cal_crc8(commands):
        hash = crc8.crc8()
        hash.update(bytearray(commands))
        commands.append(int(hash.hexdigest(), 16))
        return commands

    # the function to generate an empty status command
    def empty_status():
        byte0 = int('0x00', 16)
        byte1 = int('0x00', 16)
        byte2 = int('0x08', 16)
        byte3 = int('0x7f', 16)
        byte4 = int('0x7f', 16)
        byte5 = int('0x7f', 16)
        byte6 = int('0x7f', 16)
        byte7 = int('0x00', 16)
        commands = [byte0, byte1, byte2, byte3, byte4, byte5, byte6, byte7]
        return PyNSController.cal_crc8(commands)

    # the function to change the commands according to the button list and stick list
    def set_status(commands, button_list=[], stick_list=[127, 127, 127, 127]):
        # remove the last byte, which is the crc8 checksum
        commands.pop()
        # set the buttons
        for button in button_list:
            if button in PyNSController.b0.keys():
                commands[0] = commands[0] | PyNSController.b0[button]
            if button in PyNSController.b1.keys():
                commands[1] = commands[1] | PyNSController.b1[button]
            if button in PyNSController.b2.keys():
                commands[2] = PyNSController.b2[button]

        # set the sticks
        for i in range(4):
            commands[3+i] = stick_list[i]

        return PyNSController.cal_crc8(commands)

    # the function to release the buttons and sticks
    def release_status(commands, button_list=[], stick_list=[127, 127, 127, 127]):
        # remove the last byte, which is the crc8 checksum
        commands.pop()
        # release the buttons
        for button in button_list:
            if button in PyNSController.b0.keys():
                commands[0] = commands[0] & ~PyNSController.b0[button]
            if button in PyNSController.b1.keys():
                commands[1] = commands[1] & ~PyNSController.b1[button]
            if button in PyNSController.b2.keys():
                commands[2] = PyNSController.b2['D_C']

        # release the sticks
        for i in range(4):
            commands[3+i] = stick_list[i]

        return PyNSController.cal_crc8(commands)

    # the function to generate the status command to push a button
    def press_button(self, button_list=[], duration=0):
        # generate an empty status command
        commands = PyNSController.empty_status()
        # set the status command by the button list
        commands = PyNSController.set_status(commands, button_list)
        # send the command
        self.ser.write(bytearray(commands))
        # wait for the reply
        data = self.ser.read(size=1)
        # if the reply is not 0x90, then the command is not sent successfully
        if data.hex() != '90':
            return False
        sleep(self.gap + duration)

        # release the buttons
        commands = PyNSController.release_status(commands, button_list)
        # send the command
        self.ser.write(bytearray(commands))
        # wait for the reply
        data = self.ser.read(size=1)
        # if the reply is not 0x90, then the command is not sent successfully
        if data.hex() != '90':
            return False
        sleep(self.gap)
        return True

    # the function to generate the status command to push a stick
    # the default value is the center of the stick
    # stick_list = [LX, LY, RX, RY]
    def push_stick(self, stick_list=[127, 127, 127, 127], duration=1):
        # generate an empty status command
        commands = PyNSController.empty_status()
        # set the status command by the given stick_list
        commands = PyNSController.set_status(commands, stick_list=stick_list)
        # send the status command
        self.ser.write(bytearray(commands))
        # wait for the reply
        data = self.ser.read(size=1)
        if data.hex() != '90':
            return False
        sleep(self.gap+duration)

        commands = PyNSController.release_status(commands)
        # send the status command
        self.ser.write(bytearray(commands))
        # wait for the reply
        data = self.ser.read(size=1)
        if data.hex() != '90':
            return False
        sleep(self.gap)
        return True

    def press_button_and_stick(self, button_list=[], stick_list=[127, 127, 127, 127], duration=1):
        commands = PyNSController.empty_status()
        # set the status command by the given button_list and stick_list
        commands = PyNSController.set_status(
            commands, button_list=button_list, stick_list=stick_list)
        # send the status command
        self.ser.write(bytearray(commands))
        # wait for the reply
        data = self.ser.read(size=1)
        if data.hex() != '90':
            return False
        sleep(self.gap+duration)
        # if the reply is not 0x90, then the command is not sent successfully
        if data.hex() != '90':
            return False
        sleep(self.gap)
        return True

    def close(self):
        self.ser.close()


if __name__ == '__main__':
    # the UART port of the esp32 chip
    port = '/dev/ttyUSB0'
    # initialize the controller
    controller = PyNSController(port)
    # push the button A
    controller.press_button(['A'])
    # push the both two sticks to the left-top corner
    controller.push_stick([0, 0, 0, 0])
    # release the both two sticks
    controller.push_stick()

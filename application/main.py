# %%
import serial
from time import sleep
import crc8
import numpy as np
from PIL import Image

# %%
b0 ={
    'Minus': 0b0000_0001,
    'Plus': 0b0000_0010,
    'LClick': 0b0000_0100,
    'RClick': 0b0000_1000,
    'Home': 0b0001_0000,
    'Capture': 0b0010_0000,
    'SL': 0b0100_0000,
    'SR': 0b1000_0000,
}

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

b2 ={
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

# %%
def cal_crc8(commands):
    hash = crc8.crc8()
    hash.update(bytearray(commands))
    commands.append(int(hash.hexdigest(), 16))
    return commands

def empty_status():
    byte0 = int(b'0000_0000', 2)
    byte1 = int(b'0000_0000', 2)
    byte2 = int('0x08', 16)
    byte3 = int('0x00', 16)
    byte4 = int('0x00', 16)
    byte5 = int('0x00', 16)
    byte6 = int('0x00', 16)
    byte7 = int('0x00', 16)
    commands = [byte0, byte1, byte2, byte3, byte4, byte5, byte6, byte7]
    return cal_crc8(commands)

# stick_list = [LX, LY, RX, RY]
def set_status(commands, button_list = [], stick_list=[127, 127, 127, 127]):
    commands.pop()
    for button in button_list:
        if button in b0.keys():
            commands[0] = commands[0] | b0[button]
        if button in b1.keys():
            commands[1] = commands[1] | b1[button]
        if button in b2.keys():
            commands[2] = b2[button]
            
    for i in range(4):
        commands[3+i] = stick_list[i]
    
    return cal_crc8(commands)
        
def release_status(commands, button_list = [], stick_list=[127, 127, 127, 127]):
    commands.pop()
    for button in button_list:
        if button in b0.keys():
            commands[0] = commands[0] & ~b0[button]
        if button in b1.keys():
            commands[1] = commands[1] & ~b1[button]
        if button in b2.keys():
            commands[2] = b2['D_C']
            
    for i in range(4):
        commands[3+i] = stick_list[i]
    
    return cal_crc8(commands)

def push_button(ser, button_list = []):
    commands = empty_status()
    commands = set_status(commands, button_list)
    ser.write(bytearray(commands))
    data = ser.read(size=1)
    if data.hex() != '90':
        return False
    sleep(duration)
    commands = release_status(commands, button_list)
    ser.write(bytearray(commands))
    data = ser.read(size=1)
    if data.hex() != '90':
        return False
    sleep(duration)
    return True

def push_stick(ser, stick_list=[127, 127, 127, 127]):
    commands = empty_status()
    commands = set_status(commands, stick_list=stick_list)
    ser.write(bytearray(commands))
    data = ser.read(size=1)
    if data.hex() != '90':
        return False
    sleep(duration) 
    return True

def initial(port):
    ser = serial.Serial(port, baudrate=19200, timeout=0.5)
    if push_stick(ser):
        return ser
    
    ser.write(b'\xFF')
    data = ser.read(size=1)
    if data.hex() != 'ff':
        return False
    
    ser.write(b'\x44')
    data = ser.read(size=1)
    if data.hex() != 'ee':
        return False
    
    ser.write(b'\xEE')
    data = ser.read(size=1)
    if data.hex() != '03':
        return False
    return ser

def step1(ser):
    push_button(ser, ['L'])
    push_button(ser, ['LClick'])
    push_stick(ser, [0, 0, 127, 127])
    sleep(3.5)
    push_stick(ser)
    
def connect(ser):
    for _ in range(10):
        push_button(ser, ['L', 'R'])
        sleep(1)
    push_button(ser, ['A'])
    sleep(1)
    push_button(ser, ['Home'])
    sleep(1)
    push_button(ser, ['Home'])
    sleep(1)

def move_to_begin(ser, duration=4):
    push_stick(ser, [0, 127, 127, 127])
    sleep(duration)
    push_stick(ser)
    
def check_left(img, i, j):
    if np.uint(~img[i, j:]).sum() == 0:
        return False
    return True

# %%
img_path = './test3.png'
img = Image.open(img_path)
img = img.convert("1")
img.show()
img = np.array(img)
if img.shape[0] != 120 or img.shape[1] != 320:
    print('image size must be 120*320')
    exit()
# %%
port ='/dev/cu.usbserial-140'
ser = initial(port)

# %%
duration = 0.045
step1(ser)

# for i in range(120):
#     for j in range(320):
#         img[i][j] = (i+j)%2

for i in range(120):
    if check_left(img, i, 0):
        if img[i][0] == False:
            push_button(ser, ['A'])
        
        for j in range(1, 320):
            if img[i][j] == False:
                push_button(ser, ['A', 'D_R'])
            else:
                push_button(ser, ['D_R'])
            if j < 319 and check_left(img, i, j+1) == False:
                break
        move_to_begin(ser, 3 * j / 320)
    push_button(ser, ['D_D'])

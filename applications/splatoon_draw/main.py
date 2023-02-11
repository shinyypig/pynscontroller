# import libs
from time import sleep
import numpy as np
from PIL import Image
import pynscontroller as pyns

# some parameters
# the UART port of the esp32 chip
port = '/dev/cu.usbserial-1110'
# the path of the image
img_path = './test.png'


# press L and R buttons to connect to switch
def connect_to_switch(controller):
    for _ in range(3):
        controller.press_button(['L', 'R'])
        sleep(0.5)


# initialize the drawing process
def inital(controller):
    # press L to switch to the smallest brush
    controller.press_button(['L'])
    # press LClick to clear the screen
    controller.press_button(['LClick'])
    # move the cursor to the left top corner
    controller.push_stick([0, 0, 127, 127], duration=3.5)


# move the cursor to the begin of the line
def move_to_begin(controller, duration=4):
    # set LX to 0
    controller.push_stick([0, 127, 127, 127], duration=duration)


# check if there are any pixels waiting for drawing on the right of the current pixel
def check_left_pixels(img, i, j):
    if np.uint(~img[i, j:]).sum() == 0:
        return False
    return True


# read the image
img = Image.open(img_path)
# convert the image to black and white with the dither algorithm
img = img.convert("1")
# display the image
img.show()
# convert the image to numpy array
img = np.array(img)
# check the image size
if img.shape[0] != 120 or img.shape[1] != 320:
    print('image size must be 120*320')
    exit()


# initialize the controller
controller = pyns.PyNSController(port)

# check if the controller object is None
if controller is None:
    print('Cannot connect to esp32, please check the port or replug the chip.')
    exit()

# connect to switch
while True:
    print('Esp32 is pressing L and R buttons to connect to switch, please remove the joycon.')
    connect_to_switch(controller)
    flag = input('Connected to swith, y or n?\n')
    if flag == 'y':
        break

# press A to confirm the controller in switch
controller.press_button(['A'])
sleep(2)

# initialize the drawing process
inital(controller)

# draw the image pixel by pixel
for i in range(120):
    if check_left_pixels(img, i, 0):
        if img[i][0] == False:
            controller.press_button(['A'])

        for j in range(1, 320):
            if img[i][j] == False:
                controller.press_button(['A', 'D_R'])
            else:
                controller.press_button(['D_R'])
            if j < 319 and check_left_pixels(img, i, j+1) == False:
                break
        move_to_begin(controller, 3 * j / 320)
    controller.press_button(['D_D'])

# close the controller
controller.close()

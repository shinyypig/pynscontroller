# PyNSController

PyNSController is a Python library for controlling the Nintendo Switch through a esp32 microcontroller.

## Installation

``` bash
pip install py-ns-controller
```

## Burn the firmware

The firmware is from [UARTSwitchCon](https://github.com/nullstalgia/UARTSwitchCon), you can also find it in bin/PRO-UART0.bin in this repo.

Generally, you need to install the esptool to flash the firmware.

``` bash
pip install esptool
```

Then, you can flash the firmware to the esp32 chip by the following command.

``` bash
python -m esptool --port "/dev/cu.usbserial-1110" --baud 230400 write_flash 0x0  "./PRO-UART0.bin"
```

Please remember replace the port and the fireware path with your own port and path.

## Usage

``` python
import pynscontroller as pyns
# the UART port of the esp32 chip
port = '/dev/cu.usbserial-1110'
# create a controller instance.
# If crontroller is not None, then the controller is successfully connected.
controller = pyns.PyNSController(port)
# press the L and R button, and release it after 0.045 seconds (the fastest).
controller.press_button(['L', 'R'])
# press the A button, and release it after 1 seconds.
controller.press_button(['A'], duration=1)
# push the left stick to the right for 1 seconds.
# the stick_list is [LX, LY, RX, RY], the range of each value is [0, 255].
controller.push_stick(stick_list=[0, 127, 127, 127], duration=1)

# if you want to long press the button while pushing the stick, you can use the following code.
press_button_and_stick(button_list=['A'], stick_list=[0, 127, 127, 127], duration=1)
# the above three functions return a flag, which is True if the controller is successfully connected.
flag = controller.press_button(['L', 'R'])
```

## Application

Based on pynscontroller, various applications can be developed, such as:

- [Splatoon 3 draw bot](./applications/splatoon_draw/)
- waiting for your application...

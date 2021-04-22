# GrowBotHub Gripper
 
This repository contains a Python class that allows to control the SCHUNK Gripper (EGH-80-IOL-N) via IO-Link using a TURCK Master Module (FEN20-4IOL).


## Setup

- Connect the TURCK Master Module P1 port to your computer using an Ethernet cable
- Connect the SCHUNK Gripper to the TURCK Master Module using the IO ports
- Connect the power supply of the TURCK Master Module to an electrical outlet

Once everything is connected, find out the IP adress of the TURCK Master Module. For this, download the [Turck Service Tool](https://www.turck.de/attachment/SW_Turck_Service_Tool.zip) and search for your device. The IP adress should be shown there.

## Usage of the class
The Gripper class uses a Python package called [PyModBus](https://pymodbus.readthedocs.io/en/latest/) that provides asynchronous communication using Modbus protocol. To download the Python package, execute this command in your terminal:

```sh
pip install pymodbus
```

To use the Gripper class, first create a Gripper object with the IP adress of the TURCK Master Module. Let's take 172.31.1.51 as an example for the IP adress, but **replace it with your IP adress**.

```python
from gripper import Gripper
gripper = Gripper('172.31.1.51') # Replace with YOUR IP adress
```

This will initiate a Modbus TCP client that allows to read or write registers from the TURCK Master Module.

The Gripper class contains several functions to control the gripper. It can grip, release, set the gripper to a position and stop. Examples on how to use these functions are shown below:

```python
gripper.grip(force=1) # Takes as an argument the gripper force which can be an integer from 1 to 4 (1:weakest, 4:strongest)
gripper.release()
gripper.set_position(25) # Takes as an argument the relative position in percent of the fingers (0: fingers closed, 100: fingers opened)
gripper.stop()
```

Additional information can be found in the datasheets of the [TURCK Master Module](https://www.turck.us/attachment/100009607.pdf) and the [SCHUNK Gripper](https://schunk.com/fileadmin/pim/docs/IM0024308.PDF)

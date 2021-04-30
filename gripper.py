from pymodbus.client.sync import ModbusTcpClient
import struct
import time


class Gripper:
    def __init__(self, ip_adress='172.31.1.51'):
        """ Initializes a Gripper object by using the specified IP adress.

        Parameters:
        ip_adress (str): IP adress of the TURCK Master Module. by default '172.31.1.51'.
                         See README.md file for informations about how to find the IP adress.

        """
        if not isinstance(ip_adress, str):
            raise Exception('ip_adress requires a string, the variable you entered is of type {}'.format(type(target_position)))

        self.POSITION_MAX = 40.683074951171875 # Maximum position amplitude of the finger in mm
        self.STATUS_ERROR = 0  # Error
        self.STATUS_OOS = 1  # Out of specification
        self.STATUS_MAINTENANCE = 2  # Maintenance required
        self.STATUS_READY = 3  # Ready for operation
        self.client = ModbusTcpClient(ip_adress)
        if not self.client.connect():
            raise Exception('Connection to the gripper failed: incorrect IP-adress')
        self.status = self.get_status()
        self.timeout(0)
        time.sleep(0.1)
        self.acknowledge()
        time.sleep(0.1)
        self.reference()

    def timeout(self, value):
        """ Does a time out on the gripper by specifying the duration value.
            By default, the value is 0, which means the Modbus connection will
            never be closed

        Parameters:
        value (int): argument to define after which time (in seconds) of inactivity
                     a Modbus connection is closed through a Disconnect.

        """
        self.client.write_register(0x1120, value)

    def acknowledge(self):
        """ After an error has been rectified, the gripper is set to the normal
            operating status by acknowledging the error from the error status.
            The actuator remains de-energized until the next command.

        Parameters:
        none

        """
        self.client.write_register(0x0801, 0x0100)
        time.sleep(0.1)
        self.client.write_register(0x0801, 0x8100)

    def reference(self):
        """ The zero position is set during the referencing process. The gripper
            moves (Parameter [} 26]) to the mechanical end stop in the
            referencing direction set.

        Parameters:
        none

        """
        self.handle_errors()
        self.client.write_register(0x0801, 0x0200)
        time.sleep(0.1)
        self.client.write_register(0x0801, 0x8200)

    def measure_stroke(self):
        """ Stroke measurement is an optional function. During the stroke
            measurement, the maximum stroke of the gripper is set relative to
            the referencing position. A stroke measurement should be
            performed if the stroke

        Parameters:
        none

        """

        self.handle_errors()
        self.client.write_register(0x0801, 0x0700)
        time.sleep(0.1)
        self.client.write_register(0x0801, 0x8700)

    def calibrate(self):
        """ Calibration is an optional function. For calibration, the functions
            "reference" and "measure_stroke" are performed one after
            the other. For modules with an absolute measuring system, the
            offset and slope are determined.

        Parameters:
        none

        """

        self.handle_errors()
        self.client.write_register(0x0801, 0x0900)
        time.sleep(0.1)
        self.client.write_register(0x0801, 0x8900)

    def grip(self, force=4):
        """ When gripping, movement follows the gripping direction to the
            stop and the workpiece is held. With electric grippers, the
            workpiece is held with the gripping force set.

        Parameters:
        force (int): optional argument to define the gripping force.
                     Must be between 1 (weakest) and 4 (strongest), by default 4.


        """
        if not isinstance(force, int):
            raise Exception('Force requires an int, the variable you entered is of type {}'.format(type(target_position)))

        self.handle_errors()

        if not (1 <= force <= 4):
            raise Exception('Force value out of range (Must be between 1 and 4)')

        self.client.write_registers(0x0801, [0x0400, (4 - force) * 0x0100, 0, 0])
        time.sleep(0.05)
        self.client.write_registers(0x0801, [0x8400, (4 - force) * 0x0100, 0, 0])
        self.wait_process_command()
        time.sleep(1)

        # Wait until the grip command is successful
        while self.success() != 1:
            time.sleep(0.05)

    def release(self):
        """ When releasing, movement occurs in the opposite direction to
            gripping, up until the end stop. The command signals success
            when the end stop is reached. The smallest gripping force
            adjustment is set for the releasing process.

        Parameters:
        none

        """

        self.handle_errors()
        self.client.write_registers(0x0801, [0x0300, 0, 0, 0])
        time.sleep(0.05)
        self.client.write_registers(0x0801, [0x8300, 0, 0, 0])
        self.wait_process_command()
        time.sleep(1)

        # Wait until the release command is successful
        while self.success() != 1:
            time.sleep(0.05)

    def set_position(self, target_position):
        """ The gripper moves to the position that was specified under
            "target_position". If the run is interrupted by a blockage,
            the drive switches off. An error message requiring acknowledgment
            is generated. The actuator remains de-energized until the next run
            command.

        Parameters:
        target_position (int): required argument to define the relative position of the fingers in percent.
                               Must be between 0 (fingers closed) and 100 (fingers opened).


        """
        if not isinstance(target_position, int):
            raise Exception('Target position requires an int, the variable you entered is of type {}'.format(type(target_position)))

        self.handle_errors()

        if not (0 <= target_position <= 100):
            raise Exception('Target position value out of range (between 0 and 100)')
        elif target_position < 3:
            self.grip()
            return
        elif target_position > 97:
            self.release()
            return

        position_mm = ((100 - target_position) / 100.) * self.POSITION_MAX
        # Convert the position to binary
        position_bin = format(struct.unpack('!I', struct.pack('!f', position_mm))[0], '032b')

        self.client.write_registers(0x0801, [0x0500, 0, int(position_bin[:16], 2), int(position_bin[16:], 2)])
        time.sleep(0.05)
        self.client.write_registers(0x0801, [0x8500, 0, int(position_bin[:16], 2), int(position_bin[16:], 2)])
        self.wait_process_command()

    def fast_stop(self):
        """ The electrical power supply to the actuator is interrupted
            immediately, the gripper is stopped uncontrolled. A FastStop
            occurs independently of the status change of the "Execution
            command" bit.
            An error message requiring acknowledgment is generated. A
            FastStop does not increase the error count and is not saved as the
            most recent error.

        Parameters:
        none

        """
        if self.get_status() == self.STATUS_ERROR:
            self.acknowledge()
        self.client.write_register(0x0801, 0x0000)

    def stop(self):
        """ The gripper is brought to a controlled standstill. The gripper
            remains in a controlled standstill while retaining the force
            provided in the previous command.

        Parameters:
        none

        """
        self.handle_errors()
        self.client.write_register(0x0801, 0x0800)
        time.sleep(0.1)
        self.client.write_register(0x0801, 0x8800)

    def disconnect(self):
        """ Disconnects the Modbus TCP Client

        Parameters:
        none

        """
        self.client.close()

    def get_status(self):
        """ Reads the operating status of the gripper
            0: Error
            1: Out of specification
            2: Maintenance required
            3: Ready for operation

        Parameters:
        none

        Returns:
        status (int): the operating status of the gripper

        """
        value = self.client.read_input_registers(0x0001).registers[0]
        self.status = int(bin(value)[2:].zfill(16)[5:8], 2)
        return self.status

    def success(self):
        """ Reads the success bit of the gripper. When a new command is executed,
            the "Success" bit is reset to 0. If the command is successful, the bit
            is set to 1.

        Parameters:
        none

        Returns:
        has_success (int): the success bit of the gripper

        """
        value = self.client.read_input_registers(0x0001).registers[0]
        has_success = int(bin(value)[2:].zfill(16)[1], 2)
        return has_success

    def get_position(self):
        """ Reads the relative position in percent of the fingers.

        Parameters:
        none

        Returns:
        position_perc (int): the relative position in percent

        """
        result = self.client.read_input_registers(0x0003, 2)
        position_bin = bin(result.registers[0])[2:].zfill(16) + bin(result.registers[1])[2:].zfill(16)
        position_mm = struct.unpack('!f', struct.pack('!I', int(position_bin, 2)))[0]  # position in mm
        position_perc = int(((self.POSITION_MAX - position_mm) / self.POSITION_MAX) * 100)
        return position_perc

    def wait_process_command(self):
        """ Waits until the current command has been processed. Process command = 1 if
        the execute command is 1 and the process data has been processed.
        Process command = 0 if the execute command changes to 0.

        Parameters:
        none

        """
        for i in range(1000):
            value = self.client.read_input_registers(0x0001).registers[0]
            process_command = int(bin(value)[2:].zfill(16)[0], 2)
            if value > 2 ** 15 - 1:
                return
        self.timeout(1)
        time.sleep(0.1)
        self.timeout(0)
        time.sleep(0.1)
        self.acknowledge()

    def handle_errors(self):
        """ Handles errors of the gripper by acknowledging the error. If the error is
            of type "Out of specification", the gripper is timed out (rebooted) and
            then acknowledged.

        Parameters:
        none

        """

        self.get_status()
        if self.status == self.STATUS_ERROR:
            self.acknowledge()
            time.sleep(0.1)
        elif self.status == self.STATUS_OOS:
            self.timeout(1)
            time.sleep(0.1)
            self.timeout(0)
            time.sleep(0.1)
            self.acknowledge()
            time.sleep(0.1)

"""
Given:
  Distance = value/1024 * stroke
  Stroke is max extension length
  All values in mm
  0 and 1023 are the mechanical stops **BAD**
  Max Speed = 46 mm/s
  Stroke = 300mm

Notes:
  DO NOT set the rLimit or eLimit to their respective mechanical stops
    (Unless you want to possibly break the Linear Actuator)

  Functions not used in our Actuonix Linear Actuator from 'lac.py':
    linearActuator.set_proportional_gain()
    linearActuator.set_derivative_gain()
    linearActuator.disable_manual() DONT TOUCH THIS PL0x

    Both of these didn't do anything when tested:
      piston.set_average_rc(?) [0, 1024]
      piston.set_average_adc(?) [0, 1024]
"""

from .lac import LAC
import time
import logging

# Default IDs
vendor_id = 0x4D8
product_id = 0xFC5F

# Retract
r_limit = 1  # Retract limit
r_position = 1  # Ideal retract position
r_mech_stop = 0  # Mechanical stop of retract

# Extend
e_limit = 1022  # Extend limit
e_position = 1022  # Ideal extend position
e_mech_stop = 1023  # Mechanical stop of extend

# Additional Values
max_pwm = 1022
min_pwm = 1
stall_time = 1000  # 1000ms (1 second)
move_thresh = 5  # Movement threshold
acc_val = 4  # Accuracy value
max_speed = 1022
sleep_val = 6  # 6 seconds
stroke = 300  # max length of LAC (mm)


class WrappedLAC:
    def __init__(self):
        # Ensures the LAC will not hit mechanical stops
        if r_position <= r_mech_stop:
            raise Exception("Retract is set to the mechanical stop.")
        elif e_position >= e_mech_stop:
            raise Exception("Extend is set to the mechanical stop.")

        try:
            self.piston = LAC(vendor_id, product_id)
            self.setup()
        except Exception:
            logging.error("Failed to connect to the piston")

    # Automatically sets up the LAC
    def setup(self):

        # Retract limit set to 1mm (0-1023)
        self.piston.set_retract_limit(r_limit)
        print("Retract limit set")

        # Extend limit set to 1022mm (0-1023)
        self.piston.set_extend_limit(e_limit)
        print("Extend limit set")

        # How close to target is acceptable
        self.piston.set_accuracy(acc_val)
        print("Accuracy set")

        # Min speed (mm/s) before stalling
        self.piston.set_movement_threshold(move_thresh)
        print("Movement Threshold set")

        # Stall time (ms) set to 1 second
        self.piston.set_stall_time(stall_time)
        print("Stall Time set")

        # [1,1022]
        self.piston.set_max_pwm_value(max_pwm)
        print("Max PWM set")

        # [1,1022]
        self.piston.set_min_pwm_value(min_pwm)
        print("Min PWM set")

        # Keep on max speed [1,1022]
        self.piston.set_speed(max_speed)
        print("Piston set to max speed")

    # Extends the LAC to the max value without hitting mechanical stop
    # Takes 5 seconds to fully extend
    def extend(self):
        print("Extending...")
        if self.piston:
            self.piston.set_position(e_limit)
        time.sleep(sleep_val)  # Wait 6.5 seconds during extension

    # Retracts the LAC to the max value without hitting mechanical stop
    # Takes 5 seconds to fully retract
    def retract(self):
        if self.piston:
            self.piston.set_position(r_limit)
        time.sleep(sleep_val)  # Wait 6.5 seconds during retraction

    # Returns the current location of the LAC from [rLimit, eLimit]
    # Prints the metric location (mm) of LAC
    def position(self):
        if self.piston is None:
            return -1
        actual_pos = int(self.piston.get_feedback())  # Actual 2-bit position
        distance = (actual_pos * stroke) / e_limit  # Calculate metric distance
        print(str(distance) + "mm")
        return actual_pos

    # Retracts LAC to the original position
    # Factory reset to solve stalling issue
    def reset(self):
        print("Resetting...")
        self.retract()
        if self.piston:
            self.piston.reset()

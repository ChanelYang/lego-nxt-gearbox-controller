#!/usr/bin/env python3

import statistics
import matplotlib.pyplot as plt
import numpy as np
import pyfftw
from cued_ia_lego import *


# Try to find connected brick
try:
    brick = NXTBrick()
except Exception:
    exit()

# Set up parameters for the drive motor
motor_drive = Motor(brick, PORT_A, power=-80, smoothstart=False,
                    speedreg=False)

# Set up parameters for the shift motor
motor_shift = Motor(brick, PORT_B, power=0, smoothstart=False, speedreg=True, brake=True, hold=True)

# Touch sensors connected to sensor ports 1 and 2
touch_1 = Touch(brick, PORT_1)
touch_2 = Touch(brick, PORT_2)

# Ultrasonic sensor connected to sensor port 4
ultrasonic = Ultrasonic(brick, PORT_4)

# Light sensor connected to sensor port 3
# Use active mode (i.e. LED on)
light = Light(brick, PORT_3, illuminated=True)

# Initialize state variables
shift_power = 50
# Extra amount to shift when changing shift direction, edit to match your model
shift_backlash = 10  # degrees
# For shifting 1-2, 2-3, 3-4 and 4-5, edit to match your model
shift_degrees = [-180, -180, -160, -180]  # degrees
gear = 1  # current gear - assume start in gear 1
last_shift = ''  # keep track of last shift 'up' or 'down', start unset
finished = False
ultrasonic_triggered = False
automatic_shift_pending = False
pyfftw.interfaces.cache.enable()

# Initialise the various plots
times = []
speed_record = []
light_record = []
ultrasonic_readings = []
plt.figure(2)
plt.clf()
plt.figure(3)
plt.clf()
plt.figure(1)
plt.clf()
plt.figure(4)
plt.clf()
plt.xlabel('time (s)')
plt.ylabel('drive motor speed (rpm)')
plt.grid()

# Start the drive motor
motor_drive.reset_position()
motor_drive.run()

# Loop indefinitely, until both sensors are pressed at the same time
t_interval_start = time.perf_counter()
run_time = 0
while not finished:
    # Record the light sensor reading every iteration
    gear_changed = False
    interval_time = time.perf_counter() - t_interval_start
    times.append(run_time + interval_time)
    light_record.append(light.get_lightness())
    distance = ultrasonic.get_distance()
    ultrasonic_readings.append(distance)

    # Measure the drive motor speed every second
    if interval_time > 1:
        pos = motor_drive.get_position()
        current_speed = abs(pos / interval_time) * 60/360
        speed_record.append(current_speed)
        if len(speed_record) > 1:
            plt.figure(1)
            plt.plot([run_time, run_time + interval_time],
                     speed_record[-2:], 'r')
            plt.xlim(0, 300)
            plt.ylim(0, 200)
            plt.pause(0.1)  # forces the figure to draw now
        run_time += interval_time
        motor_drive.reset_position()
        t_interval_start = time.perf_counter()

    # Emergency stop, do not change gear
    if distance < 5:
        ultrasonic_triggered = True
        automatic_shift_pending = False
        motor_drive.idle()

    elif distance <= 15 and not ultrasonic_triggered:
        ultrasonic_triggered = True
        automatic_shift_pending = True
        motor_drive.run(-60)

    # Resume normal speed after the object moves away
    elif distance > 15 and ultrasonic_triggered:
        ultrasonic_triggered = False
        automatic_shift_pending = False
        motor_drive.run(-100)

    # Check for sensor 1
    if touch_1.is_pressed():
        # Wait until sensor 1 is released. If sensor 2 is pressed in the
        # meantime, break out of the loops.
        while touch_1.is_pressed():
            if touch_2.is_pressed():
                finished = True
                break
        if finished:
            break

        # If only sensor 1 was pressed, shift up one gear
        if gear < 5:
            turn_degrees = shift_degrees[gear - 1]
            gear += 1
            # If last shift was down, account for backlash
            if last_shift == 'down':
                turn_degrees += shift_backlash
            motor_shift.turn(turn_degrees, -shift_power)
            motor_shift.wait_for()
            brick.play_tone(1200, 200)
            gear_changed = True
            last_shift = 'up'

    # Check for sensor 2
    if touch_2.is_pressed():
        # Wait until sensor 2 is released. If sensor 1 is pressed in the
        # meantime, break out of the loops.
        while touch_2.is_pressed():
            if touch_1.is_pressed():
                finished = True
                break
        if finished:
            break

        # If only sensor 2 was pressed, shift down one gear
        if gear > 1:
            gear -= 1
            turn_degrees = shift_degrees[gear - 1]
            # If last shift was up, account for backlash
            if last_shift == 'up':
                turn_degrees += shift_backlash
            motor_shift.turn(turn_degrees, shift_power)
            motor_shift.wait_for()
            brick.play_tone(1200, 200)
            gear_changed = True
            last_shift = 'down'

    # If ultrasonic sensor triggered and gear has not changed in the current
    # cycle, change gear to increase torque
    if gear > 1 and not gear_changed and automatic_shift_pending:
        gear -= 1
        turn_degrees = shift_degrees[gear - 1]
        # If last shift was up, account for backlash
        if last_shift == 'up':
            turn_degrees += shift_backlash
        motor_shift.turn(turn_degrees, shift_power)
        motor_shift.wait_for()
        brick.play_tone(1200, 200)
        gear_changed = True
        last_shift = 'down'
    automatic_shift_pending = False

    # Display current gear
    if gear_changed:
        print(f'Now in gear {gear}')

    # Analyse the periodicity of the light sensor reading at every gear change,
    # as long as we have sufficient readings.
    if gear_changed and (len(times) > 100):

        print('Calculating power spectrum of light sensor readings ...')

        # Fourier transform to find the power spectrum. Remove the 0 Hz
        # component, which otherwise dominates the spectrum.
        samples = [l - statistics.mean(light_record) for l in light_record]
        sampling_frequency = 1 / statistics.median(diff(times))
        Y = pyfftw.interfaces.numpy_fft.rfft(samples)
        power = abs(Y) ** 2
        freq = (sampling_frequency / 2) * np.linspace(0, 1, len(Y))

        # Plot the zero-mean light sensor readings
        plt.figure(2)
        plt.clf()
        plt.plot(times, samples)
        plt.grid()
        plt.xlabel('time (s)')
        plt.ylabel('light sensor reading')
        plt.title('zero-mean light sensor readings')
        plt.pause(0.1)  # forces the figure to draw now

        # Plot the power spectrum
        plt.figure(3)
        plt.clf()
        plt.plot(freq, power)
        plt.grid()
        plt.xlabel('frequency (Hz)')
        plt.ylabel('power')
        plt.title('Power spectrum of light sensor reading')
        plt.pause(0.1)  # forces the figure to draw now

        plt.figure(4)
        plt.clf()
        plt.plot(times, ultrasonic_readings)
        plt.xlabel('time (s)')
        plt.ylabel('Distance (cm)')
        plt.title('Ultrasonic sensor distance')
        plt.pause(0.1)

        light_record = []
        times = []
        ultrasonic_readings = []
        print('... done')

# Stop the drive motor, release the shift motor brake
motor_drive.idle()
motor_shift.idle()

# Turn off LED
light.set_illuminated(False)

if speed_record:
    # Rescale the drive motor speed graph
    plt.figure(1)
    plt.xlim(0, 1.1 * max(times))
    plt.ylim(0, 1.1 * max(speed_record))
    plt.title('Motor Speed')

    # Wait for plots to close
    print('Close the plots to finish')
    plt.show()

# LEGO NXT Five-Speed Gearbox Controller

A Python controller for a five-speed LEGO NXT gearbox. It supports manual gear changes, automatic downshifting when the ultrasonic sensor detects an approaching obstacle, an emergency stop, and live plots of motor speed and sensor data.

## Features

- Five forward gears with configurable shift angles
- Manual up/down shifting with two touch sensors
- Backlash compensation when shift direction changes
- Automatic downshift for extra torque near an obstacle
- Emergency stop at very close range
- Live motor-speed, light-sensor, and distance plots
- Light-sensor frequency analysis using a fast Fourier transform (FFT)

## Hardware setup

| Component | NXT port |
| --- | --- |
| Drive motor | A |
| Gear-shift motor | B |
| Shift-up touch sensor | 1 |
| Shift-down touch sensor | 2 |
| Light sensor | 3 |
| Ultrasonic sensor | 4 |

Press both touch sensors together to stop the program safely.

## Requirements

- Python 3
- A connected LEGO NXT brick
- `cued_ia_lego` (provided by the Cambridge Engineering LEGO teaching environment)
- NumPy, Matplotlib, and pyFFTW

Install the public Python dependencies with:

```bash
python3 -m pip install -r requirements.txt
```

The `cued_ia_lego` package must be installed separately from the teaching environment used with the NXT hardware.

## Running

Connect the components to the ports above, then run:

```bash
python3 gearbox_controller.py
```

Before running on a different gearbox, calibrate these values near the top of the script:

- `shift_backlash`: extra rotation used after changing shift direction
- `shift_degrees`: motor rotation required between each pair of gears
- `shift_power`: shift-motor power

Keep the gearbox clear while testing. The drive motor starts as soon as the program connects to the brick.

## Control behaviour

- Press sensor 1 to shift up.
- Press sensor 2 to shift down.
- At 15 cm or less, the controller slows the drive and downshifts once.
- Below 5 cm, the controller stops the drive motor.
- Once the obstacle moves beyond 15 cm, normal drive speed resumes.

## Notes

This project controls physical hardware. Test at low power first and keep an accessible way to disconnect the NXT brick.

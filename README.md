
# BMT Vehicle Display

**A Raspberry Pi-based digital dashboard and in-vehicle display for BMT
MACH Hidromobil**

A PySide6 application designed to present vehicle telemetry and provide
a simple touchscreen interface for selected vehicle settings.
:::

------------------------------------------------------------------------

## Overview

BMT Vehicle Display is the in-vehicle Human-Machine Interface (HMI) for
the BMT MACH Hidromobil project. It is designed to run on a **Raspberry
Pi** connected to a **7-inch Waveshare touchscreen**.

The application receives telemetry from the vehicle electronics over a
serial connection, converts the incoming data into dashboard values, and
displays them through a custom Qt interface. It also provides a settings
page where the driver or operator can adjust the battery--hydrogen
energy-use ratio and send the selected values to the vehicle controller.

The project is built with **Python and PySide6 (Qt for Python)**. Qt
Designer is used for the main interface layout, while custom-painted Qt
widgets provide the dashboard gauges.

## Key Features

-   **Digital dashboard:** Vehicle information presented in a dedicated
    dashboard interface.
-   **Custom gauges:** Circular speed and RPM gauges, a vertical
    energy/fuel bar, and a digital gear indicator.
-   **Serial telemetry:** Background serial communication using PySerial
    and a Qt worker thread.
-   **Telemetry parsing:** Delimited packets are buffered and parsed
    into structured vehicle data.
-   **Touchscreen settings:** A slider and adjustment buttons allow the
    battery/hydrogen usage ratio to be selected.
-   **Explicit settings submission:** The selected ratio is transmitted
    only after the confirmation button is pressed.
-   **Connection feedback:** Serial connection status and errors are
    displayed in the application.
-   **Custom visual styling:** A shared Qt Style Sheet (`style.qss`)
    defines the application appearance.
-   **Startup overlay:** A logo/title splash overlay fades out to reveal
    the dashboard.
-   **Debug mode:** A local mode provides sample gauge values without
    requiring live telemetry.

## Target Hardware

  Component               Target
  ----------------------- -------------------------------------------------
  Host computer           Raspberry Pi
  Display                 7-inch Waveshare touchscreen
  Display resolution      1024 × 600 (application window target)
  Input                   Touchscreen
  Vehicle communication   UART / serial connection
  Operating system        Raspberry Pi OS / compatible Linux distribution

> **Hardware note:** The application currently sets its window to 1024 ×
> 600 pixels. Confirm the resolution and touch configuration for the
> exact Waveshare display revision and Raspberry Pi image being used.

## Software Stack

-   Python 3
-   PySide6
-   Qt Widgets
-   Qt Designer (`.ui` interface file)
-   Qt Style Sheets (QSS)
-   PySerial
-   Qt signals, slots, timers and `QThread`

## Repository Structure

``` text
bmt-vehicle-display/
│
├── assets/
│   ├── images/                  # Logos and images
│   └── icons/                   # UI icons
│
├── main.py                      # Application entry point
├── mainwindow.ui                # Qt Designer UI layout
├── GaugeBars.py                 # Custom dashboard gauge widgets
├── SerialTelemetryManger.py     # Serial communication and telemetry handling
├── style.qss                    # Application stylesheet
├── requirements.txt             # Python dependencies
└── README.md                    # Project documentation
```

### Main Components

#### `main.py` --- Application and UI Controller

The main application module is responsible for:

-   Creating and loading the Qt application interface with `QUiLoader`.
-   Applying the global QSS stylesheet.
-   Managing navigation between the dashboard and settings pages through
    a `QStackedWidget`.
-   Creating and embedding the custom gauge widgets in their UI
    containers.
-   Connecting UI controls to their corresponding actions.
-   Receiving telemetry through Qt signals and updating the dashboard.
-   Managing the splash overlay and application shutdown.

The main window is currently configured for a 1024 × 600 display.

#### `mainwindow.ui` --- User Interface Layout

The main interface is designed in Qt Designer and loaded at runtime. It
contains the dashboard and settings pages, their controls, labels,
containers and status bar.

Keeping the layout in a separate `.ui` file makes it possible to modify
the visual structure without rewriting the application controller.

#### `GaugeBars.py` --- Custom Dashboard Widgets

This module contains custom Qt widgets drawn with `QPainter`. The
current dashboard components include:

-   `SpeedCircularGauge` --- circular speed display.
-   `RpmCircularGauge` --- circular RPM display.
-   `VerticalFuelBar` --- vertical energy/battery-style indicator with
    supporting values.
-   `DotMatrixShifter` --- digital gear indicator.

The widgets expose methods for updating their displayed values, allowing
the main application to keep telemetry handling separate from drawing.

#### `SerialTelemetryManger.py` --- Serial Communication

`SerialTelemetryManager` is implemented as a `QThread` subclass. It
opens the serial port in its worker thread, reads incoming bytes,
accumulates them in a receive buffer and extracts complete packets using
configured header and footer delimiters.

Valid telemetry is emitted to the UI through the `telemetry_received` Qt
signal. Connection changes and serial errors are reported through
`connection_status`.

The module also provides methods for sending telemetry-shaped test
packets and battery/hydrogen ratio settings.

> The filename is currently spelled `SerialTelemetryManger.py` in the
> repository. The README uses the existing filename so imports remain
> consistent.

## Dashboard Data

The serial parser currently expects **seven comma-separated numeric
fields** in each telemetry payload.

    Field order Key                 Meaning                 Unit / representation
  ------------- ------------------- ----------------------- -------------------------
              1 `speed`             Vehicle speed           km/h
              2 `battery_voltage`   Battery voltage         V
              3 `battery_current`   Battery current         A
              4 `battery_temp`      Battery temperature     °C
              5 `charge_power`      Charging power          W (as displayed)
              6 `insulation_res`    Insulation resistance   Ω (as displayed)
              7 `gear`              Gear selection          `-1`: R, `0`: N, `1`: D

### Telemetry Packet Format

The current receive format uses:

``` text
<payload>
```

Example:

``` text
<65.0,54.2,18.5,34.0,0.0,500.0,1>
```

The parser extracts the text between `<` and `>`, splits it by commas
and accepts the packet only when it contains exactly seven values that
can be converted to numbers.

The receive loop runs in a worker thread, so serial reading does not
need to be performed directly in the GUI event loop.

### Battery / Hydrogen Ratio Setting

The settings page provides a 0--100 slider. The selected value
represents the battery usage percentage; the hydrogen percentage is
calculated as the complement:

``` text
Battery:  60%
Hydrogen: 40%
```

The settings packet is sent when the confirmation button is pressed:

``` text
$60,40>
```

This command uses `$` as its start delimiter to distinguish it from
telemetry packets, which start with `<`.

**Important:** This is the packet format currently implemented in the
application. The vehicle controller firmware must use the same field
order, delimiters, units and interpretation. Confirm the protocol with
the ECU firmware before connecting the display to a live vehicle.

## Installation

### 1. Prepare the Raspberry Pi

Install Raspberry Pi OS (or another compatible Linux distribution),
configure the Waveshare touchscreen and make sure the display is
operating at the intended resolution.

Update the package lists:

``` bash
sudo apt update
sudo apt upgrade -y
```

Install Python and virtual-environment support if they are not already
available:

``` bash
sudo apt install -y python3 python3-pip python3-venv
```

### 2. Clone the Repository

``` bash
git clone https://github.com/mertkaplandar/bmt-vehicle-display.git
cd bmt-vehicle-display
```

### 3. Create a Virtual Environment

``` bash
python3 -m venv .venv
source .venv/bin/activate
```

### 4. Install Dependencies

The current `requirements.txt` lists PySide6. The serial communication
module also imports PySerial, so install both packages:

``` bash
pip install --upgrade pip
pip install PySide6 pyserial
```

If you maintain the dependency file, add `pyserial` to
`requirements.txt` so a fresh installation can be completed with:

``` bash
pip install -r requirements.txt
```

### 5. Configure Serial Communication

Before running the application, check the serial configuration in
`main.py`.

The current application startup creates the serial manager with:

``` python
self.uart = SerialTelemetryManager(
    port="COM3",
    baudrate=9600,
    header="<",
    footer=">"
)
```

`COM3` is a Windows-style example and will not normally be the correct
device name on Raspberry Pi OS. A Raspberry Pi serial device may appear
as `/dev/serial0`, `/dev/ttyAMA0` or `/dev/ttyUSB0`, depending on the
connection method and system configuration.

For example:

``` python
self.uart = SerialTelemetryManager(
    port="/dev/serial0",
    baudrate=9600,
    header="<",
    footer=">"
)
```

Use the actual port and baud rate configured in the vehicle controller.
The `SerialTelemetryManager` class has a default baud rate of 115200,
while the current `main.py` startup explicitly passes 9600; therefore,
the explicit application configuration takes precedence.

On Linux, serial-port permissions may also be required. Check the device
and the user/group permissions before launching the application. Do not
assume that every Raspberry Pi OS installation uses the same serial
device name or permission configuration.

### 6. Run the Application

``` bash
python3 main.py
```

For development on a desktop computer, use a compatible Python
environment with PySide6 and PySerial installed. The application
currently uses a fixed 1024 × 600 window, so a matching display
resolution is recommended.

## Touchscreen Interaction

The settings page currently exposes the battery/hydrogen usage ratio:

1.  Open the settings page.
2.  Adjust the ratio using the slider or the increment/decrement
    controls.
3.  Review the displayed battery and hydrogen percentages.
4.  Press the confirmation button to transmit the selected values over
    serial.

Changing the slider updates the values shown in the interface. It does
**not** immediately transmit a command; transmission occurs on
confirmation.

## Development and Testing

The application includes a debug mode in `VehicleDashboard`. When debug
mode is enabled, the periodic UI update uses sample values for the
dashboard gauges. This is useful for checking the visual interface
without a live vehicle connection.

The current periodic dashboard timer is configured for 100 ms (10
updates per second). This timer is separate from the serial worker
thread, which continuously checks for incoming data.

For safe development:

-   Test the UI with debug values before connecting vehicle electronics.
-   Test serial communication with a USB-to-UART adapter or a dedicated
    simulator.
-   Verify packet delimiters, field order, baud rate and units against
    the controller firmware.
-   Test invalid, incomplete and fragmented packets.
-   Verify the settings command on a bench setup before using it with
    the vehicle.
-   Confirm that the application exits cleanly and releases the serial
    port.

## Current Implementation Notes

This repository represents an actively developed project. The following
details are important when evaluating the current code:

-   The serial port and baud rate are currently configured in `main.py`;
    they are not yet exposed as a user-facing connection configuration.
-   The receive parser accepts exactly seven comma-separated numeric
    values and silently ignores malformed payloads.
-   The telemetry protocol currently uses simple start/end delimiters.
    It does not currently implement a checksum, sequence counter or
    message identifier.
-   Battery state-of-charge and remaining-energy values are estimated in
    `main.py` using fixed voltage and capacity constants. These values
    must be calibrated for the actual battery pack before being treated
    as meaningful vehicle measurements.
-   Debug mode uses fixed demonstration values; these are not live
    vehicle measurements.
-   The current dependency file lists PySide6, while serial
    communication also requires PySerial.
-   The application uses a fixed window size. Fullscreen startup,
    automatic launch on boot and deployment hardening should be
    configured for the final Raspberry Pi installation.

## Safety and Operational Notice

This application is an in-vehicle display and operator interface. It
should not be treated as a safety-critical control system or as the sole
source of information for vehicle protection.

All telemetry values, units, limits and settings commands must be
validated against the vehicle's electronic control system. Communication
loss, invalid data and application failure must not compromise the
vehicle's independent protection mechanisms. Test changes on a bench
setup before deploying them to the vehicle.

## Contributing

Contributions, bug reports and suggestions are welcome. When proposing
changes, include the affected hardware, operating system, Python version
and steps to reproduce the issue where applicable.

------------------------------------------------------------------------

**BMT MACH --- Hidromobil**

*Vehicle Display & Touchscreen Interface*


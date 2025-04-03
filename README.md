# Autokinesis Tracker UI | aktrack-slicer

This repository contains the Control Room module for the Autokinesis Tracker system, built as a 3D Slicer extension. It provides a centralized interface for controlling experiment protocols, monitoring eye tracking, and visualizing results.

![demo_5min_data](https://github.com/bingogome/aktrack-slicer/blob/main/demo_5min_data.gif)

## Overview

The Autokinesis Tracker User Interface (aktrack-slicer) is the main control center of the Autokinesis Tracker system. It integrates with other system components (eye tracking goggles and visual stimuli screens) to coordinate experimental paradigms for tracking eye movements and measuring visual perception.

## Features

- **Subject Management**: Create and manage subject records
- **Experiment Control**: 
  - Generate randomized experiment sequences
  - Control trial execution (start, stop, navigate between trials)
  - Real-time experiment timing
- **Visualization**: 
  - Monitor tracker position in 3D
  - Replay recorded tracking data
  - Create video recordings of tracking sessions
- **Multiple Paradigm Support**:
  - VPB (Visual Perception of Bias) - Stationary dot paradigms
  - VPM (Visual Perception of Motion) - Moving dot paradigms with variable speeds
  - VPC (Visual Perception Calibration) - System calibration paradigms
- **Network Communication**: Coordinate all system components (goggles, screen display, trackers)

## System Requirements

- **Software**:
  - [3D Slicer](https://download.slicer.org/) (version 4.10 or later)
  - Python 3.6+
  - Qt 5.12+
- **Hardware**:
  - Computer running Windows/macOS/Linux
  - Network connection to other Autokinesis Tracker components
  - Recommended: Dual monitors (for control interface and visualization)

## Installation

1. Install 3D Slicer from [download.slicer.org](https://download.slicer.org/)

2. Clone this repository:
   ```
   git clone https://github.com/bingogome/aktrack-slicer.git
   ```

3. Add the module to 3D Slicer:
   - Launch 3D Slicer
   - Go to Edit -> Application Settings -> Modules
   - Add the path to the cloned repository as an "Additional module path"
   - Restart 3D Slicer

4. Load the module:
   - In 3D Slicer, navigate to Modules -> AkTrack -> Control Room

## Usage

### Setting Up an Experiment

1. Connect to system components:
   - Enter the IP addresses and ports in the "Connections" section
   - Click "Connect" to establish connections with eye-tracking goggles and visual stimuli screens

2. Create or select a subject:
   - Enter subject acronym in the "Add a Subject" field and click "Add"
   - Or select an existing subject from the dropdown menu

3. Initialize an experiment:
   - Click "Start an Experiment" to create a new experimental session
   - Generate a random trial sequence with "Generate Random Sequence"
   - Review and optionally edit the sequence in the text area
   - Click "Apply Sequence" to save and activate the sequence

### Running Experiments

1. Navigate between trials:
   - Use "Perform Current Trial" to run the trial shown in "Current Trial"
   - Use "Perform Previous Trial" to repeat the previous trial
   - Use "Stop Current Trial" to halt an ongoing trial
   - Select any trial from the dropdown and use "Perform Target Trial"

2. Control system visualization:
   - Click "Start Visualization" to see real-time tracker position
   - Use the visualization to help position subjects and verify system operation

3. Replay and analyze data:
   - Select a data file using the file selection dialog
   - Set replay speed (default 1.0x)
   - Click "Replay" to visualize recorded data
   - Use "Replay and Record" to create video files of visualizations

## Experiment Protocols

The system supports three main experiment types:

1. **VPB (Visual Perception of Bias)**: 
   - Stationary dot paradigms in two variants:
     - VPB-hfixed: Head fixed (stationary)
     - VPB-hfree: Head freely moving

2. **VPM (Visual Perception of Motion)**:
   - Moving dot paradigms with various speeds and directions
   - Format: VPM-[speed]-[direction]
   - Speeds: 2, 4, 6, 8, 12, 18 deg/sec
   - Directions: L (left), R (right), U (up), D (down)

3. **VPC (Visual Perception Calibration)**:
   - Constant-speed paradigms for system calibration
   - Format: VPC-[direction]
   - Fixed speed of 2 deg/sec

## Network Architecture

The UI coordinates communication across several components:
- Eye tracking goggles (aktrack-goggle)
- Visual stimuli screen (aktrack-screen)
- Motion tracking system (aktrack-ros)

The communication happens through UDP sockets with the following default ports:
- 8753, 8769, 8757: Visual stimuli screen
- 8057, 8059, 8083: Motion tracking system
- 8297, 8293: Eye tracking goggles

## Data Management

Experiment configurations and sequences are stored in JSON format within the `Resources/Configs/SubjectConfig.json` file. Each subject entry contains:
- Subject acronym
- List of experiment sessions with timestamps
- Sequence of trials for each session

## Troubleshooting

- **Connection Issues**: Verify IP addresses and ports in the connection settings
- **Missing Components**: Ensure all system components (goggles, screen) are powered on and running
- **Sequence Errors**: Check for proper syntax in trial sequences (e.g., VPM-8-L)

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Cite

@article{liu2024autokinesis,
  title={Autokinesis Reveals a Threshold for Perception of Visual Motion},
  author={Liu, Yihao and Tian, Jing and Martin-Gomez, Alejandro and Arshad, Qadeer and Armand, Mehran and Kheradmand, Amir},
  journal={Neuroscience},
  volume={543},
  pages={101--107},
  year={2024},
  publisher={Elsevier}
}

## Related Projects

- [aktrack-goggle](https://github.com/bingogome/aktrack-goggle) - Eye tracking module
- [aktrack-screen](https://github.com/bingogome/aktrack-screen) - Visual stimuli module

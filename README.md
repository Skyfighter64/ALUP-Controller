# ALUP-Controller
An interactive commandline ALUP Sender.

This is a tool to use, debug, and work with ALUP devices.
(Currently only over serial connection)

Features:
- Set RGB colors of leds
- Read ALUP Configuration

# Note:
This project is WIP and currently still buggy.

## Install
Use this to clone the repo and also clone the [Python-ALUP](https://github.com/Skyfighter64/Python-ALUP) submodule:\
`git clone --recurse-submodules https://github.com/Skyfighter64/ALUP-Controller.git`\
or
- `git clone https://github.com/Skyfighter64/ALUP-Controller.git`
- `cd ALUP-Controller`
- `git submodule update --init`

## Usage:
`python3 ALUP-Controller.py`

Type `help` to see available commands


## Unit Testing:
Use `python -m unittest .\tests\test_effects.py` for single test file, `python -m unittest discover -s tests/` to run all tests


## Add new effects:
To add new effects, simply add a function in effects.py. This fucntion has to comply with the properties listed there.\

To apply the effect: 
- connect to the ALUP Device
- use `effect <function name> <optional params>` to apply the effect

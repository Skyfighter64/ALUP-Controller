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

### Dependencies:
Install the [Python-ALUP](https://github.com/Skyfighter64/Python-ALUP) package via pip:
1. Clone the repository into any folder:
```sh
git clone git@github.com:Skyfighter64/Python-ALUP.git
```
2. Do development install (for now)
```sh
pip install -e ./Python-Alup/
```

## ALUP Controller
Clone the git repository into any folder.
```sh
git clone git@github.com:Skyfighter64/ALUP-Controller.git
```
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

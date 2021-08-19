# Alicpt Workspace Readme

 

## Installation & required package
All are installed in Window.
* Python3
    * pysftp
    * numpy
    * ntplib
    * newportxps 
    * Install others as prompted

### Installation with Git
```
git clone https://github.com/ttlaz123/alicpt_workspace.git
git submodule update --init --recursive ## clone newportxps
```
### Resource
https://github.com/pyepics/newportxps

## Outline of Alicpt Workspace
### Alicptfts
[![hackmd-github-sync-badge](https://hackmd.io/28NNL4k8RVC3ogB8J0pbZQ/badge)](https://hackmd.io/28NNL4k8RVC3ogB8J0pbZQ)

The alicptfts software is run under Window OS.
Alicptfts is mainly written by python3. [PyCharm](https://www.jetbrains.com/pycharm/download/#section=windows) and [Visual Studio](https://visualstudio.microsoft.com/free-developer-offers/) 
is recommend as the develop IDE. Other IDE supporting Git is also good to use.

The code is maintained by Shu-Xiao and controls the three groups for the Fourier Transform Spectrometer
### Rastor_Scanner
The code is maintained by Laura Futamura and contains the functions for determining the topology of plates.
### Hexachamber
The code is maintained by Tom Liu. Contains the code necessary for manual control of the Hexapod with the keyboard, while simultaneously controlling the movement of a newportxps positioner.

Quick start:
```
python hexachamber.py -p xxxxxx -q xxxxxx
```
More detailed instructions:
* Instructions for startup
    * Enter the folder where `hexachamber.py` is saved, and see the program input options with `python hexachamber.py -h`. 
        * The code connects to two different NewportXPS machines, one controlling the Hexapod, and one controlling the positioner.
    * Identify the IP and password for the Hexapod and Positioner. Typically the IP is either `192.168.0.254` or `192.168.254.254`, and are stored as the default values, so they do not need to be entered unless the physical setup has changed.
    * Use the `-r` flag if the positioner and hexapod need to be reinitialized, or have not yet been initialized. This process typically takes some time to perform, so if the NewportXPS machines are already up and running, this flag isn't necessary. This can be checked by opening the control panels for the machines on the browser.
    * Ensure both XPS machines are connected before running the code
* Instructions for keyboard operation
    * Instructions for moving Hexapod and Positioner shown below
    * Each key press enters a command. Only one command can be sent to each XPS machine at a time (If requested, we can add a feature that allows submission of  multiple commands to the Hexapod at once)
    * `Toggle verbose` removes all the info statements.
    * `Toggle debug` removes all the debug statements.
```
**********************************************
Instructions for moving Hexapod and Positioner
**********************************************
General Commands:
----------------------------------------------
To see instructions again: h
Toggle verbose (prints information whenever a command is run if True): z
Toggle debug (prints debugging information about the current command being run if True): x
Change the increment by which the hexapod moves: c
Change the increment by which the positioner moves: b
Change the velocity by which the positioner moves: v
Exit program: q
----------------------------------------------
Hexapod Commands:
----------------------------------------------
Shift Hexapod Closer: s
Shift Hexapod Further: w
Shift Hexapod Left: a
Shift Hexapod Right: d
Tilt Hexapod Away: i
Tilt Hexapod Toward: k
Tilt Hexapod Left: j
Tilt Hexapod Right: l
Rotate Hexapod Counter Clockwise: u
Rotate Hexapod Clockwise: o
Zeros all coordinates on Hexapod: 0
----------------------------------------------
Positioner Commands:
----------------------------------------------
Move Positioner Down: ,
Move Positioner Up: .
Zeros all coordinates on Positioner: 0
----------------------------------------------
```

    

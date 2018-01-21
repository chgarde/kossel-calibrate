# kossel-calibrate
Utilities to calibrate my Kossel Delta Printer.
** Warning, this is BETA status and ongoing development, read the code before using it !!! **

Based on the instructions given on this page http://www.think3dprint3d.com/3D-Printer-Kits/Kossel-Mini-3dPrinter-Kit/, one has to run G32 / M665 / M666 multiple times before the printer is correctly cablibrated.

This process is a bit tedious even if it supposed to be ran only once, as I'm moving a lot my printer and I wish to improve it, I decided to automate it.

What it does is :
- send G32 / M665 / M666 multiple times
- show a nice plot
- gives you the M665 and M666 lines to copy/paste into your config.g

Setup
=====
# create python virtualenv in order not to mess up your global python installation
virtualenv .env
# activate your environment
source .env/bin/activate
# install dependencies within your local env
pip install -r requirements.txt

Usage
=====
source .env/bin/activate
python calibrate.py

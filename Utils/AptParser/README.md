This is a light-weight parser for X-Plane's apt.dat file, which defines all of
the airports in the simulator.

This script takes in an apt.dat file and spits out a json file with the details
of each airport and their runways.

Currently, only land airports and land runways are retrieved.

Usage: python aptparser.py path/to/apt.dat path/to/output.json [n_airports]

See example.py for an example of how to read and make use of the generated json file.

Included in this repo is the output of running the script on the apt.dat file from X-Plane 11.

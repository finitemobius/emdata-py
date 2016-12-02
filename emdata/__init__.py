#!/usr/bin/env python3
"""Read, write, and manipulate files in the emdata format

The canonical source for this package is https://github.com/finitemobius/emdata-py
The emdata format is maintained at https://github.com/finitemobius/emdata"""

import sys
import json

__author__ = "Finite Mobius, LLC"
__credits__ = ["Jason R. Miller"]
__license__ = "GPLv3"
__version__ = "0.0.1"
__maintainer__ = "Finite Mobius, LLC"
__email__ = "jason@finitemobius.com"
__status__ = "Development"


class EMData:
    """The emdata format class"""

    def __init__(self):
        self.emdata = {
            'data': []  # This will be filled with dataset objects
        }

    def ingest(self, filename, filetype=None, datatype=None):
        """Imports the given filename, as cleanly as possible"""
        # TODO: Logic to determine type of file
        import emdata._filetypes as ft
        # Determine the type of file.
        # This tells us which ingester to use
        p = ft.determine_filetype(filename, filetype=filetype)
        # Determine what type of data are in the file
        t = ft.determine_datatype(filename, filetype=p, datatype=datatype)
        self.emdata["type"] = t

    def open(self, filename):
        """Opens an emdata json file"""
        # First, try to open the file
        try:
            fp = open(filename, mode='r')
        except Exception as e:
            print(str(e))
            return e
        # Then, try to read the file as JSON
        try:
            js = json.load(fp)
        except Exception as e:
            print(str(e))
            return e
        # TODO: validation
        # Assuming all that worked, this is our new emdata object
        self.emdata = js
        fp.close()

    def print(self):
        self.write(sys.stdout)
        pass

    def write(self, filename):
        with open(filename) as o:
            json.dump(self.emdata, o, ensure_ascii=False)


def _main():
    print("You rang?")

if __name__ == '__main__':
    _main()

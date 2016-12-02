#!/usr/bin/env python3
"""Read FEKO files into emdata dictionaries

The canonical source for this package is https://github.com/finitemobius/emdata-py
The emdata format is maintained at https://github.com/finitemobius/emdata"""

import re

__author__ = "Finite Mobius, LLC"
__credits__ = ["Jason R. Miller"]
__license__ = "GPLv3"
__version__ = "0.0.1"
__maintainer__ = "Finite Mobius, LLC"
__email__ = "jason@finitemobius.com"
__status__ = "Development"


class FFEReader:
    """Parser for FFE files"""

    # List of known column headers for FFE files
    _col_hdr_map = {
        r'^theta': {
            "quantity": "coordinate",
            "vectorComponent": "theta",
            "units": "degrees"
        },
        r'^phi': {
            "quantity": "coordinate",
            "vectorComponent": "phi",
            "units": "degrees"
        },
        r're.*etheta': {
            "quantity": "electric field",
            "vectorComponent": "theta",
            "phasorComponent": "real",
            "units": "V/m"
        },
        r'im.*etheta': {
            "quantity": "electric field",
            "vectorComponent": "theta",
            "phasorComponent": "imaginary",
            "units": "V/m"
        },
        r're.*ephi': {
            "quantity": "electric field",
            "vectorComponent": "phi",
            "phasorComponent": "real",
            "units": "V/m"
        },
        r'im.*ephi': {
            "quantity": "electric field",
            "vectorComponent": "phi",
            "phasorComponent": "imaginary",
            "units": "V/m"
        },
        r'dir.*theta': {
            "quantity": "directivity",
            "vectorComponent": "theta",
            "phasorComponent": "magnitude",
            "units": "dBi"
        },
        r'dir.*phi': {
            "quantity": "directivity",
            "vectorComponent": "phi",
            "phasorComponent": "magnitude",
            "units": "dBi"
        },
        r'dir.*total': {
            "quantity": "directivity",
            "vectorComponent": "total",
            "phasorComponent": "magnitude",
            "units": "dBi"
        }
    }
    # List of keys that are at the top level
    _top_level_keys = [
        "date", "source"
    ]

    def __init__(self):
        pass

    @staticmethod
    def read(fp):
        """Read an FFE file and return a dict of the datasets it contains

        :param fp: file pointer to parse, in text (read) mode
        :type fp: _io.TextIOWrapper
        :return: TBD
        :rtype: dict
        """
        # The dict that we will populate and return
        contents = {
            "data": [],
            "source": ["FEKO"]  # Will be appended to
        }
        # Flag for determining when we've crossed a dataset boundary
        # Set to True at first, so we init a new dataset
        new_ds = True
        # Prime the dataset contents to None
        ds = None
        # Header line identifier (compile here to speed things up)
        hl = re.compile(r'^(#|\*)')
        # For each line in the input file
        for l in fp.readlines():
            l = l.lstrip().rstrip()
            # Determine if this is a header line
            if FFEReader._is_header(hl, l):
                # If this is the first header line after a full dataset ...
                if new_ds:
                    print("I found the first header in a new dataset!")
                    # If this is not the first dataset ...
                    if ds is not None:
                        # Append the previous dataset before moving on
                        contents["data"].append(ds)
                    # Prime an empty dataset
                    ds = {}
                    # Reset the new dataset flag
                    new_ds = False
                # Parse the header line
                d = FFEReader._parse_header(l)
                # Determine if the rturned dict contains top-level keys or dataset-level keys
                # and handle appropriately
                for k in d.keys():
                    # Is this a top-level key?
                    if k in FFEReader._top_level_keys:
                        # If the key already exists at the top level
                        if k in contents.keys():
                            # First, try to append it to a list
                            try:
                                contents[k].append(d[k])
                            # If that doesn't work, just overwrite it
                            except:
                                contents[k] = d[k]
                        # If the key doesn't already exist at the top level
                        else:
                            contents[k] = d[k]
                    # Is this a dataset-level key?
                    else:
                        ds[k] = d[k]
            # If not a header line, see what we can do with it
            else:
                # Try to parse as a data line
                d = FFEReader._parse_data_line(l)
                # If we have data
                if d is not None:
                    if not new_ds:
                        print("I found the first row of a new dataset!")
                        new_ds = True
                    # Append data to columns
                    pass
        # End of File
        if ds is not None:
            # Append the last dataset
            contents["data"].append(ds)
        # Return
        return contents

    @staticmethod
    def _is_header(header_re, line):
        """Determine if a line is a header line

        :param header_re: compiled regex to perform on line
        :param line: the line to parse
        :type line: str
        :return: whether the line is a header line
        :rtype: bool
        """
        return header_re.search(line)

    @staticmethod
    def _parse_header(line):
        """Parse a header line

        :param line: the header line to parse
        :type line: str
        :rtype: dict
        """
        # Strip leading comment marks and spaces
        l = re.sub(r'^(#|\*|\s)+', r'', line.lstrip().rstrip())
        # Test whether it's the column header line
        if re.match(r'^"', l) or len(l) > 99:
            c = FFEReader._parse_column_header(l)
            # Return the data array
            return {"data": c}
        # Is this a key:value header? (contains a colon)
        elif re.search(r':', l):
            # Parse this line
            return FFEReader._parse_keyvalue_header(l)
        # Other known header type: FEKO version info
        elif re.search(r'exported by', l, re.IGNORECASE):
            return {"source": re.sub(r'.*exported by\s*', r'', l)}
        # Unrecognized header line format
        else:
            return {"description": l}

    @staticmethod
    def _parse_keyvalue_header(line):
        """Parse a header line that contains a colon

        :param line: the header line to parse
        :type line: str
        :return:
        :rtype: dict
        """
        # Split the line on colon
        k, d = re.split(r'\s*:\s+', line.lstrip().rstrip(), maxsplit=1)
        # Set up the eventual return value
        r = {}
        # Run through the list of known headers
        if re.match(r'source', k, re.IGNORECASE):
            r = {"source": d}
        elif re.match(r'date', k, re.IGNORECASE):
            r = {"date": d}
        elif re.match(r'frequency', k, re.IGNORECASE):
            r = {
                "frequency": {
                    "value": float(d),
                    "units": "Hz"
                }
            }
        elif re.match(r'origin', k, re.IGNORECASE):
            # Split into x, y, z
            p = list(map(float, re.split(r'[\s|,]+', re.sub(r'\(|\)|\s', r'', d))))
            r = {
                "position": {
                    "units": "meters",
                    "x": p[0],
                    "y": p[1],
                    "z": p[2]
                }
            }
        elif re.match(r'.*name', k, re.IGNORECASE):
            # Any header that is a "Name" can be referenced later to generate a "name" for each dataset
            r = {k: d}
        # Return
        return r

    @staticmethod
    def _parse_column_header(line):
        """Parse the column header line

        Each column header is space-separated and double-quoted
        :param line: the header line to parse
        :type line: str
        :return: list of column header dicts
        :rtype: list
        """
        # List to hold column descriptions
        cols = []
        # Strip out leading/trailing double-quotes
        # Split this row into the individual column headers
        hdr = re.split(r'["|\s]+', line.lstrip().rstrip().lstrip('"').rstrip('"'))
        # Iterate through each column header
        for l in hdr:
            match = False
            for k in FFEReader._col_hdr_map.keys():
                # See if this column header matches a known header
                if re.search(k, l, re.IGNORECASE):
                    # Add this column description to the list
                    cols.append(FFEReader._col_hdr_map[k])
                    match = True
            # Did we not match any known headers?
            # If not, we still want to put the column in there so the data columns will match the headers
            if not match:
                cols.append({"quantity": "unknown", "description": l})
        return cols

    @staticmethod
    def _parse_data_line(line):
        # Don't process blank lines
        if not re.match(r'^\s*$', line):
            # Split on spaces
            d = re.split(r'\s+', line)
            # If d is a valid list of strings
            if len(d[0]):
                # Try returning floats
                try:
                    return list(map(float, d))
                # If that fails, return the strings
                except:
                    return d
            else:
                pass
        return None

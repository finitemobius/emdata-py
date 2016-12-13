#!/usr/bin/env python3
"""Read FEKO files into emdata dictionaries

The canonical source for this package is https://github.com/finitemobius/emdata-py
The emdata format is maintained at https://github.com/finitemobius/emdata"""

import re
import copy

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
        },
        r'gain.*theta': {
            "quantity": "gain",
            "vectorComponent": "theta",
            "phasorComponent": "magnitude",
            "units": "dBi"
        },
        r'gain.*phi': {
            "quantity": "gain",
            "vectorComponent": "phi",
            "phasorComponent": "magnitude",
            "units": "dBi"
        },
        r'gain.*total': {
            "quantity": "gain",
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
        new_ds_on_next_header = True
        # Prime the dataset contents to None
        dataset = None
        # Header line identifier (compile here to speed things up)
        hl = re.compile(r'^(#|\*)')
        # For each line in the input file
        for l in fp.readlines():
            l = l.lstrip().rstrip()
            # Determine if this is a header line
            if FFEReader._is_header(hl, l):
                # If this is the first header line after a full dataset ...
                if new_ds_on_next_header:
                    # If this is not the first dataset (e.g., 'dataset' already contains something)
                    if dataset is not None:
                        # Append the previous dataset before moving on
                        contents["data"].append(copy.deepcopy(dataset))
                    # Prime an empty dataset
                    dataset = {}
                    # Reset the new dataset flag
                    new_ds_on_next_header = False
                # Parse the header line
                line = FFEReader._parse_header(l)
                # Determine if the returned dict contains top-level keys or dataset-level keys
                # and handle appropriately
                for k in line.keys():
                    # Is this a top-level key?
                    if k in FFEReader._top_level_keys:
                        # If the key already exists at the top level
                        if k in contents.keys():
                            # First, try to append it to a list
                            try:
                                contents[k].append(line[k])
                            # If that doesn't work, just overwrite it
                            except:
                                contents[k] = line[k]
                        # If the key doesn't already exist at the top level
                        else:
                            contents[k] = line[k]
                    # Is this a dataset-level key?
                    else:
                        dataset[k] = line[k]
            # If not a header line, see what we can do with it
            else:
                # Try to parse as a data line
                line = FFEReader._parse_data_line(l)
                # If we have data
                if line is not None:
                    # Do some housework if this is the first row in a new dataset
                    if not new_ds_on_next_header:
                        # Set this flag so the next time a header line is encountered, we create a new dataset
                        new_ds_on_next_header = True
                    # Append data to columns
                    if len(dataset["data"]) == len(line):
                        for i in range(len(line)):
                            dataset["data"][i]["data"].append(line[i])
        # End of File
        if dataset is not None:
            # Append the last dataset
            contents["data"].append(copy.deepcopy(dataset))
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
        # Right now, just see if it starts with a quote. There may be a more robust method.
        if re.match(r'^"', l):
            # Return the data array
            return {"data": FFEReader._parse_column_header(l)}
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
        hdrs = re.split(r'["|\s]+', line.lstrip().rstrip().lstrip('"').rstrip('"'))
        # Iterate through each column header
        for hdr in hdrs:
            # Default header
            c = {"quantity": "unknown", "description": hdr}
            # Prime the 'found a match' flag
            match = False
            # Search the known header values for a match
            for k in FFEReader._col_hdr_map.keys():
                # See if this column header matches a known header
                if match == False and re.search(k, hdr, re.IGNORECASE):
                    # Add this column description to the list
                    c = FFEReader._col_hdr_map[k]
                    match = True
            # Add a 'data' array to the column
            c["data"] = []
            # Add this column to the collection
            cols.append(c)
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

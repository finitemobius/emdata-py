# Define the types of files that we can ingest
# This is typically the name of the originating software,
# though it can also be the name of a standard
_valid_filetypes = [
    "feko", "xgtd"
]

# Map extensions to DEFAULT filetypes and data types
# (These can be detected in a deeper analysis)
_extensions = {
    "ffe": {
        "filetype": "feko",
        "type": "far field"
    },
    "efe": {
        "filetype": "feko",
        "type": "near field"
    },
    "hfe": {
        "filetype": "feko",
        "type": "near field"
    },
    "out": {
        "filetype": "feko",
        "type": None
    },
    "fz": {
        "filetype": "xgtd",
        "type": "far field"
    },
    "uan": {
        "filetype": "xgtd",
        "type": "far field"
    }
}


def determine_filetype(filename, filetype=None):
    """Given a file name, try to determine what the file is

    :param filename:
    :param filetype:
    :return:
    """
    pass


def determine_datatype(filename, filetype=None, datatype=None):
    """Given a filename, try to determine what type of data the file contains

    :param filename:
    :param filetype:
    :param datatype:
    :return:
    """
    pass

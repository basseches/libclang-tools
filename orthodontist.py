#!/usr/bin/env python3

import argparse
import sys
from pathlib import Path

import clang.cindex
from termcolor import colored, cprint

def is_valid_function(call, tu):
    if call.location.file is None or call.location.file.name != tu.spelling:
        return False
    is_func_call = call.kind == clang.cindex.CursorKind.INIT_LIST_EXPR
    # Braced init list. Make sure that it's an array decl.
    # If the number of elements in the init list is smaller than the length
    # of the array, it's doing zero initialization.
    return is_func_call and ((arr_len := call.type.get_array_size()) > 0) and \
    (sum(1 for _ in call.get_children()) < arr_len)

def find(tu):
    """Retrieve list of stack-based braced array list-initializations (if they
    do some kind of zeroing out of the structure)."""
    return [ c.semantic_parent for c in tu.cursor.walk_preorder() \
             if is_valid_function(c, tu) ]

def remove_init(o_file, edited, arr, content, offset):
    """Removes a braced array list-intialization.
    """
    cprint(f"[ Zero-initialization detected on line {arr.extent.start.line} of "
    f"{arr.location.file} ]", "blue")

    # Where the array initialization starts and ends
    start_offset = arr.extent.start.offset
    end_offset = arr.extent.end.offset

    # Print out the initialization
    print(content[start_offset:end_offset])

    resp = input(colored("\n[ Would you like to remove this braced list "
                         "initialization? ] [Y/n]: ", "blue"))
    if resp == "n":
        return offset

    tokens = []
    for token in arr.get_tokens():
        if token.spelling == "=":
            cut_start = token.extent.start.offset
        tokens.append(token)

    offset_chunk = content[offset:cut_start]
    if o_file:
        with open(o_file, "a") as output:
            output.write(offset_chunk)
    else:
        edited += offset_chunk

    print("Done.")
    return edited, end_offset


def remove_inits(o_file, arrs, filename):
    """ Removes all zero-initialization with braced init-list syntax. """
    with open(filename, "rb") as c_file:
        # To avoid any weird characters
        content = c_file.read().decode("mac_roman")

    # Overwrite the output file
    if o_file:
        open(o_file, "w").close()

    curr_offset = 0
    edited = ""
    for arr in arrs:
        # Replace zero init, writing parts of the file along the way.
        edited, curr_offset = remove_init(o_file, edited, arr, content,
                                          curr_offset)

    # Write out the rest of the file
    if o_file:
        with open(o_file, "a") as output:
            output.write(content[curr_offset:])
    else:
        sys.stdout.write(edited + content[curr_offset:])

def orthodontist():
    parser = argparse.ArgumentParser(
        description='Remove braced zero initialization of arrays. Writes result to'
                    ' stdout by default.'
    )

    parser.add_argument('filepath',
                        metavar='<filepath>',
                        type=str,
                        help='the path of the .c file')

    parser.add_argument('-i',
                        '--inplace',
                        action="store_true",
                        help='in place edit, if specified')

    parser.add_argument('-o',
                        '--outputfile',
                        action="store",
                        help='the name of an output file, if specified')

    args = parser.parse_args()

    filename = args.filepath
    if not Path(filename).is_file():
        cprint('The file specified does not exist.', 'red')
        sys.exit(1)

    idx = clang.cindex.Index.create()

    # Generate translation unit
    tu = idx.parse(filename)

    # Return cursor that points to the function call
    arrs = find(tu)

    if len(arrs) == 0:
        # Function call wasn't found
        sys.exit(1)

    o_file = filename if args.inplace else args.outputfile
    remove_inits(o_file, arrs, filename)

if __name__ == '__main__':
    orthodontist()

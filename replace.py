#!/usr/bin/env python3

import argparse
import re
import sys
from pathlib import Path

import clang.cindex
from termcolor import cprint

def is_valid_function(call, tu, name):
    if call.location.file is None or call.location.file.name != tu.spelling:
        return False
    is_func_call = call.kind == clang.cindex.CursorKind.CALL_EXPR
    if is_func_call and (call.spelling == name):
        return True
    return False

def find_func(tu, name):
    """Retrieve lists of function declarations and call expressions in a
    translation unit.
    """
    return [ c for c in tu.cursor.walk_preorder() if is_valid_function(c, tu, name) ]


def replace_call(o_file, call, content, fn_name, fn_args, offset):
    """ Replaces call to old function with call to a new function. Optionally
    replaces the old function args with args passed in as CLA.
    """
    if debug:
        cprint(f"[ Replacing call to {call.spelling}() on line "
            f"{call.extent.start.line} of {call.location.file}. ]", "red")

    tokens = []
    for token in call.get_tokens():
        tokens.append(token)

    # Where the function call starts
    start_offset = tokens[0].extent.start.offset

    if fn_args:
        # Extract old args
        old_args = []
        for arg_cursor in call.get_arguments():
            arg_start = arg_cursor.extent.start.offset
            arg_end = arg_cursor.extent.end.offset
            old_args.append(content[arg_start:arg_end])

        # Replace [NUMBER] with old function arg
        for idx, arg in enumerate(old_args):
            fn_args = re.sub(f"\[{re.escape(str(idx))}\]", arg, fn_args)

        args_string = f"({fn_args})"

    else:
        # The second token is the open paren.
        open_paren = tokens[1].extent.start.offset
        args_string = content[open_paren:tokens[-1].extent.end.offset]

    # Chunk to write (previous offset + new name and args)
    offset_chunk = content[offset:start_offset]
    new_call = fn_name + args_string

    # Open the file and write from last offset until reaching the function name,
    # then write the function name.
    if o_file:
        if debug:
            cprint("[ Old function call ]", "blue")
            print(content[start_offset:tokens[-1].extent.end.offset])
            cprint("[ New function call ]", "blue")
            print(new_call)

        with open(o_file, "a") as output:
            output.write(offset_chunk + new_call)
    else:
        sys.stdout.write(offset_chunk + new_call)

    # Update the offset value
    return tokens[-1].extent.end.offset

def replace_calls(o_file, calls, filename, fn_name, fn_args):
    """Replaces all calls to a function."""
    with open(filename, "rb") as c_file:
        # To avoid any weird characters
        content = c_file.read().decode("mac_roman")

    # Overwrite the output file
    if o_file:
        open(o_file, "w").close()

    curr_offset = 0
    for call in calls:
        # Replace calls, writing parts of the file to stdout along the way.
        curr_offset = replace_call(o_file, call, content, fn_name, fn_args,
                                curr_offset)

    # Write out the rest of the file
    if o_file:
        with open(o_file, "a") as output:
            output.write(content[curr_offset:])
    else:
        sys.stdout.write(content[curr_offset:])

class ParseFnArgs(argparse.Action):
    def __call__(self, parser, namespace, args, option_string=None):
        delim = ", "
        setattr(namespace, self.dest, delim.join(args))

def replace():
    parser = argparse.ArgumentParser(
        description='Find and replace function calls. Writes result to stdout'
                    ' by default.'
    )

    parser.add_argument('filepath',
                        type=str,
                        help='the path of the .c file to search',
                        metavar='<filename>')

    parser.add_argument('old_fn',
                        type=str,
                        help='the name of the function to replace',
                        metavar='<old-fn>')

    parser.add_argument('new_fn',
                        type=str,
                        help='the new function\'s name',
                        metavar='<new-fn>')

    parser.add_argument('-a', '--args',
                        nargs='*',
                        action=ParseFnArgs,
                        help='new args to be passed to the function (refer to'
                        ' old function\'s args with [number])',
                        metavar='args')

    parser.add_argument('-d', '--debug',
                        action='store_true',
                        help='print some debug information')

    parser.add_argument('-f', '--create-file',
                        action='store_true',
                        help='touch a file with the old function name if the'
                        ' function was replaced')

    parser.add_argument('-i', '--in-place',
                        action='store_true',
                        help='in place edit, if specified')

    parser.add_argument('-o', '--output-file',
                        action='store',
                        help='the name of an output file, if specified',
                        metavar='<filename>')

    args = parser.parse_args()

    global debug
    debug = args.debug

    filename = args.filepath
    if not Path(filename).is_file():
        cprint('The file specified does not exist.', 'red')
        sys.exit(1)

    idx = clang.cindex.Index.create()

    # Generate translation unit
    tu = idx.parse(filename)

    # Return cursor that points to the function call
    calls = find_func(tu, args.old_fn)

    if len(calls) == 0:
        # Function call wasn't found
        cprint('The function specified was not found.', 'red')
        sys.exit(0)

    if args.create_file:
        Path(f".{args.old_fn}").touch()

    o_file = filename if args.in_place else args.output_file
    replace_calls(o_file, calls, filename, args.new_fn, args.args)

if __name__ == '__main__':
    replace()

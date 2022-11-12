#!/usr/bin/env python3

import argparse
import os
import re
import sys

import clang.cindex

def find_func(tu, name):
  """ Retrieve lists of call expressions in a translation unit."""
  calls = []
  for c in tu.cursor.walk_preorder():
    if c.location.file is None:
      continue
    is_func_call = c.kind == clang.cindex.CursorKind.CALL_EXPR
    if is_func_call and (c.spelling == name):
      calls.append(c)
  return calls

def replace_call(o_file, call, content, fn_name, fn_args, offset):
  """ Replaces call to old function with call to a new function. Optionally
  replaces the old function args with args passed in as CLA.
  """
  tokens = []
  for token in call.get_tokens():
    tokens.append(token)

  # Extract args.
  old_args = []
  for arg_cursor in call.get_arguments():
    start = arg_cursor.extent.start.offset
    end = arg_cursor.extent.end.offset
    old_args.append(content[start:end])

  for idx, arg in enumerate(old_args):
    fn_args = re.sub(f"\[{re.escape(str(idx))}\]", arg, fn_args)

  # The first token is always the function ID (i.e. name).
  old_id = tokens[0]
  start_id_offset = old_id.extent.start.offset

  # Initialize with the end of the function ID
  end_offset = old_id.extent.end.offset

  # Open the file and write from last offset until reaching the function name,
  # then write the function name.
  if o_file:
    with open(o_file, "a") as output:
      output.write(content[offset:start_id_offset])
      output.write(fn_name)

      # If user provided args to replace, do that.
      if fn_args:
        output.write(f"({fn_args}")
  else:
    sys.stdout.write(content[offset:start_id_offset])
    sys.stdout.write(fn_name)

    # Ditto
    if fn_args:
      sys.stdout.write(f"({fn_args}")

  if fn_args:
    # The last token is now the close paren.
    end_offset = tokens[-1].extent.start.offset

  # Update the offset value
  return end_offset

def replace_calls(o_file, calls, filename, fn_name, fn_args):
  """Replaces all calls to a function."""
  with open(filename, "r") as c_file:
    content = c_file.read()

  # Want to overwrite the output file
  if o_file:
    open(o_file, "w").close()

  curr_offset = 0
  for call in calls:
    # Replace calls, writing parts of the file to stdout along the way.
    curr_offset = replace_call(o_file, call, content, fn_name,
                               fn_args, curr_offset)

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
    description='Find and replace function calls. Writes result to stdout.'
  )

  parser.add_argument('filepath',
                      metavar='<filepath>',
                      type=str,
                      help='the path of the .c file')

  parser.add_argument('oldfn',
                      metavar='<oldfn>',
                      type=str,
                      help='the name of the function to replace')

  parser.add_argument('newfn',
                      metavar='<newfn>',
                      type=str,
                      help='the new function\'s name')

  # Can pass arguments as $number for old args
  parser.add_argument('-a',
                      '--args',
                      nargs='*',
                      action=ParseFnArgs,
                      help='new args to be passed to the function (refer to'
                      ' old function\'s args with [number])')

  parser.add_argument('-i',
                      action="store_true",
                      help='in place edit, if specified')

  parser.add_argument('-o',
                      '--outputfile',
                      action="store",
                      help='the name of an output file, if specified')

  args = parser.parse_args()

  filename = args.filepath
  if not os.path.isfile(filename):
    print('The file specified does not exist')
    sys.exit(1)

  idx = clang.cindex.Index.create()

  # Generate translation unit
  tu = idx.parse(filename)

  # Return cursor that points to the function call
  calls = find_func(tu, args.oldfn)

  if len(calls) == 0:
    # Function call wasn't found
    sys.exit(1)

  new_fn = args.newfn
  fn_args = args.args
  o_file = filename if args.i else args.outputfile
  replace_calls(o_file, calls, filename, args.newfn, args.args)

if __name__ == '__main__':
  replace()

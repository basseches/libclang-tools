#!/usr/bin/env python3

import argparse
import os
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

def replace_call(token_gen, filename, fn_name, fn_args, offset):
  """ Replaces call to old function with call to a new function. Optionally
  replaces the old function args with args passed in as CLA.
  """
  tokens = []
  for token in token_gen:
    tokens.append(token)

  # The first token is always the function ID (i.e. name).
  old_id = tokens[0]
  start_id_offset = old_id.extent.start.offset
  diff = start_id_offset - offset

  # Open the file and write from last offset until reaching the function name,
  # then write the function name.
  with open(filename, "r") as c_file:
    c_file.seek(offset)
    sys.stdout.write(c_file.read(diff))
    sys.stdout.write(fn_name)

  end_offset = old_id.extent.end.offset

  # If user provided args to replace, do that.
  if fn_args:
    sys.stdout.write(f"({fn_args}")
    # The last token is now the close paren.
    end_offset = tokens[-1].extent.start.offset

  # Update the offset value
  return end_offset

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
  
  parser.add_argument('-a',
                      '--args',
                      nargs='*',
                      action=ParseFnArgs,
                      help='new args to be passed to the function')
  
  args = parser.parse_args()
  filename = args.filepath
  if not os.path.isfile(filename):
    print('The file specified does not exist')
    sys.exit(1)

  fn_args = args.args
  old_fn = args.oldfn
  new_fn = args.newfn

  idx = clang.cindex.Index.create()

  # translation unit
  tu = idx.parse(filename)

  # Returns cursor that points to the function call
  calls = find_func(tu, old_fn)

  if len(calls) == 0:
    # Function call wasn't found.
    sys.exit(1)

  curr_offset = 0
  for call in calls:
    # Replace calls, writing parts of the file to stdout along the way.
    curr_offset = replace_call(call.get_tokens(), filename, new_fn, fn_args,
                               curr_offset)
  
  # Write out the rest of the file
  with open(filename, "r") as c_file:
    c_file.seek(curr_offset)
    sys.stdout.write(c_file.read())

if __name__ == '__main__':
  replace()

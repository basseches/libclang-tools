#!/usr/bin/env python3

import argparse
import os
import sys

import clang.cindex

def find_func(tu, name):
  """ Retrieve lists of function declarations and call expressions in a
  translation unit.
  """
  funcs = []
  for c in tu.cursor.walk_preorder():
    if c.location.file is None:
      continue
    is_func_decl = c.kind == clang.cindex.CursorKind.FUNCTION_DECL
    if is_func_decl and (c.spelling == name) and (c.is_definition()):
      funcs.append(c)
  return funcs

def print_body(filename, extent):
  """ Print the function body associated with a function decl cursor extent
  (start and end location).
  """
  start = extent.start.offset
  body = extent.end.offset - start
  with open(filename, 'r') as file:
    file.seek(start)
    print(file.read(body))

def printdef():
  parser = argparse.ArgumentParser(
    description='Find and print the definition of a function.'
  )

  parser.add_argument('filepath',
                      metavar='<filepath>',
                      type=str,
                      help='the path of the .c file')

  parser.add_argument('function',
                      metavar='<function>',
                      type=str,
                      help='the name of the function to extract')

  args = parser.parse_args()
  filepath = args.filepath
  if not os.path.isfile(filepath):
    print('The file specified does not exist')
    sys.exit(1)

  fn_name = args.function

  idx = clang.cindex.Index.create()

  # Translation unit
  tu = idx.parse(filepath)

  # Returns cursor that points to the definition of the function
  funcs = find_func(tu, fn_name)

  if len(funcs) == 0:
    # Function definition wasn't found
    sys.exit(1)

  for f in funcs:
    print_body(filepath, f.extent)

if __name__ == '__main__':
  printdef()

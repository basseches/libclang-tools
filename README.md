# libclang-tools

Use the [`libclang`](https://libclang.readthedocs.io/en/latest/index.html) module to
query the Clang AST for a `.c` file.

## Dependencies

`libclang` is part of the
[`LLVM project.`](https://github.com/llvm/llvm-project/tree/main/clang/bindings/python)
Unfortunately, there's no good way to install Clang's Python bindings as there's no official
`libclang` package. The solution for now is to

```
pip install libclang
```
This package is an unofficial mirror.

## find.py

Finds a function's definition and prints it out.

```
usage: find.py [-h] <filepath> <function>

Find and print the definition of a function.

positional arguments:
  <filepath>  the path of the .c file
  <function>  the name of the function to extract

options:
  -h, --help  show this help message and exit
```

For nice syntax highlighting, pipe into `batcat`:

```.sh
./find.py example.c foo | batcat -l=c
```

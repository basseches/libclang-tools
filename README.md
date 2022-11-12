# libclang-tools

Use the [`libclang`](https://libclang.readthedocs.io/en/latest/index.html) module
to query the Clang AST for a `.c` file.

## Dependencies

`libclang` is part of the
[LLVM project.](https://github.com/llvm/llvm-project/tree/main/clang/bindings/python)
Unfortunately, there's no good way to install Clang's Python bindings as there's
no official`libclang` package. The solution for now is to

```
pip install libclang
```
This package is an unofficial mirror.

## `printdef.py`

*Like `printf()`, but not really like `printf()` at all.*

Finds a function's definition and prints it out.

```
usage: printdef.py [-h] <filepath> <function>

Find and print the definition of a function.

positional arguments:
  <filepath>  the path of the .c file
  <function>  the name of the function to extract

options:
  -h, --help  show this help message and exit
```

### Example usage

The following will print out the definition of `foo()` if it exists in `file.c`.

```
./printdef.py file.c foo
```

## `replace.py`

Finds all calls to a certain function and replaces them with calls to another
function. Optionally replaces the arguments with arguments passed on the command
line.

```
usage: replace.py [-h] [-a [ARGS ...]] [-i] [-o OUTPUTFILE] <filepath> <oldfn> <newfn>

Find and replace function calls. Writes result to stdout.

positional arguments:
  <filepath>            the path of the .c file
  <oldfn>               the name of the function to replace
  <newfn>               the new function's name

options:
  -h, --help            show this help message and exit
  -a [ARGS ...], --args [ARGS ...]
                        new args to be passed to the function (refer to old function's args
                        with [number])
  -i, --inplace         in place edit, if specified
  -o OUTPUTFILE, --outputfile OUTPUTFILE
                        the name of an output file, if specified
```

### Example usage

Executing the following will replace all calls to `foo()` in `file.c` with
calls to `bar()`, but the arguments to the function call will be retained.
The result is written to `stdout`.

```
./replace.py file.c foo bar
```

Executing the following will replace all calls to `foo(...)` in `file.c` with
calls to `bar(1, 2, 3)` in-place.

```
./replace.py -i file.c foo bar -a 1 2 3
```

Executing the following will replace all calls to `foo(arg0, arg1)` with calls
to `bar((arg0) * (arg1))` in-place.

```
./replace.py -i file.c foo bar -a "([0]) * ([1])"
```

---

For nice syntax highlighting, pipe into `batcat`:

```.sh
./find.py example.c foo | batcat -l=c
```

# libclang-tools

## find.py

Query the Clang AST of a `.c` file to find a function's definition and print it out.

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

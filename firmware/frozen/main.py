"""
PicoCalc UFO entrypoint — launch the interactive shell.
"""

try:
    import ufo_shell

    ufo_shell.run()
except Exception as e:
    import sys

    sys.print_exception(e)
    print("Falling back to REPL. Try: edit('apps/main.py')")

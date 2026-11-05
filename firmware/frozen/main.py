"""
PicoCalc UF2 firmware entrypoint — launch the interactive shell.
"""

try:
    import uf2_shell

    uf2_shell.run()
except Exception as e:
    import sys

    sys.print_exception(e)
    print("Falling back to REPL. Try: edit('apps/main.py')")

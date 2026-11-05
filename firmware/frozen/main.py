try:
    import uf2_shell

    uf2_shell.run()
except Exception as e:
    import sys

    sys.print_exception(e)

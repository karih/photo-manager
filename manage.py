#!.env/bin/python 

import sys
import logging

import pm.commands as cmd

if __name__ == "__main__":

    logging.basicConfig(format="%(asctime)s %(levelname)7s: %(message)s", level=logging.DEBUG, datefmt='%H:%M:%S')

    commands = [c for c in cmd.__all__ if not c.startswith("_")]

    if len(sys.argv) < 2 or sys.argv[1] not in commands:
        print("The following commands are available:")
        for c in commands:
            print("  %s" % c)
    else:
        getattr(getattr(cmd, sys.argv[1]), "main")(*sys.argv[2:])


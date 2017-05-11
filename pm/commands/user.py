# encoding=utf-8

import sys
import os
import os.path
import logging
import argparse

import string
import random

from .. import app, db, helpers, models

def val_nonempty(v):
    if len(v) < 1:
        raise ValueError("Value can not be empty")
    return v

def ask(q, default="", validator=None):
    while True:
        try:
            output = input("%s [%s]: " % (q, default))
            if not output:
                output = default
            if validator is not None:
                output = validator(output)
            return output
        except ValueError as e:
            print("Error in input (%s)." % e)

random_password = lambda: "".join(random.choice(string.ascii_letters + string.digits) for i in range(16))

def user_exists(username):
    return len(models.User.query.filter(models.User.username==username).all()) > 0

def add_user(args):
    user = models.User()
    if len(args) > 0 and val_nonempty(args[0]):
        if user_exists(args[0]):
            print("Username already in use")
            sys.exit(1)
        else:
            user.username=args[0]
    else:
        while True:
            username = ask("Username", validator=val_nonempty)
            if user_exists(username):
                print("Username already in use")
            else:
                user.username=username
                break

    password = random_password()
    user.set_password(password)
    print("Password set to %s" % password)
    db.add(user)
    db.commit()

def change_password(args):
    if len(args) != 1 or not user_exists(args[0]):
        print("User does not exist")
        sys.exit(1)

    user = models.User.query.filter(models.User.username==args[0]).all()[0]
    password = random_password()
    user.set_password(password)
    print("Password set to %s" % password)
    db.commit()


def main(*args):
    commands = {
        'add' : add_user,
        'password' : change_password,
        #'rmuser' : rmuser,
        #'password' : password,
        #'summary' : summary
    }

    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=commands.keys())
    parser.add_argument("args", nargs=argparse.REMAINDER)
    args = parser.parse_args(args)

    commands[args.command](args.args)

#!/usr/bin/env python2.7
'''
Script for container processes.
'''
import os
import shlex
from lib.scriptutil import *


def parseCommand(cmd) :
    args = shlex.split(cmd)
    exe = args.pop(0)
    return (exe, args)


def executeConf() :
    conf = "/launch.conf" 

    with open(conf) as f:
        rawcmds = f.readlines()

    cmds = []
    for cmd in rawcmds :
        if not cmd :
            continue

        cmd = cmd.lstrip().rstrip()

        if cmd[0][0] == '#' :
            continue

        (cmd, args) = parseCommand(cmd)
        execute(cmd, args)


if __name__ == "__main__":
    executeConf()
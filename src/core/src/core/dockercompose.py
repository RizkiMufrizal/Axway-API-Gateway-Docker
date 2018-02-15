import subprocess
import os
from util import *
import cmd_config


def dockerComposeStop(projectFolder) :
    _checkForFolder(projectFolder)
    dockerCompose("stop", projectFolder = projectFolder)


def dockerComposeClean(projectFolder) :
    _checkForFolder(projectFolder)
    dockerCompose("stop", projectFolder = projectFolder)
    dockerCompose("rm", args=["-vf"], projectFolder = projectFolder)


def dockerComposeUp(projectFolder, args=["-d"]) :
    _checkForFolder(projectFolder)
    dockerCompose("up", projectFolder = projectFolder, args=args)


def dockerCompose(cmd, projectFolder, args=[], wait=True) :
    _checkForFolder(projectFolder)
    popenargs = ["docker-compose"]
    if cmd_config.VERBOSE is not None:
        popenargs.append(cmd_config.VERBOSE)
        popenargs.append(cmd)
    else:
	popenargs.append(cmd)

    banner (" ".join(["[%s]" % projectFolder] + popenargs + args ))	
    
    print('running:' , popenargs , args)
    try:
        proc = subprocess.Popen(popenargs + args, stderr=subprocess.STDOUT, cwd=projectFolder)
    except OSError as ex:
        if 'No such file or directory' in ex:
            raise Exception("Command failed.  Failed to execute or find docker-compose")
        else:
            raise ex

    if proc.wait() != 0 :
        raise Exception("Command failed. Exit status %d" % proc.returncode)


def _checkForFolder(projectFolder) :
    if not os.path.exists(projectFolder) or not os.path.isdir(projectFolder) : 
        raise Exception("Folder does not exist, has it been built: %s" % projectFolder)

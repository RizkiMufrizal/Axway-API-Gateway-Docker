#!/usr/bin/env python2.7
'''
Script for Backup a direcrtory from the container
'''
import os
import socket
import signal
import time
import threading
import argparse
from lib.scriptutil import *
import subprocess
from subprocess import PIPE
import hashlib

def parseOptions() :
    global options

    parser = argparse.ArgumentParser()
    parser.add_argument("--srcdir")
    parser.add_argument("--name")

    (options, unknown) = parser.parse_known_args()

    if not options.srcdir :
        parser.error("No gateway directory specified.")

    if not options.name :
        parser.error("No backup name specified")

    if not os.path.isdir(options.srcdir) :
        parser.error("Directory not found: %s" % options.srcdir)
    
def persistHash(filepath,ref) :
    fo = open(filepath, "w")
    fo.write(ref);        
    fo.close()

def calculateHash(filepath) :
    hash_obj = hashlib.sha224()
    for file in os.listdir(filepath):
        last_change = os.path.getmtime(os.path.join(filepath,file))
        hash_obj.update(str(last_change))
    return hash_obj.hexdigest()     

def backup():
    backup_path = os.path.join(os.sep,"opt","Axway","backup")
    dest_path = os.path.join(backup_path,options.name)
    banner("Starting Backup Start from %s to %s " % (options.srcdir,options.name))        

    if not os.path.exists(backup_path):
        print "backup_path does not exist - creating %s" %backup_path
        os.makedirs(backup_path)

    if not os.path.exists(dest_path):
        execute("rm",["-rf",dest_path])   
    
    execute("cp",["-Rf",options.srcdir,dest_path])    
    state_hash = calculateHash(dest_path)
    persistHash(os.path.join(dest_path,".apigwvol"), state_hash)    
    banner("Backup state for backup %s - %s" % (options.name, state_hash))

if __name__ == "__main__":
    parseOptions()
    backup()

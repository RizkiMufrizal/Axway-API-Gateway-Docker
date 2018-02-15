#!/usr/bin/env python2.7
'''
Script for starting/stopping instances.
'''
import os
import socket
import signal
import time
import threading
import argparse
from lib.scriptutil import *

hostname = socket.gethostname()
ip = socket.gethostbyname(hostname)

def parseOptions() :
    global options

    parser = argparse.ArgumentParser()
    parser.add_argument("--cassandraDir")

    parser.add_argument("--start", action="store_const", dest="action", const="start")
    parser.add_argument("--stop", action="store_const", dest="action", const="stop")
    parser.add_argument("--wait", action="store_const", dest="action", const="wait")
    parser.add_argument("-b", "--block", action="store_true", help="Don't exit after starting.")
    parser.add_argument("--cassandraPort", default=9042)

    (options, unknown) = parser.parse_known_args()

    if not options.cassandraDir :
        parser.error("No cassandra directory specified.")

    if not os.path.isdir(options.cassandraDir) :
        parser.error("Directory not found: %s" % options.cassandraDir)

    if not options.action :
        parser.error("No action sepcified.")

def manageCassandra() :
    if options.action == 'start' :
        startCassandra(options.cassandraDir, options.cassandraPort)

    elif  options.action == 'stop' :
        stopCassandra(options.cassandraDir, options.cassandraPort)

    elif  options.action == 'wait' :
        waitCassandra(options.cassandraDir, options.cassandraPort)


def startCassandra(cassandraDir, cassandraPort) :
    banner("Starting Cassandra on %s" % (hostname))
    execute(os.path.join(cassandraDir, "bin/cassandra"), ["-p", os.path.join(cassandraDir, "bin/pidfile")])
    waitForPort(cassandraPort, hostname)

    banner("Going to execute nodetool status...")   
    execute(os.path.join(cassandraDir, "bin/nodetool"), ["status"])


def killProcess(pid, sig) :
    print "Killing: %s" % (str(pid))
    os.kill(pid, signal.SIGKILL)


def stopCassandra(cassandraDir, cassandraPort, forceDelay = 30.0) :
    banner("Stopping Cassandra on %s" % (hostname))

    # Start a thread - sometimes NM hangs (kill it if it hangs)
    stopTimer = None
    pidFile = os.path.join(cassandraDir, "bin/pidfile")
    pid = -1
    with open(pidFile, "r") as p :
        pid = int(p.read())

    if pid > 0 :
        stopTimer = threading.Timer(forceDelay, killProcess, (pid, signal.SIGKILL))
        stopTimer.start()

    # Try stopping cleanly.
    if testPort(cassandraPort, 'localhost') :
        killProcess(pid, signal.SIGINT)
        waitForPortClose(cassandraPort, 'localhost')

    if testPort(cassandraPort, hostname) :
        killProcess(pid, signal.SIGINT)
        waitForPortClose(cassandraPort, hostname)

    if stopTimer :
        stopTimer.cancel()


def waitCassandra(cassandraDir, cassandraPort) :
    banner("Waiting for Cassandra on %s" % (hostname))
    waitForPort(cassandraPort, hostname)


def unblock(signal, frame) :
    global block
    print "Exiting"
    block = False

if __name__ == "__main__":
    parseOptions()
    manageCassandra()


    if options.block :
        global block
        block = options.block
        banner("Staying alive")
        signal.signal(signal.SIGINT, unblock)
        while block :
            time.sleep(5)

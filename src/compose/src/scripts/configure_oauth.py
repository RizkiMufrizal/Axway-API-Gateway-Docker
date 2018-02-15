#!/usr/bin/env python2.7
'''
Script for configuring OAuth
'''
import os
import socket
import argparse
from lib.scriptutil import *

hostname = socket.gethostname()
ip = socket.gethostbyname(hostname)

def parseOptions() :
    global options

    parser = argparse.ArgumentParser()
    parser.add_argument("--gwdir")
    parser.add_argument("--version", default="7.3.1")
    parser.add_argument("-u", "--username", default="admin")
    parser.add_argument("-p", "--password", default="changeme")
    parser.add_argument("-g", "--group", help='The group name')
    parser.add_argument("-n", "--instance", help='The instance name')
    parser.add_argument("--type", default="all", help='The deployment type: "authzserver", "clientdemo" or "all" (default all)')
    parser.add_argument("--port", default="8089", help='The port Client Application registry is listening on (default 8089)')
    parser.add_argument("--admin", default="regadmin", help='The Client Application Registry admin name (default regadmin)')
    parser.add_argument("--adminpw", default="changeme", help='The Client Application Registry admin password (default changeme)')

    (options, unknown) = parser.parse_known_args()

    if not options.gwdir :
        parser.error("No gateway directory specified.")

    if not os.path.isdir(options.gwdir) :
        parser.error("Directory not found: %s" % options.gwdir)

    if not options.group :
        parser.error("No group specified.")

    if not options.instance :
        parser.error("No instance specified.")

def configureOAuth() :
    banner("Configuring OAuth on %s: %s:%s" % (hostname, options.group, options.instance))

    execute(os.path.join(options.gwdir, "samples/scripts/run.sh"), [
        "oauth/deployOAuthConfig.py",
        "-g", options.group,
        "-n", options.instance,
        "-u", options.username,
        "-p", options.password,
        "--type", options.type,
        "--port", options.port,
        "--admin", options.admin,
        "--adminpw", options.adminpw],
        cwd = os.path.join(options.gwdir, "samples/scripts"))

    # Wait for it to come up.
    waitForPort(options.port)

if __name__ == "__main__":
    parseOptions()
    configureOAuth()


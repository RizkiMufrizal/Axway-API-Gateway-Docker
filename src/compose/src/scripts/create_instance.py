#!/usr/bin/env python2.7
'''
Script for creating instances.
'''
import os
import socket
import glob
import argparse
from lib.scriptutil import *

hostname = socket.gethostname()
ip = socket.gethostbyname(hostname)

def parseOptions() :
    global options

    parser = argparse.ArgumentParser()
    parser.add_argument("--gwdir")
    parser.add_argument("--username", default="admin")
    parser.add_argument("--password", default="changeme")
    parser.add_argument("-g", "--group")
    parser.add_argument("-n", "--instance")
    parser.add_argument("--current_version")

    # Passphrased creation requires the group to be created before
    # setting the passphrase, so we'll do this on the first instance
    # in the group.
    parser.add_argument("--first", action="store_true", help="Need to set the passphrase after creating the first instance.")

    # Managedomain args
    parser.add_argument("-m", "--mgmtPort", default="8085")
    parser.add_argument("-s", "--svcPort", default="8080")
    parser.add_argument("--domain_passphrase")
    parser.add_argument("--passphrase")

    (options, unknown) = parser.parse_known_args()

    if not options.gwdir :
        parser.error("No gateway directory specified.")

    if not options.current_version:
        parser.error("No gateway version specified.")

    if not options.gwdir :
        parser.error("No gateway directory specified.")

    if not os.path.isdir(options.gwdir) :
        parser.error("Directory not found: %s" % options.gwdir)

    if not options.group :
        parser.error("No group specified.")

    if not options.instance :
        parser.error("No instance specified.")

def createInstance() :
    banner("""Creating instance on %s: %s:%s
Instance Management Port: %s
Instance Services Port:   %s""" % (hostname, options.group, options.instance, options.mgmtPort, options.svcPort))

    # Each group needs a dediciated ip...created it if this is the first in this group.
    groupPath = os.path.join(options.gwdir, "groups", "topologylinks", options.group)

    additionalArgs = []
    if options.domain_passphrase :
        additionalArgs.extend(["--domain_passphrase", options.domain_passphrase])

    groupArgs = []
    if not options.first and options.passphrase :
        groupArgs.extend(["--passphrase", options.passphrase])

    execute(os.path.join(options.gwdir, "posix/bin/managedomain"), ["-c",
        "-g", options.group,
        "-n", options.instance,
        "--username", options.username,
        "--password", options.password,
        "-m", options.mgmtPort,
        "-s", options.svcPort] + additionalArgs + groupArgs)

    if options.first and options.passphrase :
        if options.current_version == "7.2.2" :
            # Dumb Dumb Dumb....7.2.2. the change_passphrase cli option is documented but not implemented...patching it on the fly
            replaceAll(os.path.join(options.gwdir, "system/lib/jython/managedomain.py"), [
                ("        or options.edit_host", "        or options.edit_host\n        or options.change_passphrase"),
                ("    if options.edit_host:",  """
    if options.change_passphrase:
        groupname = getGroupParam(False, options, manageDomainUtil)
        (oldPassphrase, newPassphrase) = getOldNewPassphrase(False, options)
        manageDomainUtil.updateGroupPassphrase(groupname, oldPassphrase, newPassphrase)
        sys.exit(0)

    if options.edit_host : """)])

        # Change the passphrase
        execute(os.path.join(options.gwdir, "posix/bin/managedomain"), ["--change_passphrase",
            "-g", options.group,
            "-n", options.instance,
            "--username", options.username,
            "--password", options.password,
            "--old_passphrase", "",
            "--new_passphrase", options.passphrase] + additionalArgs)

if __name__ == "__main__":
    parseOptions()
    createInstance()

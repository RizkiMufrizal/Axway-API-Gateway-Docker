#!/usr/bin/env python2.7
'''
Script for configuring nodemanager
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
    parser.add_argument("--anm_host")
    parser.add_argument("--current_version", default="7.3.1")
    parser.add_argument("--username", default="admin")
    parser.add_argument("--password", default="changeme")

    parser.add_argument("--secondary_anm", action="store_true")

    # Manage Domain flags
    parser.add_argument("--sign_alg")
    parser.add_argument("--domain_name")
    parser.add_argument("--domain_passphrase")
    parser.add_argument("--key_passphrase")
    parser.add_argument("--port")
    parser.add_argument("--name")
    # Enable Metrics
    parser.add_argument("--metrics_enabled")
    parser.add_argument("--metrics_dburl")
    parser.add_argument("--metrics_dbuser")
    parser.add_argument("--metrics_dbpass")

    (options, unknown) = parser.parse_known_args()

    if not options.gwdir :
        parser.error("No gateway directory specified.")

    if not options.gwdir :
        parser.error("No gateway directory specified.")

    if not os.path.isdir(options.gwdir) :
        parser.error("Directory not found: %s" % options.gwdir)

def configureNodeManager() :
    if options.metrics_enabled :
        configureMetricsDatabase()

    if options.anm_host and options.anm_host != "localhost" and options.anm_host != hostname :
        configureStandardNode()
    else :
        configureANMNode()

    startNodeManager()


def configureANMNode() :
    banner("Configuring Admin NodeManager on %s: %s" % (hostname, options.gwdir))
    # 1. Configure
    configureDNS()

    # 2. Initialize domain
    additionalArgs = []
    if options.sign_alg :
        additionalArgs.extend(["--sign_alg", options.sign_alg])

    if options.domain_name :
        additionalArgs.extend(["--domain_name", options.domain_name])

    if options.domain_passphrase :
        additionalArgs.extend(["--domain_passphrase", options.domain_passphrase])

    if options.key_passphrase :
        additionalArgs.extend(["--key_passphrase", options.key_passphrase])

    if options.port :
        additionalArgs.extend(["--port", options.port])

    if options.name :
        additionalArgs.extend(["--name", options.name])

    if options.metrics_enabled :
        additionalArgs.extend(["--metrics_enabled", "1"])
        additionalArgs.extend(["--metrics_dburl", options.metrics_dburl])
        additionalArgs.extend(["--metrics_dbuser", options.metrics_dbuser])
        additionalArgs.extend(["--metrics_dbpass", options.metrics_dbpass])

    execute(os.path.join(options.gwdir, "posix/bin/managedomain"), ["-i"] + additionalArgs)


def configureStandardNode() :
    banner("""Configuring Standard NodeManager on %s: %s
Admin Host: %s""" % (hostname, options.gwdir, options.anm_host))

    # 1. Register local ip in DNS
    configureDNS()

    # 2. Register with ANM
    additionalArgs = []
    if options.domain_passphrase :
        additionalArgs.extend(["--domain_passphrase", options.domain_passphrase])

    if options.metrics_enabled :
        additionalArgs.extend(["--metrics_enabled", "1"])
        additionalArgs.extend(["--metrics_dburl", options.metrics_dburl])
        additionalArgs.extend(["--metrics_dbuser", options.metrics_dbuser])
        additionalArgs.extend(["--metrics_dbpass", options.metrics_dbpass])

    if options.current_version <= "7.3.0" :
        execute(os.path.join(options.gwdir, "posix/bin/managedomain"), ["-a",
            "--host", hostname, 
            "--remote_host", options.anm_host,
            "--username", options.username,
            "--password", options.password] + additionalArgs)
    else :
        execute(os.path.join(options.gwdir, "posix/bin/managedomain"), ["-a",
            "--host", hostname, 
            "--anm_host", options.anm_host,
            "--username", options.username,
            "--password", options.password] + additionalArgs)


    if options.secondary_anm :
        execute(os.path.join(options.gwdir, "posix/bin/managedomain"), ["--edit_host",
            "--host", hostname, 
            "--username", options.username,
            "--password", options.password,
            "--is_admin", "1"])

def configureDNS() :
    configureResolvConf()
    registerWithDNS(hostname, ip)


def startNodeManager() :
    execute(os.path.join(options.gwdir, "posix/bin/nodemanager"), ["-d"])

def configureMetricsDatabase():
    additionalArgs = []
    execute(os.path.join(options.gwdir, "posix/bin/dbsetup"), ["--dburl", options.metrics_dburl,
        "--dbuser", options.metrics_dbuser,
        "--dbpass", options.metrics_dbpass,
        "--reinstall"] + additionalArgs)
if __name__ == "__main__":
    parseOptions()
    configureNodeManager()


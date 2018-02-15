#!/usr/bin/env python2.7
'''
Script for configuring cassandra-tools-jvm.xml
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
    parser.add_argument("-g", "--group")
    parser.add_argument("-n", "--instance")
    (options, unknown) = parser.parse_known_args()

    if not options.gwdir :
        parser.error("No gateway directory specified.")

    if not options.gwdir :
        parser.error("No gateway directory specified.")

    if not os.path.isdir(options.gwdir) :
        parser.error("Directory not found: %s" % options.gwdir)

    if not options.group :
        parser.error("No group specified.")

    if not options.instance :
        parser.error("No instance specified.")

def configureCassandraToolsJvm(options) :
    cassandraTools = os.path.join(options.gwdir, "system/conf/cassandra-tools-jvm.xml")
    cfgStr="""<SystemProperty name="cassandra.config" value="file://%s/groups/topologylinks/%s-%s/conf/kps/cassandra/cassandra.yaml"/>""" % (options.gwdir, options.group, options.instance)
    replaceAll(cassandraTools, [
        (r'^.*<SystemProperty name="cassandra.config".*$', ''), 
        (r'^(.*</JVMSettings>.*)$', r'%s\n\1' % cfgStr)])

if __name__ == "__main__":
    parseOptions()
    configureCassandraToolsJvm(options)


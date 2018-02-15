#!/usr/bin/env python2.7
#
#
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "../core/src"))
"""Util to copy to live Axway Compose env

Usage:
    cp --config <conffile>  <container name>:<path>  <local path>
    cp --config <conffile>  <local path>  <container name>:<path>
    cp --version

Options:
    --config <conffile> The json topology description
"""

VERSION = "0.1.0"

from optparse import OptionParser
from core.config import *
from core.docker import *
from core.template import addTemplateKey

def parseOptions() :
    parser = OptionParser()
    parser.add_option("-c", "--config", help="The JSON file defining the topology.")

    (options, args) = parser.parse_args()

    if not options.config :
        parser.error("No config file given")

    if len(args) != 2 :
        parser.error("Invalid number of arguments")

    return (options, args)


def copyFrom(container, src, target) :
    print "Copying from (%s) %s -> %s" % (container["runtime"], src, target)
    dockerCp(container["runtime"], src, target)

def copyTo(container, src, target) :
    print "Copying to %s -> (%s) %s" % (src, container["runtime"], target)
    dockerCpTo(container["runtime"], src, target)


def copy(config, src, dest) :
    srctoks = string.split(src, ":", 2)
    desttoks = string.split(dest, ":", 2)

    if len(srctoks) <= 1 and len(desttoks) <= 1 :
        raise Exception("No container name specified.")

    if len(srctoks) > 1 :
        copyFrom(config.getContainer(srctoks[0]), srctoks[1], dest)
    else :
        copyTo(config.getContainer(desttoks[0]), src, desttoks[1])

def addTemplateKeys() :
    '''
    Add the template replacement params. For now just {compose-root} to 
    reference the root install. Try install location or (for dev) ../compose
    '''
    root =  os.path.dirname(__file__)
    composeRoot = os.path.join(root, "../compose")

    if os.path.exists(composeRoot) :
        composeRoot = os.path.abspath(composeRoot) 
        addTemplateKey("compose-root", composeRoot)
    else :
        print "Warning: No {compose-root} value specified."


def main() :
    (options, args) = parseOptions()
    addTemplateKeys()
    config = Config(options.config)
    copy(config, args[0], args[1])

if __name__ == "__main__":
    main()

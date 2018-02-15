#!/usr/bin/env python2.7
#
#
"""Axway Compose

Usage:
    axway-compose --config <conffile>  [--clean] [--build] [--start|--stop|--restart]
    axway-compose --version

Options:
    --config <conffile> The json topology description
    --clean             Delete the associated containers and images.
    --baseos            Base OS Image to be used by cassandra
    --build             Build the images described in the topology.
    --image             Base API Gateway Docker image name.
    --start             Start the containers described in the topology.
    --restart           Restart the containers described in the topology.
    --stop              Stop the containers described in the topology.

"""
import os
import time
from datetime import datetime
import argparse
from util import isFrozen, addTemplateKeys
#from build.builder import Builder
#from build.runner import Runner
from core.config import BuildConfig, Config
from core.util import banner,output
from core import cmd_config
from version import VERSION
from scripts.lib import settings

from build.engine import *

def parseOptions() :
    if isFrozen() :
        defaultRoot =  os.path.dirname(sys.executable)
    elif __file__:
        defaultRoot =  os.path.dirname(__file__)

    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--version", action="store_true", help="Display the version.")
    parser.add_argument("-c", "--config", default="apigw-topology-config.json", help="The JSON file defining the topology.")
    parser.add_argument("-r", "--root", default=defaultRoot)
    parser.add_argument("-i", "--image", help="Base API Gateway Docker image name. Uses gwlatest_<baseos> by default, where <baseos> is the value of the --baseos parameter.")
    parser.add_argument("--baseos", default="centos", help="Base OS Image to be used.")
    parser.add_argument("--verbose", action="store_true", help="Run docker-compose with verbose mode")
    parser.add_argument("--keep", action="store_true", help="Don't cleanup build topology. Allows for investigation into build issues.")
    # runAction: start|restart
    parser.add_argument("--desktop", action="append", type=str, dest="desktops", help="Configure the container for desktop interaction.")
    parser.add_argument("--expose", action="append", type=str, dest="ports", help="Bind the container ports to the host. Format <container name>[:<host port>]:<container port>")
    parser.add_argument("--volume", action="append", type=str, dest="volumes", help="Add volume mounts. Format <container name>:<host path>:<container path>")

    (options, unknown) = parser.parse_known_args()

    if not options.version :
        if not options.config :
            parser.error("No config file given")

        if not options.image:
            options.image = "gwlatest_%s" % options.baseos

        if options.ports and not (options.runAction == "start" or options.runAction == "restart") :
            parser.error("Exposed ports are only for use with start or restart.")

        if options.volumes and not (options.runAction == "start" or options.runAction == "restart") :
            parser.error("Volumes are only for use with start or restart.")

        if options.desktops and not (options.runAction == "start" or options.runAction == "restart") :
            parser.error("Desktop is only for use with start or restart.")

    return options


def main():
    options = parseOptions()

    if options.version :
        print VERSION
        return

    if options.verbose :
        cmd_config.VERBOSE = "--verbose"

    print "Using Base API Gateway Docker image name: %s" % options.image
    os.environ["API_GATEWAY_IMAGE_NAME"] = options.image
   
    addTemplateKeys(options.root)

    builder = BuilderEngine(BuildConfig(options.config), options.root, options.baseos, options.keep)
    runner = RunnerEngine(Config(options.config), options.root, options.baseos, {
        "ports" : options.ports,
        "volumes" : options.volumes,
        "desktops" : options.desktops
        })

    timing = {}
    timing["summary"] = builder.config.summarize()

    startTime = datetime.now()
    runner.clean()
    builder.clean()    
    builder.build()    
    runner.build()
    timing["generate"] = str(datetime.now() - startTime)


    summaryMsg=("Summary\n" +
         timing["summary"] + "\n" +
         ("" if "generate" not in timing else    "\n    Generate took    : %s" % timing["generate"])) 

    banner(summaryMsg)
    output("summary.txt", summaryMsg)

if __name__ == '__main__':
    main()

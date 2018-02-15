from ..processor import Processor
import os
import sys
import re
from core.util import *
from core.docker import *
from analyticscommand import *


class AnalyticsConfigProcessor(Processor) :
    '''
    The entry point for processing the analytics configuration.
    '''
    KEY = 'analyticsConfig'

    def __init__(self, engine, config) :
        super(AnalyticsConfigProcessor, self).__init__(engine, AnalyticsConfigProcessor.KEY, config)
        self.config = config

    def buildPhase3(self, container, node) :
        print "Building analytics"
        ConfigureAnalyticsServer(container, self.config).execute()


    def _getLaunchCmd(self, container, node) :
        return ["/scripts/manage_analytics.py --gwdir %s --start " % node["installPathCurrent"]]

from ..util.command import *
from core.docker import *
from core.util import *

                
class ConfigureAnalyticsServer(Command) :
    def __init__(self, container, config) :
        super(ConfigureAnalyticsServer, self).__init__(config)
        additionalArgs = []

        scriptcmd = [
            "/scripts/manage_analytics.py", 
            "--gwdir", container["analyticsConfig"]["installPathCurrent"], 
            "--dburl", container["analyticsConfig"]["dburl"], 
            "--dbuser", container["analyticsConfig"]["dbuser"], 
            "--dbpass", container["analyticsConfig"]["dbpass"], 
            "--configure", 
            "--current_version", container["gatewayConfig"]["currentVersion"],
            ] + additionalArgs
        self.cmds.append((container["runtime"], scriptcmd, None))

        scriptcmd = [
            "/scripts/manage_analytics.py",
            "--gwdir", container["analyticsConfig"]["installPathCurrent"],
            "--start",
            "--current_version", container["gatewayConfig"]["currentVersion"],
            ] + additionalArgs
        self.cmds.append((container["runtime"], scriptcmd, None))


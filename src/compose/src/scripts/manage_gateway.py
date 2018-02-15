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
import glob
from lib.scriptutil import *


hostname = os.getenv('EXT_HOSTNAME', socket.gethostname())
ip = socket.gethostbyname(hostname)

def parseOptions() :
    global options

    parser = argparse.ArgumentParser()
    parser.add_argument("--gwdir")

    parser.add_argument("--backoff", action="store_true", default=False)
    parser.add_argument("--start", action="store_const", dest="action", const="start")
    parser.add_argument("--stop", action="store_const", dest="action", const="stop")
    parser.add_argument("--backupRecover",  action="store_true", default=False)
    parser.add_argument("--wait", action="store_const", dest="action", const="wait")
    parser.add_argument("--nm", action="store_true", help="Apply action to nodemanager")
    parser.add_argument("-a", "--all", action="store_true", help="Apply action to all instances")
    parser.add_argument("-g", "--group", help="Specific group to apply action to")
    parser.add_argument("-n", "--instance", help="Specific instance to apply action to")
    parser.add_argument("--analytics", action="store_true", help="Start Analytics too")
    parser.add_argument("--apimgr",  action="store_true", dest="hasapimgr", default=False)

    parser.add_argument("-b", "--block", action="store_true", help="Don't exit after starting.")

    parser.add_argument("-D", action="append", type=str, dest="properties", help="Properties passed to the vshell commandline.")

    (options, unknown) = parser.parse_known_args()

    if not options.gwdir :
        parser.error("No gateway directory specified.")

    
    if not options.gwdir :
        parser.error("No gateway directory specified.")

    if not os.path.isdir(options.gwdir) :
        parser.error("Directory not found: %s" % options.gwdir)

    if not options.all and not options.nm :
        if not options.group :
            parser.error("No group specified.")

        if not options.instance :
            parser.error("No instance specified.")


def setupCassandra(gw_dir):
    confDirs = getConfDirectories(os.path.join(os.sep,"opt","Axway","apigateway"))
    if not confDirs:
        return 
    for confDir in confDirs:
       print "Setting Cassandra Hosts on %s" % confDir
       args = [ os.path.join(os.sep,"scripts", "configure_cassandrahostsandreplication.py"), 
               "--esFile", os.path.join(confDir,"configs.xml")]
       casHosts = os.getenv('CASSANDRA_HOSTS', "cassandra-m,cassandra-s1,cassandra-s2").split(",")
       for casHost in casHosts:
         args.append("--hostAndPort")
         args.append(casHost + ":9042")
         
       execute(os.path.join(gw_dir, "samples/scripts/run.sh"), 
               args,
               cwd = os.path.join(gw_dir,"samples","scripts"))

    print "Finished Setting up cassandra on %s" % gw_dir


def changeAPIAdminPwd(gwdir,group,name,user,passwd,adminName,adminPasswd):
    banner("Changing password for  %s %s" % (group,name))
    args = ["--resetPassword",
 	    "-g", group,
            "-n", name,
            "--username", user,
            "--password", passwd,
            "--adminName", adminName,
            "--adminPass", adminPasswd]
    execute(os.path.join(gwdir, "posix/bin/setup-apimanager"), args)


def initialiseLicense(gwdir) :
    licPath = os.path.join(gwdir,"conf","licenses")
    gwlicFile = os.path.join(licPath,"lic.lic")
    licenseFromEnv = os.getenv('APIGW_LICENSE')
    licValue = None
    if licenseFromEnv:
        print "Environment variable APIGW_LICENSE is set"
        #obtain unzipped and base64 decoded license string and write to new file
        try:
            licValue = getDecompressedBase64Lic(licenseFromEnv)
        except:
            warnmessage = "WARNING - The format of the APIGW_LICENSE environment variable is not valid \n"
            formatmessage = 'Format must be: export APIGW_LICENSE="$(cat /path/to/mylicense/lic.lic | gzip | base64)"\n'
            raise Exception(warnmessage + formatmessage)
    else:
        if len(glob.glob1(licPath,"*.lic")) < 1:
            nolicfoundmessage = "Environment variable APIGW_LICENSE is not set and no license(s) were found in %s" % licPath
            raise Exception(nolicfoundmessage)



    if licValue:
        print "Checking if a license file named %s exists" %gwlicFile
        licFileExists = True if os.path.exists(gwlicFile) else False
        if not licFileExists:
            print "Adding license file %s to the container" % gwlicFile
        else:
            print "%s file already exists . Overriding this with value found in environment variable APIGW_LICENSE " %gwlicFile

        with open(gwlicFile, 'w') as f:
            f.write(licValue)


def manageGateway() :
    if options.backoff :
        backoffSecs = os.getenv('START_BACKOFF_SECS', "0")
        print "Instance backoff %s seconds" % backoffSecs
        time.sleep(float(backoffSecs))
    elif options.action == 'start' :
        casFile = os.path.join(options.gwdir,"groups",".setupCas")
        if options.backupRecover and not os.path.exists(casFile) :
            setupCassandra(options.gwdir)
            with open(casFile, 'w') as f:
    	        f.write('done') 

        initialiseLicense(options.gwdir)

        if options.nm :
            startNodeManager(options.gwdir, options.properties)

        if options.analytics :
            startAnalytics(options.gwdir)

        if options.all :
            startAll(options.gwdir, options.properties)
        elif options.instance :
            startInstance(options.gwdir, options.group, options.instance, options.properties)

    elif  options.action == 'stop' :
        if options.all :
            stopAll(options.gwdir)
        elif options.instance :
            stopInstance(options.gwdir, options.group, options.instance)

        if options.nm :
            stopNodeManager(options.gwdir)

    elif  options.action == 'wait' :
        if options.nm :
            waitNodeManager(options.gwdir)

        if options.all :
            waitAll(options.gwdir)
        elif options.instance :
            waitInstance(options.gwdir, options.group, options.instance)



def startNodeManager(gwdir, properties = None) :
    banner("Starting NodeManager on %s" % (hostname))

    detail = getNodeManagerFromTopology(gwdir, hostname)
    managementPort = detail["managementPort"]

    # Register this host with the dns server running on anm.
    configureResolvConf()
    registerWithDNS(hostname, ip)

    args = []
    if properties is not None :
        for prop in properties :
            args.append("-D%s" % prop)
    args.append("-d")
    execute(os.path.join(gwdir, "posix/bin/nodemanager"), args)

    waitForPort(managementPort)


def killProcess(pid, sig) :
    print "Killing: %s" % (str(pid))
    os.kill(pid, signal.SIGKILL)


def stopNodeManager(gwdir, forceDelay = 30.0) :
    banner("Stopping NodeManager on %s" % (hostname))

    detail = getNodeManagerFromTopology(gwdir, hostname)
    managementPort = detail["managementPort"]

    # Start a thread - sometimes NM hangs (kill it if it hangs)
    stopTimer = None
    pidFile = os.path.join(gwdir, "conf", detail["id"] + ".pid")
    pid = -1
    with open(pidFile, "r") as p :
        pid = int(p.read())

    if pid > 0 :
        stopTimer = threading.Timer(forceDelay, killProcess, (pid, signal.SIGKILL))
        stopTimer.start()

    # Try stopping cleanly.
    if testPort(managementPort) :
        proc = execute(os.path.join(gwdir, "posix/bin/nodemanager"), ["-k"], wait = False)
        waitForPortClose(managementPort)
        proc.kill()

    if stopTimer :
        stopTimer.cancel()


def waitNodeManager(gwdir) :
    banner("Waiting for NodeManager on %s" % (hostname))
    detail = getNodeManagerFromTopology(gwdir, hostname)
    managementPort = detail["managementPort"]
    waitForPort(managementPort)


def startAll(gwdir, properties = None) :
    banner("Starting instances on %s" % (hostname))

    instancesByGroup = getInstancesFromTopology(gwdir,hostname)

    for group, instances in instancesByGroup.iteritems() :
        for instance in instances :
            startInstance(gwdir, group, instance["name"], properties, instance["managementPort"])


def startInstance(gwdir, group, instance, properties = None, managementPort = None) :
    banner("Starting instance %s: %s:%s" % (hostname, group, instance))

    if managementPort is None :
        detail = getInstanceByNameFromTopology(gwdir, group, instance, hostname)
        managementPort = detail["managementPort"]

    args = ["-g", group, "-n", instance]
    if properties is not None :
        for prop in properties :
            args.append("-D%s" % prop)
    args.append("-d")

    execute(os.path.join(gwdir, "posix/bin/startinstance"), args)

    waitForPort(managementPort)
    pasFile = os.path.join(gwdir,"groups",".setupPas")
    if options.backupRecover and not os.path.exists(pasFile) and options.hasapimgr:
    	changeAPIAdminPwd(gwdir,group,instance,"admin","changeme","apiadmin","changeme")
        with open(pasFile, 'w') as f:  
                f.write('done')

def startAnalytics(gwdir) :
    banner("Starting Analytics %s" % (hostname))

    execute(os.path.join(gwdir.replace("apigateway","analytics"), "posix/bin/analytics"), [
        "-k"])
    execute(os.path.join(gwdir.replace("apigateway","analytics"), "posix/bin/analytics"), [
        "-d"])

    waitForPort(8040)


def waitAll(gwdir) :
    banner("Waiting for instances on %s" % (hostname))

    instancesByGroup = getInstancesFromTopology(gwdir)

    for group, instances in instancesByGroup.iteritems() :
        for instance in instances :
            waitInstance(gwdir, group, instance["name"], instance["managementPort"])


def waitInstance(gwdir, group, instance, managementPort = None) :
    banner("Waiting for instance %s: %s:%s" % (hostname, group, instance))
    if managementPort is None :
        detail = getInstanceByNameFromTopology(gwdir, group, instance, hostname)
        managementPort = detail["managementPort"]
    waitForPort(managementPort)


def stopAll(gwdir) :
    banner("Stopping instances on %s" % (hostname))

    instancesByGroup = getInstancesFromTopology(gwdir)

    for group, instances in instancesByGroup.iteritems() :
        for instance in instances :
            stopInstance(gwdir, group, instance["name"], instance["managementPort"])


def stopInstance(gwdir, group, instance, managementPort = None) :
    banner("Stopping instance %s: %s:%s" % (hostname, group, instance))

    if managementPort is None :
        detail = getInstanceByNameFromTopology(gwdir, group, instance, hostname)
        managementPort = detail["managementPort"]

    proc = execute(os.path.join(gwdir, "posix/bin/startinstance"), [
        "-g", group,
        "-n", instance,
        "-k"], wait = False)
    waitForPortClose(managementPort)
    proc.kill()



def unblock(signal, frame) :
    global block
    print "Exiting"
    block = False

if __name__ == "__main__":
    parseOptions()
    manageGateway()


    if options.block :
        global block
        block = options.block
        banner("Staying alive")
        signal.signal(signal.SIGINT, unblock)
        while block :
            time.sleep(5)

import os
import json
import socket
import socket
import fcntl
import struct
import array
import subprocess
import time
import errno
import re
import cStringIO
from datetime import datetime, timedelta
from settings import TIMEOUT
from gzip import GzipFile
from base64 import b64decode

def banner(msg) :
    print "--------------------------------------------------------------------------------"
    print msg
    print "--------------------------------------------------------------------------------"


def execute(cmd, args = [], wait = True, cwd = None, failOnError = True, noOutput= False) :
    if noOutput:
        devnull = open(os.devnull, 'wb')
        proc = subprocess.Popen([cmd] + args, stdout=devnull,stderr=devnull, cwd = cwd)
    else:
        print " ".join([cmd] + args)
        proc = subprocess.Popen([cmd] + args, stderr=subprocess.STDOUT, cwd = cwd)

    if wait :
        if not noOutput:
            print "Waiting for %s" % cmd
        proc.wait()
        if not noOutput:
            print "%s finished, exit code %d" % (cmd, proc.returncode)
        if failOnError and proc.returncode != 0:
            raise Exception("Command failed. Exit status %d" % proc.returncode)
        else :
            return proc.returncode
    return proc

def testPort(port, host="localhost") :
    try:
        host_addr = socket.gethostbyname(host)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        s.connect((host, int(port)))
        s.close()
    except:
        return False

    return True
    
def waitForPort(port, host="localhost", timeout=TIMEOUT) :
    end = datetime.now() + timedelta(0,timeout)
    print "Wait for port to open with timeout: %s" % timeout
    isOpen = testPort(port, host);

    if not isOpen :
        while (datetime.now() <= end) :
            time.sleep(3)
            isOpen = testPort(port, host);

            if isOpen :
                break

    if not isOpen :
        raise Exception("Timeout waiting for port %s on %s" % (str(port), host))

def getConfDirectories(apigwDir) :
    topologyJson = os.path.join(apigwDir, "groups", "deployments.json")
    if not os.path.isfile(topologyJson):
        return None
    jsonStr = open(topologyJson).read()
    deploymentsData = json.loads(jsonStr)
    groupDirs = []

    for instanceId, instanceConfs in deploymentsData["serviceDeployments"].items():
        for instanceConf in instanceConfs :
            for groupId, group in deploymentsData["deploymentArchives"].items():
               for confId in group.keys():
                   if confId == instanceConf["archiveID"]:
                       groupDirs.append(os.path.join(apigwDir, "groups", groupId,"conf",instanceConf["archiveID"]))

    return groupDirs

def waitForPortClose(port, host="localhost", timeout=TIMEOUT) :
    end = datetime.now() + timedelta(0,timeout)

    isOpen = testPort(port, host);

    if isOpen :
        while (datetime.now() <= end) :
            time.sleep(3)
            isOpen = testPort(port, host);

            if not isOpen :
                break

    if isOpen :
        raise Exception("Timeout waiting for port %s to close on %s" % (str(port), host))


def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc: # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else: raise



def replaceAll(file, findAndReplace) :
    fh = open(file, 'r')
    data = fh.read()
    fh.close()

    for (find, replace) in findAndReplace :
        pattern = re.compile(find, re.MULTILINE)
        data = pattern.sub(replace, data)

    fh = open(file, 'w')
    fh.write(data)
    fh.close()


def findInFile(file, find) :
    pattern = re.compile(find, re.MULTILINE)
    fh = open(file, 'r')
    data = fh.read()
    fh.close()

    result = pattern.findall(data)

    return result


def _getTopologyAndHostId(gwdir, hostname=None) :
    if hostname == None :
        hostname = socket.gethostname()

    topologyJson = os.path.join(gwdir, "groups", "topology.json")   
    jsonStr = open(topologyJson).read()
    topologyData = json.loads(jsonStr)

    # Get the host id
    hostId = None
    for host in topologyData["hosts"] :
        if host["name"] == hostname :
            hostId = host["id"]
            break

    return (topologyData, hostId)


def getIdFromTopology(gwdir) :
    (topologyData, localHostId) = _getTopologyAndHostId(gwdir, None)
    result = None
    return topologyData["id"]


def getProductVersionFromTopology(gwdir) :
    (topologyData, localHostId) = _getTopologyAndHostId(gwdir, None)
    result = None
    return topologyData["productVersion"]


def getHostFromTopology(gwdir, hostId) :
    (topologyData, localHostId) = _getTopologyAndHostId(gwdir, None)
    result = None
    for host in topologyData["hosts"] :
        if host["id"] == hostId :
            result = host["name"]
            break
    return result


def getNodeManagerFromTopology(gwdir, hostname=None) :
    (topologyData, hostId) = _getTopologyAndHostId(gwdir, hostname)
    result = None
    for group in topologyData["groups"] :
        for instance in group["services"] :
            if instance["type"] == "nodemanager" and instance["hostID"] == hostId :
                result=instance
                break
    return result


def getAdminNodeManagerFromTopology(gwdir) :
    (topologyData, hostId) = _getTopologyAndHostId(gwdir, None)
    result = None
    for group in topologyData["groups"] :
        for instance in group["services"] :
            if instance["type"] == "nodemanager" and "internal_admin_nm" in instance["tags"] and instance["tags"]["internal_admin_nm"]:
                result=instance
                break
    return result


def getGroupsFromTopology(gwdir, hostname=None) :
    (topologyData, hostId) = _getTopologyAndHostId(gwdir, hostname)

    result = []
    for group in topologyData["groups"] :
        if group["name"] not in result :
            result.append(group["name"])
    return result


def getGroupIdFromTopology(gwdir, group, hostname=None) :
    (topologyData, hostId) = _getTopologyAndHostId(gwdir, hostname)

    for grp in topologyData["groups"] :
        if grp["name"] != group :
            continue
        return grp["id"]
    return None


def getInstancesFromTopology(gwdir, hostname=None) :
    (topologyData, hostId) = _getTopologyAndHostId(gwdir, hostname)

    result = {}
    for group in topologyData["groups"] :
        if group["name"] not in result :
            result[group["name"]] = []

        for instance in group["services"] :
            if instance["type"] == "gateway" and instance["hostID"] == hostId :
                result[group["name"]].append(instance)
    return result


def getInstanceByNameFromTopology(gwdir, group, instance, hostname=None) :
    (topologyData, hostId) = _getTopologyAndHostId(gwdir, hostname)

    # Get the instance
    result = None
    for grp in topologyData["groups"] :
        if grp["name"] != group :
            continue

        for inst in grp["services"] :
            if inst["name"] == instance and inst["hostID"] == hostId :
                result = inst
                break
    return result


def getInterface(interface):
    ifs = getInterfaces("^" + interface + "$")
    return None if len(ifs) == 0 else ifs[0]


def getInterfaces(match = None):
    maxPossible = 256
    buffer = maxPossible * 32

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    names = array.array('B', '\0' * buffer)
    outbytes = struct.unpack('iL', fcntl.ioctl(
        s.fileno(),
        0x8912,  # SIOCGIFCONF
        struct.pack('iL', buffer, names.buffer_info()[0])
    ))[0]

    namesStr = names.tostring()
    ifdetail = []
    for i in range(0, outbytes, 40):
        name = namesStr[i:i+16].split('\0', 1)[0]
        ip   = namesStr[i+20:i+24]

        if not match or re.match(match, name) :
            quad = [ord(ip[0]), ord(ip[1]), ord(ip[2]), ord(ip[3])]
            ipstr = quadToIp(quad)
            ifdetail.append((name, ipstr, quad))
    return ifdetail

def quadToIp(quad) :
    return "%s.%s.%s.%s" % (str(quad[0]), str(quad[1]), str(quad[2]), str(quad[3]))


def getGroupHostName(hostname, group) :
    return "%s_%s" % (hostname, re.sub("[,\-\s\*\.=#&\^%\$]", "", group).lower())


def configureResolvConf(dnsserver = "dns") :
    '''
    nameserverip = socket.gethostbyname(dnsserver)    
    data = ""
    with open("/etc/resolv.conf", "r") as resolvConf :
        data = resolvConf.read()

    data = "nameserver\t%s\n%s" % (nameserverip, data)
    with open("/etc/resolv.conf", "w") as resolvConf :
        resolvConf.write(data)
    execute("/sbin/resolvconf", ["-u"])
    '''


def registerWithDNS(hostname, ip, dnsserver = "dns") :
    '''
    # Using our custom nodejs dns server we can inject via http
    print "- Registering ip with DNS Server %s: [%s    %s]" % (dnsserver, hostname, ip)
    waitForPort(5353, dnsserver)
    r = requests.put("http://%s:5353/%s?ip=%s" % (dnsserver, hostname, ip))
    print(r.text)
    r.close()
    '''
    
def registerInHosts(hostname, ip) :
    banner("Adding to /etc/hosts %s:%s" % (hostname, ip))
    hostsfile = "/etc/hosts"
    replaceAll(hostsfile, [
        (r'.* %s$' % hostname, ''),
        (r'\n\Z', '\n%s %s\n' % (ip, hostname))])


def configureEnvProperties(gwdir, group, instance, properties) :
    '''
    Add properties to envSettings.props. 
    properties: [("key", "value"),...]
    '''
    envSettings = os.path.join(gwdir, "groups/topologylinks", "%s-%s" % (group, instance), "conf/envSettings.props")

    for (propKey, propVal) in properties :
        if (len(findInFile(envSettings, propKey + "=")) > 0) :
            # Modify existing value
            matchStr = r'^%s=.*$' % propKey
        else :
            # Append new value
            matchStr = r'\Z'

        replaceAll(envSettings, [(matchStr, '%s=%s\n' % (propKey, propVal))])

def getFirstInstanceInGroupIfExists(group, containername) :
    if not group["instances"]:
        print "No gateway instances found for group named %s on host %s" % (group["name"], containername)
        return None

    return group["instances"][0]

def getDecompressedBase64Lic(lic) :
    return GzipFile(fileobj=cStringIO.StringIO(b64decode(lic))).read()

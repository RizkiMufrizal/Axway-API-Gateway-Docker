import subprocess
import tarfile
import shutil
import string
import tempfile
from util import *

def dockerCreateRunContainer(name, image, cmd="run", commandLine = None, daemon = True, interacive = True,
        volumes=[], volumesFrom=[], hostname=None, links=[], privileged = False, labels = [], net=None) :
    args = []

    if daemon and cmd == "run" :
        args.append("-d")

    if interacive :
        args.append("-it")

    if net :
        args.extend(["--net", net])

    if hostname :
        args.extend(["-h", hostname])

    if cmd == "run" :
        args.append("--rm=false")

    for volume in volumes :
        args.extend(["-v", volume])

    for vf in volumesFrom :
        args.extend(["--volumes-from", vf])

    for link in links :
        args.extend(["--link", link])

    if name :
        args.extend(["--name", name])

    for label in labels :
        args.extend(["--label", label])

    if privileged :
        args.append("--privileged")

    args.append(image)

    if commandLine :
        args.extend(commandLine)

    docker(cmd, args)


def dockerExec(container, cmd, options = None) :
    args = []
    if options :
        args.extend(options)

    args.append(container)
    args.extend(cmd)

    docker("exec", args, logFrom = container )


def dockerCp(container, path, target, failOnError = True) :
    args = [ "%s:%s" % (container, path), target]
    return docker("cp", args, failOnError = failOnError)


def dockerCpTar(container, path, target) :
    cmd = ["docker", "cp", "%s:%s" % (container, path), "-"]
    with open(target, "wb") as targetFile :
        banner (" ".join(cmd))
        proc = subprocess.Popen(cmd, stderr=subprocess.STDOUT, stdout=targetFile)
        if proc.wait() != 0 :
            raise Exception("Command failed. Exit status %d" % proc.returncode)


def dockerCpTo(container, src, target) :
    '''
    docker cp doesn't yet allow copy from host to container so hack it by using
    stdin and tar.
    '''
    if not os.path.exists(src) :
        raise Exception("Not found: %s", src)

    tmpDir = tempfile.mkdtemp()
    try :
        if os.path.isdir(src) :
            # Copying a directory in to the container, need to tar it up
            dockerExec(container, ["mkdir", "-p", target])

            tarFileName = os.path.join(tmpDir, os.path.basename(src) + ".tar")
            with tarfile.open(tarFileName, "w") as tar:
                tar.add(src, arcname=".")

            srcPath = tarFileName
            expandCmd = ["/bin/tar", "-C", target, "-xf", "-"]

        else :
            # Copying a file
            dockerExec(container, ["mkdir", "-p", os.path.dirname(target)])

            srcPath = src
            expandCmd = ["tee", target]


        cmd = ["docker", "exec", "-i", container] + expandCmd
        with open(srcPath, "r") as srcFile :
            banner (" ".join(cmd))
            proc = subprocess.Popen(cmd, stderr=subprocess.STDOUT, stdin=srcFile)
            if proc.wait() != 0 :
                raise Exception("Command failed. Exit status %d" % proc.returncode)
    finally :
        shutil.rmtree(tmpDir)


def dockerCpTarTo(container, tar, target) :
    '''
    docker cp doesn't yet allow copy from host to container so hack it by using
    stdin and tar.
    '''
    dockerExec(container, ["mkdir", "-p", target])

    cmd = ["docker", "exec", "-i", container, "/bin/tar", "-C", target, "-xf", "-"]
    with open(tar, "r") as tarFile :
        banner (" ".join(cmd))
        proc = subprocess.Popen(cmd, stderr=subprocess.STDOUT, stdin=tarFile)
        if proc.wait() != 0 :
            raise Exception("Command failed. Exit status %d" % proc.returncode)


def dockerCommit(container, imageName, options = None) :
    args = []
    if options :
        args.extend(options)

    args.append(container)
    args.append(imageName)

    docker("commit", args)


def dockerRm(container, options = None, failOnError = True) :
    args = []
    if options :
        args.extend(options)
    args.append(container)
    docker("rm", args, failOnError = failOnError)


def dockerRmi(image, options = None, failOnError = True) :
    args = []
    if options :
        args.extend(options)
    args.append(image)
    docker("rmi", args=args, failOnError = failOnError)


def docker(cmd, args=[], logFrom = None, failOnError = True, stdout = None) :
    banner (" ".join(["docker", cmd] + args))
    proc = subprocess.Popen(["docker", cmd] + args, stdout=stdout, stderr=subprocess.STDOUT)

    if logFrom :
        logProc = subprocess.Popen(["docker", "logs", "--tail=0", "-f", logFrom], stderr=subprocess.STDOUT)

    proc.wait()

    if logFrom :
        logProc.kill()

    if proc.returncode != 0 and failOnError :
        raise Exception("Command failed. Exit status %d" % proc.returncode)
    else :
        return proc.returncode

def dockerInspect(container, template = None, failOnError = True) :
    args = []
    if template :
        args.extend(["-f", template])

    args.append(container)

    inspectFile = tempfile.NamedTemporaryFile(delete=True)
    docker("inspect", args, stdout=inspectFile, failOnError=failOnError)
    data=None
    with open (inspectFile.name, "r") as inspectFileRead:
        data=inspectFileRead.read()

    return data

def getContainerIpAndHost(name) :
    try :
        data = dockerInspect(name, "{{if eq .State.Running true}}{{.NetworkSettings.IPAddress}} {{.Config.Hostname}}{{end}}")
        data = data.replace("\n", "")
        detail = string.split(data, " ", 1)
    except :
        detail = None

    return detail if not detail or len(detail) == 2 else None


def dockerExport(container, tarAbsPath, options = None) :
    args = ["--output", tarAbsPath]
    if options :
        args.extend(options)
    args.append(container)
    docker("export", args)


def dockerImport(tarAbsPath, imageName, options = None) :
    args = []
    if options :
        args.extend(options)
    args.append(tarAbsPath)
    args.extend(["--", imageName])
    docker("import", args)

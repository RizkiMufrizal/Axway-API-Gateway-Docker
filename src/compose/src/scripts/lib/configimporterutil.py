import os
from lib.scriptutil import *

def importConfig(options, frags, **kwargs) :
    '''
    Helper to execute the config fragment import (jython util).
    '''
    if not options.gwdir :
        raise Exception("gwdir not set.")
    if not options.group :
        raise Exception("group not set.")
    if not options.instance :
        raise Exception("instance not set.")
    if not options.username :
        raise Exception("username not set.")
    if not options.password :
        raise Exception("password not set.")
    if options.passphrase is None:
        raise Exception("passphrase (for group) not set.")

    if not isinstance(frags, list) :
        frags = [frags]

    if len(frags) == 0 :
        return

    files = []
    for frag in frags:
        files.extend(["-f", frag])

    args = []
    for (k,v) in kwargs.iteritems() :
        if type(v) == type(list()) :
            for singleval in v :
                args.append("%s=%s" % (k,singleval))
        else :
            args.append("%s=%s" % (k,v))

    optional = [] 
    if options.passphrase:
        optional.extend(["--passphrase", options.passphrase])

    execute(os.path.join(options.gwdir, "samples/scripts/run.sh"), [
        os.path.join(os.path.dirname(__file__), "configimporter.py"),
        "-g", options.group,
        "-n", options.instance,
        "--username", options.username,
        "--password", options.password] + optional + files + args,
        cwd = os.path.join(options.gwdir, "samples/scripts"))
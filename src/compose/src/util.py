import os
import sys
from core.template import addTemplateKey


def isFrozen() :
    '''Built as an executable.'''
    return getattr(sys, 'frozen', False)


def addTemplateKeys(rootDir) :
    basedir = rootDir if isFrozen() else os.path.join(rootDir, "..")
    addTemplateKey("compose-root", basedir)
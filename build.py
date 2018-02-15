#!/usr/bin/env python2.7
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "core/src"))
from src.core.src.core.docker import *
from urlparse import urlparse
import argparse
import subprocess

def _clean(images):
    for image in images:
        dockerRmi(image, ["-f"], failOnError=False)

def _buildStatic(repo, imagedir):
    if not _imageExists(repo):
        print "Building docker image with repository name: %s from directory %s" % (repo, imagedir)
        docker("build", ["-t", repo, os.path.join("dockerfiles", imagedir)])
    else:
        print "Image: %s already exists. Not building this. " % repo

def _build(repo, imagedir):
    if not _imageExists(repo):
        print "Building docker image with repository name: %s from directory %s" % (repo, imagedir)
        path = os.path.join("dockerfiles", imagedir)

        if 'centos' in baseOs:
            docker("build", ["-t", repo, "-f", os.path.join(path, "Dockerfile.centos"), path])
        elif 'redhat' in baseOs:
            docker("build", ["-t", repo, "-f", os.path.join(path, "Dockerfile.redhat"), path])
        else:
            raise Exception('Cannot build image %s!' % repo)
    else:
        print "Image: %s already exists. Not building this. " % repo

def _buildSP(repo, imagedir):
    if not _imageExists(repo):
        print "Building api gateway docker image which includes service pack with repository name: %s from directory %s" % (repo, imagedir)
        path = os.path.join("dockerfiles", imagedir)
        if 'centos' in baseOs:
            docker("build", ["-t", repo, "-f", os.path.join(path, "Dockerfile.sp_centos"), path])            
        elif 'redhat' in baseOs:
            docker("build", ["-t", repo, "-f", os.path.join(path, "Dockerfile.sp_redhat"), path])
        else:
            raise Exception('Cannot build image %s!' % repo)
        
    else:
        print "Image: %s already exists. Not building this. " % repo

def _imageExists(repo):
    try:
        docker("history", [repo])
        return True
    except:        
        return False

def _deploy(installer, license, sp=None ):
    print "Copying dependencies into Dockerfile directory for image build (links don't work)..."
    _deployFile(installer, os.path.join("dockerfiles", "gwlatest", "APIGateway_Install.run"))
    if sp:
        print "Copying sp to same..."
        _deployFile(sp, os.path.join("dockerfiles", "gwlatest", "APIGateway_SP.tar.gz"))

    _deployFile(license,   os.path.join("dockerfiles", "gwlatest", "lic.lic"))

    destScripts = os.path.join("dockerfiles", "gwlatest", "scripts")
    if os.path.exists(destScripts):
        shutil.rmtree(destScripts)
    shutil.copytree(os.path.join("src", "compose", "src", "scripts"), destScripts)

def _deployFile(src, dest) :
    print "Copying: %s to %s" % (src, dest)
    if not os.path.exists(src):         
         sys.exit("\nThe source file: %s does not exist, exiting" % src);
    shutil.copy2(src, dest)

def _parseArgs() :
    parser = argparse.ArgumentParser(description='Build API Gateway static docker Images. Run this before running compose.py.')
    parser._action_groups.pop()
    required = parser.add_argument_group('required arguments')
    optional = parser.add_argument_group('optional arguments')
    required.add_argument("--installer", required=True, help="API Gateway installer. (APIGateway_Install.run)")    
    required.add_argument("--license",   required=True, help="API Gateway license. (license.lic)")
    optional.add_argument("--image",     required=False, default="gwlatest" , help="Name of API Gateway base image that this tool generates. (gwlatest)")
    optional.add_argument("--baseos",    required=False, default='centos', help="Base OS Image to build( Must be either 'centos' or 'redhat')")
    optional.add_argument("--sp",        required=False, help="API Gateway SP tar file. (APIGateway_SP.tar.gz)")
    optional.add_argument("--clean",     required=False, default=False, action="store_true", help="Set to True to remove all docker images created by this tool.")    
    args = parser.parse_args()    
    return (args)

if __name__ == "__main__":
    (args) = _parseArgs()

    global baseOs

    baseOs           = args.baseos
    gwBaseOs         = "gw" + baseOs
    cassandra        = "cassandra_%s" % baseOs 
    static_images    = [gwBaseOs, cassandra]
    gw_image         = args.image
    supported_os     = ["centos", "redhat"]

    if not args.baseos in supported_os :
        sys.exit("Base OS image (--baseos) supplied must be either 'centos' or 'redhat'")

    if ":" in gw_image:
        img_delimiter = gw_image.index(':')
        gw_latest =  gw_image[:img_delimiter] + '_' + baseOs + gw_image[img_delimiter:]
    else:
        gw_latest = gw_image + '_' + baseOs

    if args.clean:
        _clean(static_images)
        _clean([gw_latest])

    if args.sp is not None:
        _deploy(args.installer, args.license, args.sp)
    else:
        _deploy(args.installer, args.license)

    for image in static_images:
        _buildStatic(image, image)

    if args.sp is not None: 
        _buildSP(gw_latest, "gwlatest")
    else:
        _build(gw_latest, "gwlatest")
  

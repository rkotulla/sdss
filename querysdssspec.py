#!/usr/bin/env python

###############################################################
#                                                             #
# Copyright (c) 2016, Ralf Kotulla                            #
#                     kotulla@wisc.edu                        #
#                                                             #
###############################################################

import os, sys
import astropy
import astropy.units
import astropy.coordinates
import astropy.io.fits as fits

import astroquery
from astroquery.simbad import Simbad
import astroquery.sdss

import ephem
import time
import numpy

import subprocess
from optparse import OptionParser

# for parallel data downloads
import threading
import Queue
import traceback
import json

from querysdss import resolve_name_to_radec
from load_sdss_frame_from_web import *

def get_sdss_spectrum(objname, radius=5):

    safe_objname = objname.replace(" ", "_")
    #
    # Create objname directory
    #
    rawdir = "%s/raw/" % (safe_objname)
    print rawdir
    try:
        os.makedirs(safe_objname)
        os.makedirs(rawdir)
    except Exception as e:
        print e
        pass

    #
    # Resolve the object name using simbad
    #
    coord_fn = "%s/coord.txt" % (safe_objname)
    coords, ra_dec = resolve_name_to_radec(objname=objname, coord_fn=coord_fn)

    print("Using field-of-view of >= %.2f arcsec" % (radius))
    search_radius = astropy.coordinates.Angle(radius / 3600., unit=astropy.units.deg)
    try:
        xid = astroquery.sdss.SDSS.query_region(coords, radius=search_radius, spectro=True)
    except Exception as e:
        print "Problem querying SDSS source catalog:\n%s" % (str(e))
        return

    if (xid is None):
        print("No spectra found for target %s" % (objname))
        return

    # print(xid)
    # print "\n"*5
    # print numpy.array(xid)
    # print "\n"*5
    # print str(xid)
    # print "\n"*5
    # print str(xid).splitlines()#keepends=False)

    #
    # convert the first match to a json file we can use elsewhere
    #
    json_dict = {}
    for cn in xid.colnames:
        json_dict[cn] = xid[0][cn]
    print json_dict
    json_fn = "%s/sdss_spec.json" % (safe_objname)
    with open(json_fn, "w") as json_f:
        json.dump(json_dict, json_f)

    #numpy.savetxt("dummy.txt", numpy.array(xid))

    #
    # Now download the SDSS spectrum as FITS and as static image
    #
    sp = astroquery.sdss.SDSS.get_spectra(matches=xid[0:1])
    # print sp
    spec_fn = "%s/%s_sdssspec.fits" % (safe_objname, safe_objname)
    sp[0].writeto(spec_fn, clobber=True)

    #
    # Download static spec
    #
    # specobjid = xid[0]['specobjid']
    # spec_img_fn = "%s/sdss_spec.jpg" % (safe_objname)
    # spec_url = "http://skyserver.sdss.org/dr12/en/get/SpecById.ashx?id=%d" % (specobjid)
    # print spec_url
    # cmd = "wget -nv -O %s '%s'" % (spec_img_fn, spec_url)
    # os.system(cmd)
    # print cmd
    # x=download_file(spec_url)#, spec_img_fn)
    # print x

    #print(xid[0])
    #print(xid[0]['ra'])

    #
    # Go through each of the found matches nearby and create a list of
    # unique run/rerun/camcol/field combos
    #
    # combos = []
    # run_rerun_camcol = []
    # for i, obj in enumerate(xid):
    #     combo = (obj['run'], obj['rerun'], obj['camcol'], obj['field'])
    #     combos.append(combo)
    #     run_rerun_camcol.append((obj['run'], obj['rerun'], obj['camcol']))
    #
    # unique = set(combos)
    # print(unique)


if __name__ == "__main__":

    parser = OptionParser()
    parser.add_option("-r", "--radius", dest="radius",
                      help="Search radius / Field of view",
                      default=10., type=float)
    parser.add_option("-f", "--force", dest="force",
                      help="Force running, even if data already exists",
                      default=False, action='store_true')
    (options, cmdline_args) = parser.parse_args()

    if (os.path.isfile(cmdline_args[0])):
        # Read target names from file
        with open(cmdline_args[0], 'r') as listfile:
            objects = [l.strip() for l in listfile.readlines()]
    else:
        # Take one or more object names from command line
        objects = cmdline_args[0:]

    #
    # Now download all files, one after the other
    #
    print("Using %s for resampling" % (options.resample_dir))
    for objname in objects:
        if (os.path.isdir(objname) and not options.force):
            print "Object %s exists, skipping" % (objname)
            continue
        # try:
        print "running get_spectrum for",objname
        get_sdss_spectrum(objname=objname,
                  radius=options.radius,
                  # resample_dir=options.resample_dir,
                  # parallel=options.parallel
                          )
        # except (KeyboardInterrupt, SystemError, SystemExit):
        #     raise
        # except:
        #     error_fn = "%s.error" % (objname)
        #     etype, error, stackpos = sys.exc_info()
        #
        #     exception_string = ["\n",
        #                 "=========== EXCEPTION ==============",
        #                 "etype: %s" % (str(etype)),
        #                 "error: %s" % (str(error)),
        #                 "stackpos: %s" % (str(stackpos)),
        #                 "---\n",
        #                 traceback.format_exc(),
        #                 "--- end\n"
        #     ]
        #     with open(error_fn, "w") as err:
        #         err.writelines(exception_string)

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
import numpy

import ephem

import subprocess

if __name__ == "__main__":

    objname = sys.argv[1]
    list_fn = sys.argv[2]
    fields = numpy.loadtxt(list_fn, delimiter=',', dtype=numpy.int)

    #
    # Create objname directory
    #
    try:
        os.makedirs(objname)
    except:
        pass


    print fields

    # os._exit(0)

    ugriz_filenames = {}
    allfiles = []
    for pointing, sdss_locator in enumerate(fields):
        #print pointing

        (run, rerun, camcol, field) = list(sdss_locator)
        #print (run, rerun, camcol, field)
        #continue

        ugriz_hdus = {}
        for filtername in ['u', 'g', 'r', 'i', 'z']:
            print("Downloading %s-band of %s (run=%d,rerun=%d,camcol=%d,field=%d)" % (
                filtername, objname, run, rerun, camcol, field))

            hdus = astroquery.sdss.SDSS.get_images(run=run,
                                                   rerun=rerun,
                                                   camcol=camcol,
                                                   field=field,
                                                   band=filtername
                                                   )
            # print(type(hdus), hdus)
            if (not filtername in ugriz_filenames):
                ugriz_filenames[filtername] = []

            for i, rethdu in enumerate(hdus):
                del rethdu[1:]
                # print type(rethdu)
                out_fn = "%s/%s_%s.%d_%d.raw.fits" % (objname, objname, filtername, pointing, i)
                rethdu.writeto(out_fn, clobber=True)
                ugriz_filenames[filtername].append(out_fn)
                allfiles.append(out_fn)

            ugriz_hdus[filtername] = hdus[0]


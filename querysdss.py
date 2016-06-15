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

from load_sdss_frame_from_web import *

def stackfiles(imgout, weightout, inputlist, coverage_fn, resample_dir="./"):
    #
    # Open the coverage file, find center coordinates and image size
    # this then needs to be propagated to the stack and individual files below
    #
    coverage_hdu = fits.open(coverage_fn)


    swarp_cmd = """swarp
        -IMAGEOUT_NAME %(imgout)s
        -WEIGHTOUT_NAME %(weightout)s
        -WEIGHT_TYPE NONE
        -COMBINE Y
        -COMBINE_TYPE AVERAGE
        -RESAMPLE Y
        -SUBTRACT_BACK N
        -CENTER_TYPE MANUAL
        -CENTER %(ra)f,%(dec)f
        -IMAGE_SIZE %(sx)d,%(sy)d
        -RESAMPLE_DIR %(resamp)s
        %(files)s
        """ % {
        'imgout': imgout,
        'weightout': weightout,
        'files': " ".join(inputlist),
        'ra': coverage_hdu[0].header['CRVAL1'],
        'dec': coverage_hdu[0].header['CRVAL2'],
        'sx': coverage_hdu[0].header['NAXIS1'],
        'sy': coverage_hdu[0].header['NAXIS2'],
        'resamp': resample_dir,
    }
    print(" ".join(swarp_cmd.split()))
    # g = ugriz_hdus['g'][0].data
    # r = ugriz_hdus['r'][0].data
    # i = ugriz_hdus['i'][0].data
    # combined = g+r+i
    #
    #     gri_hdu = fits.HDUList(
    #         [fits.PrimaryHDU(header=ugriz_hdus['g'][0].header),
    #          fits.ImageHDU(header=ugriz_hdus['g'][0].header,
    #                         data=combined)])
    #     gri_hdu.writeto("%s_gri.%d.fits" % (objname,pointing), clobber=True)
    #
    ret = subprocess.Popen(swarp_cmd.split(),
                           stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE)
    (_stdout, _stderr) = ret.communicate()
    if (ret.returncode != 0):
        print("There was a problem creating %s" % (imgout))

    return True


if __name__ == "__main__":

    parser = OptionParser()
    parser.add_option("-r", "--radius", dest="radius",
                      help="Search radius / Field of view",
                      default=10., type=float)
    parser.add_option("", "--resamp", dest="resample_dir",
                      help="directory for swarp temporary files",
                        default="./", type=str)
    (options, cmdline_args) = parser.parse_args()

    objname = cmdline_args[0]

    #
    # Create objname directory
    #
    rawdir = "%s/raw/" % (objname)
    try:
        os.makedirs(objname)
        os.makedirs(rawdir)
    except:
        pass

    results = Simbad.query_object(objname)

    print(results[0][1])
    print(results[0][2])

    print type(results[0][1])

    e = ephem.Equatorial(str(results[0][1]), str(results[0][2]))
    print(e)
    print(e.ra, e.dec)




    coords = astropy.coordinates.SkyCoord(results[0][1], results[0][2], frame='icrs',
                                          unit=(astropy.units.hourangle, astropy.units.deg))
    print(coords)

    print("Using field-of-view of >= %.2f arcmin"  %(options.radius))
    search_radius = astropy.coordinates.Angle(options.radius/60, unit=astropy.units.deg)
    xid = astroquery.sdss.SDSS.query_region(coords, radius=search_radius)

    print(xid)

    print(xid[0])
    print(xid[0]['ra'])

    #
    # Go through each of the found matches nearby and create a list of
    # unique run/rerun/camcol/field combos
    #
    combos = []
    run_rerun_camcol = []
    for i,obj in enumerate(xid):
        combo = (obj['run'], obj['rerun'], obj['camcol'], obj['field'])
        combos.append(combo)
        run_rerun_camcol.append( (obj['run'], obj['rerun'], obj['camcol']) )

    unique = set(combos)
    print(unique)

    #
    # Make sure to get a complete list of fields to download, even in the case that some
    # fields for a given run/rerun/camcol are missing (e.g. in the case that the field list
    # includes fields 71 & 76, but not 72-75
    #
    fields = numpy.array(list(unique))
    exposures = []
    for run,rerun,camcol in set([tuple(f[:3]) for f in fields]):
        _this = (fields[:,0] == run) & (fields[:,1] == rerun) & (fields[:,2] == camcol)
        min_field = numpy.min(fields[:,3][_this])
        max_field = numpy.max(fields[:,3][_this])
        for _field in numpy.arange(min_field, max_field+1):
            exposures.append((run,rerun,camcol,_field))

    #
    # Now download the image
    #
    ugriz_filenames = {}
    allfiles = []
    n_retry_max = 5
    filters = ['u', 'g', 'r', 'i', 'z']

    current_frame = 0
    for pointing, (run,rerun,camcol,field) in enumerate(exposures):

        ugriz_hdus = {}
        for filtername in filters:
            current_frame += 1

            print("Downloading %s-band of %s (run=%d,rerun=%d,camcol=%d,field=%d), pointing %d/%d, file %d/%d" % (
                    filtername, objname, run, rerun, camcol, field,
                pointing+1, len(unique), current_frame, len(unique)*len(filters)))

            n_retries = 0
            while(n_retries < n_retry_max):
                try:
                    hdus = get_fits_from_sdss(run=run,
                                            rerun=rerun,
                                            camcol=camcol,
                                            field=field,
                                            band=filtername,
                                            ensure_single_imagehdu=True)

                    # hdus = astroquery.sdss.SDSS.get_images(run=run,
                    #                             rerun=rerun,
                    #                             camcol=camcol,
                    #                             field=field,
                    #                             band=filtername
                    #                             )
                    break
                except:
                    print("Encountered error, trying again after 1 second")
                    time.sleep(1)
                    n_retries += 1
                    continue
            if (n_retries >= n_retry_max):
                print("Unable to get this one, moving on :(")
                continue

            #print(type(hdus), hdus)
            if (not filtername in ugriz_filenames):
                ugriz_filenames[filtername] = []

            for i, rethdu in enumerate(hdus):
                #
                # Each output image has 4 extensions
                # (see https://data.sdss.org/datamodel/files/BOSS_PHOTOOBJ/frames/RERUN/RUN/CAMCOL/frame.html)
                # Primary: Image data, sky-subtracted and flux-calibrated (counts are nanomaggies)
                # Ext 1:   Image, 1-D, with flat-fielding data
                # Ext 2:   Table-HDU, data to re-interpolate the subtraced 2-D image
                # Ext 3:   Table-HDU, detailed astrometric data
                #
                #

                #
                # Now we have a nice FITS image, with a single ImageHDU containing all image data, and a
                # bunch of TableHDUs that are ignored when running swarp, but still contain all information.
                #
                out_fn = "%s/%s_%s.%d_%d.fits" % (rawdir, objname, filtername, pointing, i)
                rethdu.writeto(out_fn, clobber=True)
                ugriz_filenames[filtername].append(out_fn)
                allfiles.append(out_fn)

            ugriz_hdus[filtername] = hdus[0]

    #
    # Combine the gri bands for better S/N
    #
    print("combining g,r,i bands to improve S/N")

    #
    # First, stack all files available to get total area
    #
    coverage_fn = "%s/%s.sdss_coverage.fits" % (objname, objname)
    swarp_cmd = """swarp
        -IMAGEOUT_NAME %s
        -HEADER_ONLY Y
        %s""" % (coverage_fn, " ".join(allfiles))
    print(" ".join(swarp_cmd.split()))
    ret = subprocess.Popen(swarp_cmd.split(),
                           stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE)
    (_stdout, _stderr) = ret.communicate()
    if (ret.returncode != 0):
        print("There was a problem creating g/r/i image")

    #
    # Open the coverage file, find center coordinates and image size
    # this then needs to be propagated to the stack and individual files below
    #
    coverage_hdu = fits.open(coverage_fn)

    #
    # Now stack all g/r/i files, making sure to use the full grid as found via the coverage check above
    #
    allfiles = []
    for filtername in ['g', 'r', 'i']:
        allfiles += ugriz_filenames[filtername]

    raw_fn = "%s/%s_gri.fits" % (objname, objname)
    weight_fn = "%s/%s_gri.weight.fits" % (objname, objname)
    gri_fn = "%s/%s_gri.fits" % (objname, objname)

    stackfiles(imgout=raw_fn,
               weightout=weight_fn,
               inputlist=allfiles,
               coverage_fn=coverage_fn,
               resample_dir=options.resample_dir)

    #
    # Add file headers
    #


    #
    # Now compute de-projected frames for each of the filters
    #
    for filtername in filters:

        raw_fn = "%s/%s_%s.fits" % (objname, objname, filtername)
        weight_fn = "%s/%s_%s.weight.fits" % (objname, objname, filtername)
        gri_fn = "%s/%s_%s.fits" % (objname, objname, filtername)

        stackfiles(imgout=raw_fn,
                   weightout=weight_fn,
                   inputlist=ugriz_filenames[filtername],
                   coverage_fn=coverage_fn)

    #
    # Now open the resulting stack files, and
    # - re-insert headers from original input frames
    # - mask all bad pixels (having 0 weights) with NaNs
    #

    # print("Deleting file cache")
    # try:
    #     os.system("rm -rf /tmp/tmp*")
    # except:
    #     pass

    print("All done with %s" % (objname))
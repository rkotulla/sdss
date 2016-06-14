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

import subprocess

def stackfiles(imgout, weightout, inputlist, coverage_fn):
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
        %(files)s
        """ % {
        'imgout': imgout,
        'weightout': weightout,
        'files': " ".join(inputlist),
        'ra': coverage_hdu[0].header['CRVAL1'],
        'dec': coverage_hdu[0].header['CRVAL2'],
        'sx': coverage_hdu[0].header['NAXIS1'],
        'sy': coverage_hdu[0].header['NAXIS2'],

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

    objname = sys.argv[1]

    #
    # Create objname directory
    #
    try:
        os.makedirs(objname)
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


    search_radius = astropy.coordinates.Angle(10./60, unit=astropy.units.deg)
    xid = astroquery.sdss.SDSS.query_region(coords, radius=search_radius)

    print(xid)

    print(xid[0])
    print(xid[0]['ra'])

    #
    # Go through each of the found matches nearby and create a list of
    # unique run/rerun/camcol/field combos
    #
    combos = []
    for i,obj in enumerate(xid):
        combo = (obj['run'], obj['rerun'], obj['camcol'], obj['field'])
        combos.append(combo)

    unique = set(combos)
    print(unique)

    #
    # Now download the image
    #
    ugriz_filenames = {}
    allfiles = []
    n_retry_max = 5
    for pointing, (run,rerun,camcol,field) in enumerate(unique):

        ugriz_hdus = {}
        for filtername in ['u', 'g', 'r', 'i', 'z']:
            print("Downloading %s-band of %s (run=%d,rerun=%d,camcol=%d,field=%d)" % (
                    filtername, objname, run, rerun, camcol, field))

            n_retries = 0
            while(n_retries < n_retry_max):
                try:
                    hdus = astroquery.sdss.SDSS.get_images(run=run,
                                                rerun=rerun,
                                                camcol=camcol,
                                                field=field,
                                                band=filtername
                                                )
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
                del rethdu[1:]
                #print type(rethdu)
                out_fn = "%s/%s_%s.%d_%d.raw.fits" % (objname, objname, filtername, pointing, i)
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

    raw_fn = "%s/%s_gri.raw.fits" % (objname, objname)
    weight_fn = "%s/%s_gri.weight.fits" % (objname, objname)
    gri_fn = "%s/%s_gri.fits" % (objname, objname)

    stackfiles(imgout=raw_fn,
               weightout=weight_fn,
               inputlist=allfiles,
               coverage_fn=coverage_fn)

    #
    # Add file headers
    #


    #
    # Now compute de-projected frames for each of the filters
    #
    for filtername in ['g', 'r', 'i']:

        raw_fn = "%s/%s_%s.raw.fits" % (objname, objname, filtername)
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

    print("All done with %s" % (objname))
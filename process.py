#!/usr/bin/env python

###############################################################
#                                                             #
# Copyright (c) 2016, Ralf Kotulla                            #
#                     kotulla@wisc.edu                        #
#                                                             #
###############################################################

import pyfits, os, sys, numpy
import scipy, scipy.ndimage
import astLib.astWCS

from optparse import OptionParser

import warnings
with warnings.catch_warnings():
    warnings.filterwarnings("ignore",category=DeprecationWarning)
    warnings.filterwarnings("ignore",category=UserWarning)

    import astropy
    import astropy.units
    import astropy.coordinates
    import astropy.io.fits as fits

    import astroquery
    from astroquery.simbad import Simbad
    import astroquery.sdss

from astropy.utils.exceptions import AstropyWarning
warnings.simplefilter('ignore', category=AstropyWarning)

def create_cutout(hdulist, ra, dec, fov):

    for i, ext in enumerate(hdulist):
        data = ext.data
        if (type(data) != numpy.ndarray):
            continue
        if (data.ndim != 2):
            continue

        wcs = astWCS.WCS(ext.header, mode='pyfits')
        xy = wcs.sky2pix(ra, dec)

        print xy



if __name__ == "__main__":

    print sys.argv[1]
    objname = sys.argv[1]

    results = Simbad.query_object(objname)

    coords = astropy.coordinates.SkyCoord(results[0][1], results[0][2], frame='icrs',
                                          unit=(astropy.units.hourangle, astropy.units.deg))
    print(coords)
    print float(coords.ra)

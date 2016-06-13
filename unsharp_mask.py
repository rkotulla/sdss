#!/usr/bin/env python

###############################################################
#                                                             #
# Copyright (c) 2016, Ralf Kotulla                            #
#                     kotulla@wisc.edu                        #
#                                                             #
###############################################################

import pyfits, os, sys, numpy
import scipy, scipy.ndimage

from optparse import OptionParser

if __name__ == "__main__":

    parser = OptionParser()
    parser.add_option("-s", "--size", dest="size",
                      help="Median smoothing length",
                      default=21, type=int)
    (options, filenames) = parser.parse_args()

    print "Hello!"

    for infile in filenames: #sys.argv[1:]:

        hdulist = pyfits.open(infile)
        hdulist_median = pyfits.open(infile)

        # for now, assume it's a swarped file
        for i, ext in enumerate(hdulist):
            data = ext.data
            if (type(data) != numpy.ndarray):
                continue
            if (data.ndim != 2):
                continue

            print infile, ext.name, ext.data.shape

            # smoothed = scipy.ndimage.filters.gaussian_filter(
            #     input=data, 
            #     sigma=10, 
            #     order=0, output=None, mode='constant', cval=0.0
            #     )
            # leftover = data - smoothed

            median = scipy.ndimage.filters.median_filter(
                input=data.astype(numpy.float), 
                size=options.size, 
                output=None, mode='constant', cval=0.0
                )
            leftover = data - median

            for h in ['BSCALE', 'BZERO']:
                try:
                    if (h in ext.header): 
                        del ext.header[h]
                    if (h in hdulist_median[i].header):
                        del hdulist_median[i].header[h]
                except KeyError:
                    pass

            ext.data = leftover
            hdulist_median[i].data = median

        hdulist.writeto(infile[:-5]+".unsharped.fits", clobber=True)
        hdulist_median.writeto(infile[:-5]+".filtered.fits", clobber=True)



        

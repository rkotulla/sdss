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


def unsharp_mask(data, sizes=[5], mode='median'):

    smooth_list = [None] * len(sizes)
    filtered_list = [None] * len(sizes)
    for i_size, size in enumerate(sizes):
        print("computing %s, size %0.1f" % (mode, size))
        if (mode == 'median'):
            smoothed = scipy.ndimage.filters.median_filter(
                input=data.astype(numpy.float),
                size=int(numpy.round(size,0)),
                output=None, mode='constant', cval=0.0
                )
        elif (mode == 'gauss'):
            smoothed = scipy.ndimage.filters.gaussian_filter(
                input=data.astype(numpy.float),
                sigma=size, order=0, output=None, mode='reflect'
            )
        else:
            pass

        filtered = data - smoothed

        smooth_list[i_size] = smoothed
        filtered_list[i_size] = filtered

    return smooth_list, filtered_list



if __name__ == "__main__":

    parser = OptionParser()
    parser.add_option("-s", "--size", dest="size",
                      help="Median smoothing length",
                      default='21', type=str)
    parser.add_option("-m", "--mode", dest="mode",
                      help="mode (gauss/median)",
                      default="median", type=str)
    (options, filenames) = parser.parse_args()

    sizes = [float(d) for d in options.size.split(",")]
    for infile in filenames: #sys.argv[1:]:

        print "Working on %s" % (infile)

        hdulist = pyfits.open(infile)
        hdulist_median = pyfits.open(infile)

        # # for now, assume it's a swarped file
        # for i, ext in enumerate(hdulist):
        #     data = ext.data
        #     if (type(data) != numpy.ndarray):
        #         continue
        #     if (data.ndim != 2):
        #         continue
        #
        #     print infile, ext.name, ext.data.shape
        #
        #     # smoothed = scipy.ndimage.filters.gaussian_filter(
        #     #     input=data,
        #     #     sigma=10,
        #     #     order=0, output=None, mode='constant', cval=0.0
        #     #     )
        #     # leftover = data - smoothed
        #
        #     median = scipy.ndimage.filters.median_filter(
        #         input=data.astype(numpy.float),
        #         size=options.size,
        #         output=None, mode='constant', cval=0.0
        #         )
        #     leftover = data - median
        #
        #     for h in ['BSCALE', 'BZERO']:
        #         try:
        #             if (h in ext.header):
        #                 del ext.header[h]
        #             if (h in hdulist_median[i].header):
        #                 del hdulist_median[i].header[h]
        #         except KeyError:
        #             pass
        #
        #     ext.data = leftover
        #     hdulist_median[i].data = median
        #

        try:
            smoothed, filtered = unsharp_mask(data=hdulist[0].data, mode=options.mode, sizes=sizes)

            for i_size, size in enumerate(sizes):
                hdulist[0].data = smoothed[i_size]
                hdulist[0].header['UM_MODE'] = options.mode
                hdulist[0].header['UM_SIZE'] = size
                hdulist.writeto("%s.smooth.%s__%05.1f.fits" % (infile[:-5], options.mode, size), clobber=True)

                hdulist_median[0].data = filtered[i_size]
                hdulist_median[0].header['UM_MODE'] = options.mode
                hdulist_median[0].header['UM_SIZE'] = size
                hdulist_median.writeto("%s.filtered.%s_%05.1f.fits" % (infile[:-5], options.mode, size), clobber=True)
        except (KeyboardInterrupt, SystemError, SystemExit):
            raise
        except:
            print "There was a problem processing %s" % (infile)


        

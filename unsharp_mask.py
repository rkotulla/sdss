#!/usr/bin/env python3

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
import parallel_filter

def unsharp_mask(data, sizes=[5], mode='median', isize=-1):

    smooth_list = [None] * len(sizes)
    filtered_list = [None] * len(sizes)

    if (isize > 0):
        input_img = parallel_filter.parallel_filter(
            fct=scipy.ndimage.filters.gaussian_filter,
            data=data.astype(numpy.float),
            overlap=4*numpy.fabs(isize),
            sigma=numpy.fabs(isize),
            order=0, mode='reflect',
            truncate=4,
        )
    else:
        input_img = data

    for i_size, size in enumerate(sizes):
        print("computing %s, size %0.1f" % (mode, size))
        if (mode == 'median'):
            smoothed = scipy.ndimage.filters.median_filter(
                input=data.astype(numpy.float),
                size=int(numpy.round(size,0)),
                output=None, mode='constant', cval=0.0
                )

            filtered = input_img - smoothed


        elif (mode == 'gauss'):
            # smoothed = scipy.ndimage.filters.gaussian_filter(
            #     input=data.astype(numpy.float),
            #     sigma=size, order=0, output=None, mode='reflect'
            # )
            smoothed = parallel_filter.parallel_filter(
                fct=scipy.ndimage.filters.gaussian_filter,
                data=data.astype(numpy.float),
                overlap=4*size,

                sigma=size,
                order=0,
                mode='reflect',
                truncate=4,
            )

            filtered = input_img - smoothed

        elif (mode == "structuremap"):

            smoothed = parallel_filter.parallel_filter(
                fct=scipy.ndimage.filters.gaussian_filter,
                data=data.astype(numpy.float),
                overlap=4*size,

                sigma=size,
                order=0,
                mode='reflect',
                truncate=4,
            )

            filtered = input_img / smoothed
            filtered[~numpy.isfinite(filtered)] = 1.

        elif (mode == "structuremap2"):

            smoothed = parallel_filter.parallel_filter(
                fct=scipy.ndimage.filters.gaussian_filter,
                data=data.astype(numpy.float),
                overlap=4*size,

                sigma=size,
                order=0,
                mode='reflect',
                truncate=4,
            )

            pre_filtered = input_img / smoothed
            pre_filtered[~numpy.isfinite(pre_filtered)] = 1.

            filtered = parallel_filter.parallel_filter(
                fct=scipy.ndimage.filters.gaussian_filter,
                data=pre_filtered.astype(numpy.float),
                overlap=4*size,

                sigma=size,
                order=0,
                mode='reflect',
                truncate=4,
            )

            
        else:
            pass

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
    parser.add_option("-n", "--nosmooth", dest="smooth",
                      help="disable output of the smoothed files",
                      action="store_false", default=True)
    parser.add_option("-i", "--isize", dest="isize",
                      help="smoothing length for input",
                      default=-1., type=float)
    parser.add_option("-e", "--extname", dest="extname",
                      help="smoothing length for input",
                      default=0, type=str)
    (options, filenames) = parser.parse_args()

    sizes = [float(d) for d in options.size.split(",")]
    for infile in filenames: #sys.argv[1:]:

        print("Working on %s" % (infile))

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
            missing_sizes = []
            for size in sizes:

                out_fn = "%s.filtered.%s_%05.1f.fits" % (infile[:-5], options.mode, size)
                if (options.isize > 0):
                    out_fn = "%s.filtered.%s_%05.1f_s%.1f.fits" % (infile[:-5], options.mode, size, options.isize)

                #fn = "%s.filtered.%s_%05.1f.fits" % (infile[:-5], options.mode, size)
                if (not os.path.isfile(out_fn)):
                    missing_sizes.append(size)

            print(hdulist[options.extname].data.shape)
            smoothed, filtered = unsharp_mask(
                data=hdulist[options.extname].data,
                mode=options.mode,
                sizes=missing_sizes,
                isize=options.isize
            )

            # continue

            for i_size, size in enumerate(missing_sizes):
                if (options.smooth):
                    for ext in hdulist:
                        while('HISTORY' in ext.header):
                            del ext.header['HISTORY']
                    hdulist[options.extname].data = smoothed[i_size]
                    hdulist[options.extname].header['UM_MODE'] = options.mode
                    hdulist[options.extname].header['UM_SIZE'] = size
                    hdulist.writeto("%s.smooth.%s__%05.1f.fits" % (infile[:-5], options.mode, size), clobber=True)

                out_fn = "%s.filtered.%s_%05.1f.fits" % (infile[:-5], options.mode, size)
                if (options.isize > 0):
                    out_fn = "%s.filtered.%s_%05.1f_s%.1f.fits" % (infile[:-5], options.mode, size, options.isize)
                print("writing smoothed file to %s" % (out_fn))

                # Delete all history headers
                for ext in hdulist_median:
                    while('HISTORY' in ext.header):
                        del ext.header['HISTORY']

                hdulist_median[options.extname].data = filtered[i_size]
                hdulist_median[options.extname].header['UM_MODE'] = options.mode
                hdulist_median[options.extname].header['UM_SIZE'] = size
                hdulist_median.writeto(out_fn, clobber=True)
        except (KeyboardInterrupt, SystemError, SystemExit):
            raise
        except Exception as e:
            print("There was a problem processing %s\n%s" % (infile, str(e)))


        

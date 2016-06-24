#!/usr/bin/env python


import astropy.io.fits as fits
import numpy
import os, sys

from PIL import Image, ImageFont, ImageDraw
#import Image
from optparse import OptionParser

print Image.SAVE

if __name__ == "__main__":

    parser = OptionParser()
    parser.add_option("-w", "--weight", dest="weight_fn",
                      help="weight filename",
                      default="", type=str)
    (options, cmdline_args) = parser.parse_args()

    if (os.path.isfile(options.weight_fn)):
        weight_hdulist = fits.open(options.weight_fn)
        weight_map = weight_hdulist[0].data
    else:
        weight_map = 1

    print cmdline_args

    for fn in cmdline_args:
        #
        # Open input files
        #
        hdulist = fits.open(fn)
        data = hdulist[0].data

        #
        # Mask out all areas ouside the covered f.o.v.
        #
        data[weight_map <= 0] = numpy.NaN
        valid_data = data[weight_map > 0]

        good_data = weight_map > 0

        for iteration in range(3):

            qs = numpy.nanpercentile(data[good_data], q=[16,50,84])

            _median = qs[1]
            _sigma = (qs[2] - qs[0]) / 2.
            _mingood = _median - 3*_sigma
            _maxgood = _median + 3*_sigma
            good_data[ (data<_mingood) | (data>_maxgood)] = False

            print iteration, _median, _sigma, _mingood, _maxgood

        #
        # Good cuts are from -5sigma - 5*sigma
        #
        min_level = _median - 5*_sigma
        max_level = _median + 5*_sigma

        greyscale = (data - min_level) / (max_level - min_level)
        greyscale[greyscale < 0] = 0
        greyscale[greyscale >= 1] = 1

        output_fn = fn[:-5]+".png"
        print output_fn
        image = Image.fromarray(numpy.uint8(greyscale * 255))
        image = image.transpose(Image.FLIP_TOP_BOTTOM)
        image.save(output_fn, "PNG")
        del image



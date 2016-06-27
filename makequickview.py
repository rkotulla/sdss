#!/usr/bin/env python


import astropy.io.fits as fits
import astropy.wcs

import numpy
import os, sys

from PIL import Image, ImageFont, ImageDraw
#import Image
from optparse import OptionParser

from astropy import units as u
import astropy
import astropy.nddata

print Image.SAVE

def make_image(img_fn, weight_fn, output_fn, cutout=None, min_max=None):

    hdulist = fits.open(img_fn)
    data = hdulist[0].data

    if (os.path.isfile(weight_fn)):
        weight_hdulist = fits.open(weight_fn)
        weight_map = weight_hdulist[0].data
    else:
        weight_map = 1

    #
    # Mask out all areas ouside the covered f.o.v.
    #
    data[weight_map <= 0] = numpy.NaN
    valid_data = data[weight_map > 0]

    good_data = weight_map > 0

    ####
    if (not cutout == None):
        ra,dec,size = cutout
        wcs = astropy.wcs.WCS(header=hdulist[0].header)
        x,y = wcs.all_world2pix(ra,dec,0)
        print x,y
        # position = (49.7, 100.1)
        # size = (40, 50)  # pixels
        # cutout = astropy.nddata.Cutout2D(data, position, size)

        _x = int(x)
        _y = int(y)
        data = data[_y-500:_y+500, _x-500:_x+500]

    if (min_max == None):
        for iteration in range(3):
            qs = numpy.nanpercentile(data[good_data], q=[16, 50, 84])

            _median = qs[1]
            _sigma = (qs[2] - qs[0]) / 2.
            _mingood = _median - 3 * _sigma
            _maxgood = _median + 3 * _sigma
            good_data[(data < _mingood) | (data > _maxgood)] = False

            print iteration, _median, _sigma, _mingood, _maxgood

        #
        # Good cuts are from -5sigma - 5*sigma
        #
        min_level = _median - 5 * _sigma
        max_level = _median + 5 * _sigma
    else:
        min_level, max_level = min_max

    greyscale = (data - min_level) / (max_level - min_level)
    greyscale[greyscale < 0] = 0
    greyscale[greyscale >= 1] = 1

    print output_fn
    image = Image.fromarray(numpy.uint8(greyscale * 255))
    image = image.transpose(Image.FLIP_TOP_BOTTOM)
    image.save(output_fn, "PNG")
    del image

    return (min_level, max_level)

if __name__ == "__main__":

    parser = OptionParser()
    parser.add_option("-w", "--weight", dest="weight_fn",
                      help="weight filename",
                      default="", type=str)
    (options, cmdline_args) = parser.parse_args()

    print cmdline_args

    for fn in cmdline_args:


        output_fn = fn[:-5]+".png"
        make_image(fn, options.weight_fn, output_fn)

        # #
        # # Open input files
        # #
        # hdulist = fits.open(fn)
        # data = hdulist[0].data
        #
        # #
        # # Mask out all areas ouside the covered f.o.v.
        # #
        # data[weight_map <= 0] = numpy.NaN
        # valid_data = data[weight_map > 0]
        # 
        # good_data = weight_map > 0
        #
        # for iteration in range(3):
        #
        #     qs = numpy.nanpercentile(data[good_data], q=[16,50,84])
        #
        #     _median = qs[1]
        #     _sigma = (qs[2] - qs[0]) / 2.
        #     _mingood = _median - 3*_sigma
        #     _maxgood = _median + 3*_sigma
        #     good_data[ (data<_mingood) | (data>_maxgood)] = False
        #
        #     print iteration, _median, _sigma, _mingood, _maxgood
        #
        # #
        # # Good cuts are from -5sigma - 5*sigma
        # #
        # min_level = _median - 5*_sigma
        # max_level = _median + 5*_sigma
        #
        # greyscale = (data - min_level) / (max_level - min_level)
        # greyscale[greyscale < 0] = 0
        # greyscale[greyscale >= 1] = 1
        #
        # output_fn = fn[:-5]+".png"
        # print output_fn
        # image = Image.fromarray(numpy.uint8(greyscale * 255))
        # image = image.transpose(Image.FLIP_TOP_BOTTOM)
        # image.save(output_fn, "PNG")
        # del image
        #


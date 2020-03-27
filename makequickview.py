#!/usr/bin/env python


import astropy.io.fits as fits
import astropy.wcs
import math

import numpy
import os, sys

from PIL import Image, ImageFont, ImageDraw
#import Image
from optparse import OptionParser

from astropy import units as u
import astropy
import astropy.nddata

print Image.SAVE

def make_image(img_fn, weight_fn, output_fn, cutout=None, min_max=None, nsigma=[-5,+5], scale='linear'):

    hdulist = fits.open(img_fn)
    data = hdulist[0].data

    if (os.path.isfile(weight_fn)):
        weight_hdulist = fits.open(weight_fn)
        weight_map = weight_hdulist[0].data
    else:
        weight_map = numpy.ones_like(data)


    #
    # Mask out all areas ouside the covered f.o.v.
    #
    data[weight_map <= 0] = numpy.NaN
    valid_data = data[weight_map > 0]

    good_data = weight_map > 0

    ####
    if (not cutout == None):
        print "prepping cutout", cutout
        ra,dec,size,coord = cutout
        #print math.degrees(float(ra)), math.degrees(float(dec))
        #print hdulist[0].header
        wcs = astropy.wcs.WCS(header=hdulist[0].header)
        #print wcs
        ra,dec = math.degrees(float(ra)), math.degrees(float(dec))
        #ra,dec = coord
        x,y = wcs.all_world2pix(ra,dec,0)
        print ra, dec, "-->", x,y
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
        print nsigma
        min_level = _median + nsigma[0] * _sigma
        max_level = _median + nsigma[1] * _sigma
    else:
        min_level, max_level = min_max

    print min_level, max_level
    greyscale = (data - min_level) / (max_level - min_level)

    if (scale == "arcsinh"):
        print "Applying arcsinh contrast adjustment"
        #greyscale = greyscale / 10.
        numpy.arcsinh(greyscale,out=greyscale) / numpy.arcsinh(1.)
        #greyscale = numpy.log10(greyscale)  # / numpy.arcsinh(1.)


    greyscale[greyscale < 0.] = 0.
    greyscale[greyscale >= 1.] = 1.


    print output_fn
    image = Image.fromarray(numpy.uint8(greyscale * 255))
    image = image.transpose(Image.FLIP_TOP_BOTTOM)
    image.save(output_fn, "JPEG")
    del image

    return (min_level, max_level)

if __name__ == "__main__":

    parser = OptionParser()
    parser.add_option("-w", "--weight", dest="weight_fn",
                      help="weight filename",
                      default="", type=str)
    parser.add_option("-s", "--scale", dest="scale",
                      help="scaling [linear|arcsinh]",
                      default="linear", type=str)
    parser.add_option("-x", "--max", dest="max",
                      help="scaling [linear|arcsinh]",
                      default=5, type=float)
    parser.add_option("-n", "--min", dest="min",
                      help="scaling [linear|arcsinh]",
                      default=-2, type=float)
    (options, cmdline_args) = parser.parse_args()

    print cmdline_args

    for fn in cmdline_args:


        output_fn = fn[:-5]+".png"
        if (os.path.isfile(output_fn)):
            continue

        make_image(fn, options.weight_fn, output_fn, nsigma=[options.min, options.max],
                   scale=options.scale)

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


#!/usr/bin/env python

import os, sys, numpy
import glob

import makequickview
import querysdss
import astropy
import astropy.io.fits as fits

if __name__ == "__main__":

    objname = sys.argv[1]

    # get ra/dec from name
    #_, (ra, dec) = querysdss.resolve_name_to_radec(objname)
    #print ra, dec
    ra,dec = 148.97195, 69.68075
    coord = astropy.coordinates.SkyCoord(ra, dec, frame='icrs',
                                          unit=(astropy.units.hourangle, astropy.units.deg))


    print ra, dec

    fn_template = "%s/%s_gri.filtered.*.fits" % (objname, objname)
    print fn_template

    fns = glob.glob(fn_template)
    weight_fn = glob.glob("%s/%s_gri.weight.fits" % (objname, objname))[0]

    print fns

    index_fn = "%s/index.html" % (objname)

    with open(index_fn, "w") as index_file:
        print >>index_file, "<html><body>"

        for fn in fns:
            hdulist = fits.open(fn)
            um_mode = hdulist[0].header["UM_MODE"]
            um_size = hdulist[0].header["UM_SIZE"]
            outfile = fn[:-5]+".png"
            crop_outfile = fn[:-5]+".crop.png"
            _, bn = os.path.split(outfile)
            _, cropbn = os.path.split(crop_outfile)
            if (not os.path.isfile(outfile)):
                min_max = makequickview.make_image(fn, weight_fn, outfile)
                makequickview.make_image(fn, weight_fn=weight_fn, output_fn=crop_outfile,
                                         cutout=(ra,dec,5), min_max=min_max)

            print >>index_file, """
            <p>%(o)s - %(m)s @ %(s).1f pixels<br>
            full frame: <a href='%(ff)s'>%(ff)s</a><br>
            <a href='%(cf)s'><img src='%(cf)s' style='width:500;'</img></a></p>
            """ % {
                'cf': cropbn,
                'ff': bn,
                'o': objname,
                'm': um_mode,
                's': um_size,
            }
        print >>index_file, "</body></html>"
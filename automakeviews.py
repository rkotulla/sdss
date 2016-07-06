#!/usr/bin/env python

import os, sys, numpy
import glob

import makequickview
import querysdss
import astropy
import astropy.io.fits as fits


def create_quick_view(objname):

    # get ra/dec from name
    _, (ra, dec) = querysdss.resolve_name_to_radec(objname)
    print ra, dec
    #ra,dec = 148.97195, 69.68075
    coord = astropy.coordinates.SkyCoord(ra, dec, frame='icrs',
                                          unit=(astropy.units.hourangle, astropy.units.deg))

    print coord, ra, dec

    weight_fn = glob.glob("%s/%s_gri.weight.fits" % (objname, objname))[0]
    gri = "%s/%s_gri.fits" % (objname, objname)

    #print fns

    index_fn = "%s/index.html" % (objname)

    with open(index_fn, "w") as index_file:
        print >>index_file, """
        <html>
        <head>
           <link rel="stylesheet" type="text/css" href="../reu_sdss.css">
           <base target="_blank">
        </head>
        <body>"""

        print >>index_file, """
        <h1>%(objname)s</h1>
        <p><ul>
            <li><a href="https://ned.ipac.caltech.edu/cgi-bin/objsearch?objname=%(objname)s&extend=no&hconst=73&omegam=0.27&omegav=0.73&corr_z=1&out_csys=Equatorial&out_equinox=J2000.0&obj_sort=RA+or+Longitude&of=pre_text&zv_breaker=30000.0&list_limit=5&img_stamp=YES">NED page</a></li>
            <li><a href="https://ned.ipac.caltech.edu/cgi-bin/NEDatt?objname=%(objname)s">NED classifications</a></li>
            <li><a href="https://ned.ipac.caltech.edu/cgi-bin/imgdata?objname=%(objname)s&hconst=73.0&omegam=0.27&omegav=0.73&corr_z=1">NED images</a></li>
            <!--<li><a href="https://ned.ipac.caltech.edu/cgi-bin/datasearch?search_type=Photo_id&objid=58481&objname=%(objname)s&img_stamp=YES&hconst=73.0&omegam=0.27&omegav=0.73&corr_z=1&of=table">NED Spectral Energy Distributions</a></li>-->
            <li><a href="http://simbad.u-strasbg.fr/simbad/sim-id?Ident=%(objname)s&NbIdent=1&Radius=2&Radius.unit=arcmin&submit=submit+id">SIMBad Identifier query</a></li>
            </ul>
            </p>""" % {
            'objname': objname.replace(" ","+"),
        }

        #
        # Add the GRI stack
        #
        fn = "%s/%s_gri.fits" % (objname, objname)
        outfile = fn[:-5] + ".jpg"
        crop_outfile = fn[:-5] + ".crop.jpg"
        _, bn = os.path.split(outfile)
        _, cropbn = os.path.split(crop_outfile)
        if (not os.path.isfile(outfile)):
            min_max = makequickview.make_image(fn, weight_fn, outfile, nsigma=[-15,+100],
                                     scale='arcsinh')
            makequickview.make_image(fn, weight_fn=weight_fn, output_fn=crop_outfile,
                                     cutout=(ra, dec, 5, coord), min_max=min_max,
                                     scale='arcsinh')
        print >>index_file, """
            <div class="filtered">
            <h2>%(o)s - gri stack</h2>
            <p>full frame: <a href='%(ff)s'>%(ff)s</a><br>
            <a href='%(cf)s'><img src='%(cf)s' style='width:500;'</img></a>
            </p>
            </div><hr>
            """ % {
                'cf': cropbn,
                'ff': bn,
                'o': objname,
            }

        #
        # Add the g/r/i image as 3-color image
        #

        #
        # Now add all unsharp-masked frames
        #
        for mode in ['gauss', 'median']:
            fn_template = "%s/%s_gri.filtered.%s_*.fits" % (objname, objname, mode)
            print fn_template

            fns = glob.glob(fn_template)
            um_sizes = numpy.zeros((len(fns)))

            for i_fn, fn in enumerate(fns):
                hdulist = fits.open(fn)
                um_size = -1 if not "UM_SIZE" in hdulist[0].header else hdulist[0].header["UM_SIZE"]
                um_sizes[i_fn] = um_size
            si = numpy.argsort(um_sizes)
            fns_sorted = numpy.array(fns)[si]
            print fns
            for i_fn, fn in enumerate(fns_sorted):
                hdulist = fits.open(fn)

                nsigma = [-5, +5]
                um_mode = hdulist[0].header["UM_MODE"] if "UM_MODE" in hdulist[0].header else "???"
                um_size = hdulist[0].header["UM_SIZE"] if "UM_SIZE" in hdulist[0].header else -1.
                um_sizes[i_fn] = um_size
                outfile = fn[:-5]+".jpg"
                crop_outfile = fn[:-5]+".crop.jpg"
                _, bn = os.path.split(outfile)
                _, cropbn = os.path.split(crop_outfile)

                if (not os.path.isfile(outfile)):
                    min_max = makequickview.make_image(fn, weight_fn, outfile, nsigma=nsigma)
                    makequickview.make_image(fn, weight_fn=weight_fn, output_fn=crop_outfile,
                                             cutout=(ra,dec,5,coord), min_max=min_max)

                print >>index_file, """
                <div class="filtered"><h2>%(o)s - %(m)s @ %(s).1f pixels</h2>
                <p>full frame: <a href='%(ff)s'>%(ff)s</a><br>
                <a href='%(cf)s'><img src='%(cf)s' style='width:500;'</img></a></p></div>
                """ % {
                    'cf': cropbn,
                    'ff': bn,
                    'o': objname,
                    'm': um_mode,
                    's': um_size,
                }
        print >>index_file, "</body></html>"



if __name__ == "__main__":


    if (os.path.isfile(sys.argv[1])):
        with open(sys.argv[1], "r") as f:
            objects = [l.split()[0] for l in f.readlines()]
        for objname in objects:
            create_quick_view(objname)
    else:
        objname = sys.argv[1]
        create_quick_view(objname)
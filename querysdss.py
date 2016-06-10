#!/usr/bin/env python



import os, sys
import astropy
import astropy.units
import astropy.coordinates
import astropy.io.fits as fits

import astroquery
from astroquery.simbad import Simbad
import astroquery.sdss

import ephem

if __name__ == "__main__":

    objname = sys.argv[1]


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


    search_radius = astropy.coordinates.Angle(1./60, unit=astropy.units.deg)
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
    for (run,rerun,camcol,field) in unique:

        for filtername in ['u', 'g', 'r', 'i', 'z']:

            hdus = astroquery.sdss.SDSS.get_images(run=run,
                                            rerun=rerun,
                                            camcol=camcol,
                                            field=field,
                                            band=filtername
                                            )
            print(type(hdus), hdus)

            for i, rethdu in enumerate(hdus):
                print type(rethdu)
                rethdu.writeto("%s_%s.%d.fits" % (objname, filtername, i), clobber=True)

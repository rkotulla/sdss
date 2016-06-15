#!/usr/bin/env python

import astropy.io.fits as fits
import urllib2
import tempfile
import bz2

def get_fits_from_sdss(run, rerun=301, camcol=1, field=1, filter='g'):
    url = "http://dr12.sdss3.org/sas/dr12/boss/photoObj/frames/%(rerun)3d/%(run)d/%(camcol)d/frame-%(filter)1s-%(run)06d-%(camcol)d-%(field)04d.fits.bz2" % {
        'run': run,
        'rerun': rerun,
        'camcol': camcol,
        'field': field,
        'filter': filter,
    }
    print url
    return openfitsfromweb(url)

def openfitsfromweb(url):

    # open the response
    response = urllib2.urlopen(url)

    #
    # Make sure the server reports the response as OK (HTTP code 200)
    #
    if (response.getcode() != 200):
        return None

    #
    # Prepare a tmp file to hold the data so we can open it using pyfits
    #
    tmpfile = tempfile.TemporaryFile(mode='w+b', suffix='.fits.bz2', prefix='sdss_tmp_')

    #
    # Read the data from the server, uncompress it using the bz2 algorithm, and write data to
    # tmp-file. Make sure to set read pointer to beginning of file
    #
    try:
        data = response.read()
        rawdata = bz2.decompress(data)
        tmpfile.write(rawdata)
    except:
        return None
    tmpfile.seek(0)

    # with open("/tmp/myfile.fits.bz2", 'wb') as f:
    #     f.write(data)
    # with open("/tmp/myfile.fits", 'wb') as f:
    #     f.write(rawdata)

    hdu = fits.open(tmpfile, mode='denywrite')
    return hdu


if __name__ == "__main__":

    # url = "http://dr12.sdss3.org/sas/dr12/boss/photoObj/frames/301/4294/5/frame-g-004294-5-0229.fits.bz2"
    # hdu = openfitsfromweb(url)

    hdu = get_fits_from_sdss(run=4294, rerun=301, camcol=5, field=229, filter='g')
    hdu.info()

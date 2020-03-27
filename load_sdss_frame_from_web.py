#!/usr/bin/env python

import astropy.io.fits as fits
import urllib2
import tempfile
import bz2
import logging


def convert_flatfield_to_tablehdu(hdu):
    #
    # Each output image has 4 extensions
    # (see https://data.sdss.org/datamodel/files/BOSS_PHOTOOBJ/frames/RERUN/RUN/CAMCOL/frame.html)
    # Primary: Image data, sky-subtracted and flux-calibrated (counts are nanomaggies)
    # Ext 1:   Image, 1-D, with flat-fielding data
    # Ext 2:   Table-HDU, data to re-interpolate the subtraced 2-D image
    # Ext 3:   Table-HDU, detailed astrometric data
    #
    #

    # Ext 1 is a problem here, because swarp (see below) treats it as an image and then
    # fails to handle it properly. Solution: Convert the ImageHDU to a TableHDU
    #
    columns = [fits.Column(name="RESPONSE", format='D', unit='cts/nmgy',
                           array=hdu[1].data[:])]
    coldefs = fits.ColDefs(columns)
    flat_tbhdu = fits.BinTableHDU.from_columns(coldefs)
    hdu[1] = flat_tbhdu

    return hdu


def get_fits_from_sdss(run, rerun=301, camcol=1, field=1, band='g', ensure_single_imagehdu=False, rawfile=None):
    logger = logging.getLogger('GetFitsFromSDSS')

    url = "http://dr12.sdss3.org/sas/dr12/boss/photoObj/frames/%(rerun)3d/%(run)d/%(camcol)d/frame-%(filter)1s-%(run)06d-%(camcol)d-%(field)04d.fits.bz2" % {
        'run': run,
        'rerun': rerun,
        'camcol': camcol,
        'field': field,
        'filter': band,
    }
    logger.debug("SDSS image source: %s" % (url))
    hdu = openfitsfromweb(url, rawfile)

    hdu[0].header['Q_RUN'] = (run, "run")
    hdu[0].header['Q_RERUN'] = (rerun, "rerun")
    hdu[0].header['Q_CAMCOL'] = (camcol, "camcol")
    hdu[0].header['Q_FIELD'] = (field, "field")
    hdu[0].header['Q_URL'] = (url, "download url")

    if (ensure_single_imagehdu):
        convert_flatfield_to_tablehdu(hdu)

    return hdu

def download_file(url, target_fn=None):

    logger = logging.getLogger("Downloader")

    # open the response
    print("Querying %s" % (url))
    response = urllib2.urlopen(url)

    #
    # Make sure the server reports the response as OK (HTTP code 200)
    #
    print("Server responded: %d" % (response.getcode()))
    if (response.getcode() != 200):
        return None

    data = response.read()

    if (target_fn is not None):
        with open(target_fn, "w") as tf:
            tf.write(data)
            return len(data)
    else:
        return data



def openfitsfromweb(url, rawfile=None):

    logger = logging.getLogger("DownloadFitsFromWeb")

    # open the response
    print(url)
    logger.debug("Querying %s" % (url))
    response = urllib2.urlopen(url)

    #
    # Make sure the server reports the response as OK (HTTP code 200)
    #
    logger.debug("Server responded: %d" % (response.getcode()))
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

    #if (not rawfile == None):
    #    with open(rawfile, "wb") as rf:
    #        rf.write(data)

    # with open("/tmp/myfile.fits.bz2", 'wb') as f:
    #     f.write(data)
    # with open("/tmp/myfile.fits", 'wb') as f:
    #     f.write(rawdata)

    hdu = fits.open(tmpfile, mode='denywrite')
    return hdu


if __name__ == "__main__":

    # url = "http://dr12.sdss3.org/sas/dr12/boss/photoObj/frames/301/4294/5/frame-g-004294-5-0229.fits.bz2"
    # hdu = openfitsfromweb(url)

    hdu = get_fits_from_sdss(run=4294, rerun=301, camcol=5, field=229, band='g')
    hdu.info()

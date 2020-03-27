#!/usr/bin/env python

###############################################################
#                                                             #
# Copyright (c) 2016, Ralf Kotulla                            #
#                     kotulla@wisc.edu                        #
#                                                             #
###############################################################

import os, sys
import astropy
import astropy.units
import astropy.coordinates
import astropy.io.fits as fits

import astroquery
from astroquery.simbad import Simbad
import astroquery.sdss

import ephem
import time
import numpy

import subprocess
from optparse import OptionParser

# for parallel data downloads
import threading
import Queue
import traceback

from load_sdss_frame_from_web import *

def stackfiles(imgout, weightout, inputlist, coverage_fn, resample_dir="./"):
    #
    # Open the coverage file, find center coordinates and image size
    # this then needs to be propagated to the stack and individual files below
    #
    coverage_hdu = fits.open(coverage_fn)


    swarp_cmd = """swarp
        -IMAGEOUT_NAME %(imgout)s
        -WEIGHTOUT_NAME %(weightout)s
        -WEIGHT_TYPE NONE
        -COMBINE Y
        -COMBINE_TYPE AVERAGE
        -RESAMPLE Y
        -SUBTRACT_BACK N
        -CENTER_TYPE MANUAL
        -CENTER %(ra)f,%(dec)f
        -IMAGE_SIZE %(sx)d,%(sy)d
        -RESAMPLE_DIR %(resamp)s
        %(files)s
        """ % {
        'imgout': imgout,
        'weightout': weightout,
        'files': " ".join(inputlist),
        'ra': coverage_hdu[0].header['CRVAL1'],
        'dec': coverage_hdu[0].header['CRVAL2'],
        'sx': coverage_hdu[0].header['NAXIS1'],
        'sy': coverage_hdu[0].header['NAXIS2'],
        'resamp': resample_dir,
    }
    print(" ".join(swarp_cmd.split()))
    # g = ugriz_hdus['g'][0].data
    # r = ugriz_hdus['r'][0].data
    # i = ugriz_hdus['i'][0].data
    # combined = g+r+i
    #
    #     gri_hdu = fits.HDUList(
    #         [fits.PrimaryHDU(header=ugriz_hdus['g'][0].header),
    #          fits.ImageHDU(header=ugriz_hdus['g'][0].header,
    #                         data=combined)])
    #     gri_hdu.writeto("%s_gri.%d.fits" % (objname,pointing), clobber=True)
    #
    ret = subprocess.Popen(swarp_cmd.split(),
                           stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE)
    (_stdout, _stderr) = ret.communicate()
    if (ret.returncode != 0):
        print("There was a problem creating %s" % (imgout))

    return True


class SDSS_Downloader(threading.Thread):

    def __init__(self, queue, rawdir, ugriz_filenames={}, allfiles=[], n_retry_max=5):
        self.queue = queue
        self.n_retry_max=n_retry_max
        self.ugriz_filenames = ugriz_filenames
        self.allfiles = allfiles
        self.rawdir = rawdir
        self.done = False
        threading.Thread.__init__(self)

    def run(self):

        while (True):
            try:
                job = self.queue.get_nowait()
            except Queue.Empty:
                # nothing left to do
                break

            (run,rerun,camcol,field,filtername,pointing,ensure_single) = job
            #print job
            #continue

            print("Downloading pointing %d, filter %s (run=%d,rerun=%d,camcol=%d,field=%d)" % (
                pointing, filtername, run, rerun, camcol, field))

            n_retries = 0
            while(n_retries < self.n_retry_max or n_retries==0):
                try:
                    rethdu = get_fits_from_sdss(run=run,
                                              rerun=rerun,
                                              camcol=camcol,
                                              field=field,
                                              band=filtername,
                                              ensure_single_imagehdu=True)

                    # hdus = astroquery.sdss.SDSS.get_images(run=run,
                    #                             rerun=rerun,
                    #                             camcol=camcol,
                    #                             field=field,
                    #                             band=filtername
                    #                             )
                    break
                except Exception as e:
                    print("Encountered error, trying again after 1 second:\n%s" % (e))
                    time.sleep(1)
                    n_retries += 1
                    continue
            if (n_retries >= self.n_retry_max):
                print("Unable to get this one, moving on :(")
                continue

            # print(type(hdus), hdus)
            if (not filtername in self.ugriz_filenames):
                self.ugriz_filenames[filtername] = []

            #
            # Now we have a nice FITS image, with a single ImageHDU containing all image data, and a
            # bunch of TableHDUs that are ignored when running swarp, but still contain all information.
            #
            out_fn = "%s/%s_%s.%03d.fits" % (self.rawdir, objname, filtername, pointing)
            rethdu.writeto(out_fn, clobber=True)
            self.ugriz_filenames[filtername].append(out_fn)
            self.allfiles.append(out_fn)

        self.done = True
        print("download worker shutting down")

    def wait(self):
        while (not self.done):
            time.sleep(0.1)
        return


def resolve_name_to_radec(objname, coord_fn=None):

    if (not coord_fn == None and os.path.isfile(coord_fn)):
        print "loading coordinates from file"
        with open(coord_fn, "r") as cf:
            line = cf.readline()
            items = line.split()
            _ra = items[0]
            _dec = items[1]
    else:
        try:
            print "querying Simbad"
            results = Simbad.query_object(objname)
        except:
            return None, (-1,-1)

        if (results == None):
            return None, (-1,-1)

        print(results[0][1])
        print(results[0][2])

        print type(results[0][1])

        _ra  = results[0][1].replace(" ", ":")
        _dec = results[0][2].replace(" ", ":")

    e = ephem.Equatorial(str(_ra), str(_dec))
    print(e)
    print(e.ra, e.dec)

    #
    # Save the coordinates
    #
    if (not coord_fn == None and not os.path.isfile(coord_fn)):
        with open(coord_fn, "w") as cf:
            print >> cf, _ra, _dec, numpy.degrees(e.ra), numpy.degrees(e.dec)

    coords = astropy.coordinates.SkyCoord(_ra, _dec, frame='icrs',
                                          unit=(astropy.units.hourangle, astropy.units.deg))
    print(coords)

    return coords, (e.ra, e.dec)

def query_sdss_object(objname, radius=10., resample_dir="./", parallel=False):

    #
    # Create objname directory
    #
    rawdir = "%s/raw/" % (objname)
    try:
        os.makedirs(objname)
        os.makedirs(rawdir)
    except:
        pass

    #
    # Resolve the object name using simbad
    #
    if (objname.startswith("pos:")):
        items = objname.split(":")[1:3]
        _ra = float(items[0])
        _dec = float(items[1])
        print "Using user-defined coordiantes: %f %f" % (_ra, _dec)
        coords = astropy.coordinates.SkyCoord(_ra, _dec, frame='icrs',
                                          unit=(astropy.units.deg, astropy.units.deg))
    else:
        coord_fn = "%s/coord.txt" % (objname)
        coords, ra_dec = resolve_name_to_radec(objname=objname, coord_fn=coord_fn)


    print("Using field-of-view of >= %.2f arcmin"  %(radius))
    search_radius = astropy.coordinates.Angle(radius/60, unit=astropy.units.deg)
    try:
        xid = astroquery.sdss.SDSS.query_region(coords, radius=search_radius)
    except Exception as e:
        print "Problem querying SDSS source catalog:\n%s" % (str(e))
        return

    print(xid)

    print(xid[0])
    print(xid[0]['ra'])

    #
    # Go through each of the found matches nearby and create a list of
    # unique run/rerun/camcol/field combos
    #
    combos = []
    run_rerun_camcol = []
    for i,obj in enumerate(xid):
        combo = (obj['run'], obj['rerun'], obj['camcol'], obj['field'])
        combos.append(combo)
        run_rerun_camcol.append( (obj['run'], obj['rerun'], obj['camcol']) )

    unique = set(combos)
    print(unique)

    #
    # Make sure to get a complete list of fields to download, even in the case that some
    # fields for a given run/rerun/camcol are missing (e.g. in the case that the field list
    # includes fields 71 & 76, but not 72-75
    #
    fields = numpy.array(list(unique))
    exposures = []
    for run,rerun,camcol in set([tuple(f[:3]) for f in fields]):
        _this = (fields[:,0] == run) & (fields[:,1] == rerun) & (fields[:,2] == camcol)
        min_field = numpy.min(fields[:,3][_this])
        max_field = numpy.max(fields[:,3][_this])
        for _field in numpy.arange(min_field, max_field+1):
            exposures.append((run,rerun,camcol,_field))

    #
    # Now download the image
    #
    ugriz_filenames = {}
    allfiles = []
    n_retry_max = 5
    filters = ['u', 'g', 'r', 'i', 'z']

    # Setup a download queue that we can work done in parallel
    download_queue = Queue.Queue()

    current_frame = 0
    for pointing, (run,rerun,camcol,field) in enumerate(exposures):

        ugriz_hdus = {}
        for filtername in filters:
            current_frame += 1

            if (not parallel):
                print("Downloading %s-band of %s (run=%d,rerun=%d,camcol=%d,field=%d), pointing %d/%d, file %d/%d" % (
                        filtername, objname, run, rerun, camcol, field,
                    pointing+1, len(exposures), current_frame, len(exposures)*len(filters)))

                n_retries = 0
                while(n_retries < n_retry_max):
                    try:
                        hdus = get_fits_from_sdss(run=run,
                                                rerun=rerun,
                                                camcol=camcol,
                                                field=field,
                                                band=filtername,
                                                ensure_single_imagehdu=True)

                        # hdus = astroquery.sdss.SDSS.get_images(run=run,
                        #                             rerun=rerun,
                        #                             camcol=camcol,
                        #                             field=field,
                        #                             band=filtername
                        #                             )
                        break
                    except:
                        print("Encountered error, trying again after 1 second")
                        time.sleep(1)
                        n_retries += 1
                        continue
                if (n_retries >= n_retry_max):
                    print("Unable to get this one, moving on :(")
                    continue

                #print(type(hdus), hdus)
                if (not filtername in ugriz_filenames):
                    ugriz_filenames[filtername] = []

                for i, rethdu in enumerate(hdus):
                    #
                    # Each output image has 4 extensions
                    # (see https://data.sdss.org/datamodel/files/BOSS_PHOTOOBJ/frames/RERUN/RUN/CAMCOL/frame.html)
                    # Primary: Image data, sky-subtracted and flux-calibrated (counts are nanomaggies)
                    # Ext 1:   Image, 1-D, with flat-fielding data
                    # Ext 2:   Table-HDU, data to re-interpolate the subtraced 2-D image
                    # Ext 3:   Table-HDU, detailed astrometric data
                    #
                    #

                    #
                    # Now we have a nice FITS image, with a single ImageHDU containing all image data, and a
                    # bunch of TableHDUs that are ignored when running swarp, but still contain all information.
                    #
                    out_fn = "%s/%s_%s.%d_%d.fits" % (rawdir, objname, filtername, pointing, i)
                    rethdu.writeto(out_fn, clobber=True)
                    ugriz_filenames[filtername].append(out_fn)
                    allfiles.append(out_fn)

                ugriz_hdus[filtername] = hdus[0]

            else:
                # This is what we do to download frames in parallel
                download_queue.put((run,rerun,camcol,field,filtername,pointing,True))

    if (parallel):
        # For parallel processing, start the worker threads
        downloaders = []
        for n_threads in range(2):
            t = SDSS_Downloader(queue=download_queue,
                                rawdir=rawdir,
                                ugriz_filenames=ugriz_filenames,
                                allfiles=allfiles)
            t.daemon=True
            t.start()
            downloaders.append(t)
        # Now all workers are busy
        for t in downloaders:
            t.wait()
        # Now all workers are done with their work

    #
    # Combine the gri bands for better S/N
    #
    print("combining g,r,i bands to improve S/N")

    #
    # First, stack all files available to get total area
    #
    coverage_fn = "%s/%s.sdss_coverage.fits" % (objname, objname)
    swarp_cmd = """swarp
        -IMAGEOUT_NAME %s
        -HEADER_ONLY Y
        %s""" % (coverage_fn, " ".join(allfiles))
    print(" ".join(swarp_cmd.split()))
    ret = subprocess.Popen(swarp_cmd.split(),
                           stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE)
    (_stdout, _stderr) = ret.communicate()
    if (ret.returncode != 0):
        print("There was a problem creating g/r/i image")

    #
    # Open the coverage file, find center coordinates and image size
    # this then needs to be propagated to the stack and individual files below
    #
    coverage_hdu = fits.open(coverage_fn)

    #
    # Now stack all g/r/i files, making sure to use the full grid as found via the coverage check above
    #
    allfiles = []
    for filtername in ['g', 'r', 'i']:
        allfiles += ugriz_filenames[filtername]

    raw_fn = "%s/%s_gri.fits" % (objname, objname)
    weight_fn = "%s/%s_gri.weight.fits" % (objname, objname)
    gri_fn = "%s/%s_gri.fits" % (objname, objname)

    stackfiles(imgout=raw_fn,
               weightout=weight_fn,
               inputlist=allfiles,
               coverage_fn=coverage_fn,
               resample_dir=resample_dir)

    #
    # Now compute de-projected frames for each of the filters
    #
    for filtername in filters:

        raw_fn = "%s/%s_%s.fits" % (objname, objname, filtername)
        weight_fn = "%s/%s_%s.weight.fits" % (objname, objname, filtername)
        gri_fn = "%s/%s_%s.fits" % (objname, objname, filtername)

        stackfiles(imgout=raw_fn,
                   weightout=weight_fn,
                   inputlist=ugriz_filenames[filtername],
                   coverage_fn=coverage_fn)

    #
    # Now open the resulting stack files, and
    # - re-insert headers from original input frames
    # - mask all bad pixels (having 0 weights) with NaNs
    #

    # print("Deleting file cache")
    # try:
    #     os.system("rm -rf /tmp/tmp*")
    # except:
    #     pass

    print("All done with %s" % (objname))


if __name__ == "__main__":

    parser = OptionParser()
    parser.add_option("-r", "--radius", dest="radius",
                      help="Search radius / Field of view",
                      default=10., type=float)
    parser.add_option("", "--resamp", dest="resample_dir",
                      help="directory for swarp temporary files",
                        default="./", type=str)
    parser.add_option("-p", "--parallel", dest="parallel",
                      help="Download all files for a given object in parallel",
                      default=False, action='store_true')
    parser.add_option("-f", "--force", dest="force",
                      help="Force running, even if data already exists",
                      default=False, action='store_true')
    (options, cmdline_args) = parser.parse_args()

    if (os.path.isfile(cmdline_args[0])):
        # Read target names from file
        with open(cmdline_args[0], 'r') as listfile:
            objects = [l.strip() for l in listfile.readlines()]
    else:
        # Take one or more object names from command line
        objects = cmdline_args[0:]

    #
    # Now download all files, one after the other
    #
    print("Using %s for resampling" % (options.resample_dir))
    for objname in objects:
        if (os.path.isdir(objname) and not options.force):
            print "Object %s exists, skipping" % (objname)
            continue
        try:
            query_sdss_object(objname=objname,
                      radius=options.radius,
                      resample_dir=options.resample_dir,
                      parallel=options.parallel)
        except (KeyboardInterrupt, SystemError, SystemExit):
            raise
        except:
            error_fn = "%s.error" % (objname)
            etype, error, stackpos = sys.exc_info()

            exception_string = ["\n",
                        "=========== EXCEPTION ==============",
                        "etype: %s" % (str(etype)),
                        "error: %s" % (str(error)),
                        "stackpos: %s" % (str(stackpos)),
                        "---\n",
                        traceback.format_exc(),
                        "--- end\n"
            ]
            with open(error_fn, "w") as err:
                err.writelines(exception_string)

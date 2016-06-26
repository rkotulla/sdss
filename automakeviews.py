#!/usr/bin/env python

import os, sys, numpy
import makequickview
import glob

if __name__ == "__main__":

    objname = sys.argv[1]

    fn_template = "%s/%s_gri.filtered.*.fits" % (objname, objname)
    print fn_template

    fns = glob.glob(fn_template)
    weight_fn = glob.glob("%s/%s_gri.weight.fits" % (objname, objname))[0]

    print fns

    index_fn = "%s/index.html" % (objname)

    with open(index_fn, "w") as index_file:
        print >>index_file, "<html><body>"

        for fn in fns:
            outfile = fn[:-5]+".png"
            _, bn = os.path.split(outfile)
            if (not os.path.isfile(outfile)):
                makequickview.make_image(fn, weight_fn, outfile)

            print >>index_file, "<p><a href='%(f)s'><img src='%(f)s' style='width:400;'</img></a></p>" % {
                'f': bn,
            }
        print >>index_file, "</body></html>"
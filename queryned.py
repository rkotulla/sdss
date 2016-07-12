#!/usr/bin/env python

import os, sys
import astroquery.ned as ned

if __name__ == "__main__":

    objname = sys.argv[1]

    results = ned.Ned.query_object(objname)
    print results

    positions = ned.Ned.get_table(objname, table='positions')
    print positions

    notes = ned.Ned.get_table(objname, table='object_notes')
    print notes

    notes = ned.Ned.get_table(objname, table='classification')
    print notes

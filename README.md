REU program at UW Madison
# The search for central features in early-type galaxies
Student: Travis Stadler (North Caroline A &amp; T) /
Mentor: Ralf Kotulla (@rkotulla)


## Basic steps:
1) Download data using ```querysdss```
2) Computing unsharp-masking for frames with ```unsharp_mask```
3) optional: Convert FITS data to png for easier viewing using ```makequickview```
4) Inspect results and come up with list of interesting galaxies.


### How to use each of the tools

#### ```querysdss```

querysdss takes either a filename as only parameter, or a list of object identifiers (e.g. galaxy name, NGC number,
star name, or whatever simbad can resolve into coordinates). In the case of usng a filename as input, this file should
contain a list of object identifiers, with one object per line. Empty lines or lines starting starting with # are
ignored.

**Examples:**

Download images for M81, M82, M51 and M42:

```querysdss.py m82 m81 m51 m42```

Download a object list:

```querysdss.py objects.cat```

In this case, the ```objects.cat``` file should look like this:

```
M81
M82
M51
# M1
M42
```

#### ```unsharp_mask.py```

For proper unsharp-masking using gaussian-smoothing, run it like this:

```~/reu_sdss/unsharp_mask.py input_gri.fits --size=2,3,5,7,11,15,21,35 --mode=gauss```

or alternatively, run a median-filtering algorithm this way:

```~/reu_sdss/unsharp_mask.py input_gri.fits --size=3,7,15 --mode=median```



#### ```makequickview```
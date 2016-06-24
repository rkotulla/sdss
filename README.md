REU program at UW Madison
# The search for central features in early-type galaxies
Student: Travis Stadler /
Mentor: Ralf Kotulla (@rkotulla)


## Basic steps:
1) Download data using ```querysdss```
2) Computing unsharp-masking for frames with ```unsharp_mask```
3) optional: Convert FITS data to png for easier viewing using ```makequickview```
4) Inspect results and come up with list of interesting galaxies.


### How to use each of the tools

#### ```querysdss```

#### ```unsharp_mask.py```

For proper unsharp-masking using gaussian-smoothing, run it like this:

```~/reu_sdss/unsharp_mask.py input_gri.fits --size=2,3,5,7,11,15,21,35 --mode=gauss```

or alternatively, run a median-filtering algorithm this way:

```~/reu_sdss/unsharp_mask.py input_gri.fits --size=3,7,15 --mode=median```



#### ```makequickview```
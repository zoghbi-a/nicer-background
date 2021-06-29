
### NICER
The Neutron star Interior Composition Explorer ([NICER](https://heasarc.gsfc.nasa.gov/docs/nicer/)) is an International Space Station (ISS) payload devoted to the study of high energy X-ray sources in the Universe. Primarily designed to study Neutron Stars, but it can also study black holes in stellar systems and also in active galactic nuclei (AGN).


Unlike detectors that have CCD detectors that allow one to simultaenously separate photons from the source from those of the background by selecting the relevant regoins on the CCD, NICER does not produce images, so estimating the background is a non-trivial task.

To help with background estimates, NICER observed regions of the sky that are known to contain no X-ray sources, called `BKGD_RXTE[1..8]`. This model used those observations to train a machine learning model to estimate the background in observations of targets of interest.

The basic idea is to use `MKF` parameters that come with every observations, that contain information about the telescope and the envirenment during the observations, to estimate background.


### Content
This repository contains the trained model and spectral data that can be used to estimate the background of specific observations. The model has been trained, and the final product is provided here so it can be used.

There are 2 components in the model data:
- `nicerBgML.py`: a python script that reads the model files (`model.npz`) and produces a background spectrum for a given obsID.
- `nicerBgML.tgz`: The data of the model, and it includes two parts: the model files (`model.npz`) and the basis spectra `spec.*.pha`. The former is the numpy file that contains the trained model and related variables. The `spec.*.pha` are the basis spectra that are used to construct the background spectrum after the modeling.

### USAGE:
- Download both `nicerBgML.py` and `nicerBgML.tgz` files.
- unpack `nicerBgML.tgz`

Running `nicerBgML.py -h` print some useful information on the usages:
```
usage: nicerBgML.py [-h] [--dataDir dataDir] [--modelFile modelFile] [-v] obsID

Estimate NICER background using Machine Learning. This is a basic version that uses 50 MPUs (standard minus 14 and 34).
Version 0.1.t4n20 uses tBin=4 seconds and nGrp=20. - tBin is the time bin size use for constructing the model, and it is
the time bin size that will be used when binning the MKF data. - nGrp is the number of basis spectra used in the
modeling

positional arguments:
  obsID                 The obsID for which the background spectrum is to be estimated

optional arguments:
  -h, --help            show this help message and exit
  --dataDir dataDir     The path to the directory containing the data (default: nicerBgML)
  --modelFile modelFile
                        The name of the model npz file. Search in current folder and in dataDir (default: model.npz)
  -v, --version         show program's version number and exit
  
```
- If the folder containing the model data is `nicerBgML`, then from some `obsID` (e.g. `4693011001`), we use:
```
> python nicerBgML.py --dataDir ./nicerBgML  4693011001
```
If everything runs correctly, the background spectrum `spec.b.pha` will be created inside `4693011001/spec`


### WARNING
This is a basic version that uses 50 MPUs (standard 52 minus 14 and 34) using standard filtering criteria. If  you use a different number of MPUs, you will have to scale the background spectrum accordingly.

If you use a filtering criterian that is different from the standard one in `nicerl2`, this model may not be applicable. I am working on ways to include non-standard selection criteria in the future.
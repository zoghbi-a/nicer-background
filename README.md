
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

### Requirement
- The script uses `fcurve` and `mathpha` from `ftools`, so a functioning installation of `heasoft` is needed.
- The following python libraries are needed:
    - `numpy`
    - `astropy`
    - `pandas`
    - `sklearn`
    - `py-xgboost`
    
The python libraries can be installed with `conda` (e.g. `pip install numpy astropy pandas sklearn py-xgboost`).

Note that py-xgboost is available only through conda not through pip. See the section "Known Issues" below.

- Version **0.2.t4n20** requires a geomagnetic data file (kpFile in the USAGE section below). The latest file can be downloaded from https://heasarc.gsfc.nasa.gov/FTP/caldb/data/gen/pcf/geomag/kp_noaa.fits. The model was trained using the noaa data file, so it is suggested that it is the one used and not the Potsdam one (see discussion [here](https://heasarc.gsfc.nasa.gov/docs/nicer/analysis_threads/geomag/)).

- See the **Known Issues** section below for a modification to the `fcurve` code that may be needed for the script to run correctly.

### USAGE:
- Download both `nicerBgML.py` and `nicerBgML.tgz` files.
- unpack `nicerBgML.tgz`

Running `nicerBgML.py -h` print some useful information on the usages:
```
usage: nicerBgML.py [-h] [--dataDir dataDir] [--modelFile modelFile] [-v] obsID kpFile

Estimate NICER background using Machine Learning. This is a basic version that uses 50 MPUs (standard minus 14 and 34). Version
0.2.t4n20 uses tBin=4 seconds and nGrp=20. Unlike 0.1.t4n20, this version include more MKF parameters, including the KP parameter used
in the space weather model. - tBin is the time bin size use for constructing the model, and it is the time bin size that will be used
when binning the MKF data. - nGrp is the number of basis spectra used in the modeling The kpFile parameter should point to the latest
KP index file that can be downloaded from https://heasarc.gsfc.nasa.gov/FTP/caldb/data/gen/pcf/geomag/kp_noaa.fits. See
https://heasarc.gsfc.nasa.gov/docs/nicer/analysis_threads/geomag/ for details.

positional arguments:
  obsID                 The obsID for which the background spectrum is to be estimated
  kpFile                The KP index file. Download from: https://heasarc.gsfc.nasa.gov/FTP/caldb/data/gen/pcf/geomag/kp_noaa.fits

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

### VERSIONS:
- **0.1.t4n20**: This is the first model presented at the NICER Observatory Science Working Group (OSWG) on June 30, 2021. It is based on a classification model that uses 15 parameters from the MKF file sampled every 4 seconds to classify the background data into 20 basis spectra. The root-mean-squared performance in the background estimates is `2.0` counts/s vs `3.2` in the 3C50 model. If the 1% outlier backgorund observations are discarded, the performance is `1.3` counts/s (vs `2.3` for the 3C50 model).


- **0.2.t4n20**: This is an enhanced version of 0.1.t4n20, released on July 11, 2021. It is based on more MKKF parameters, 27 in total, including the KP index from the geomagnetic data. It is also a classification model that samples the MKF parameters every 4 seconds that classifies the background data into 20 basis spectra. The root-mean-squared performance in the background estimates is `1.7` counts/s vs `3.2` in the 3C50 model. If the 1% outlier backgorund observations are discarded, the performance is `0.87` counts/s (vs `2.3` for the 3C50 model).

### WARNING
This is a basic version that uses 50 MPUs (standard 52 minus 14 and 34) using standard filtering criteria. If  you use a different number of MPUs, you will have to scale the background spectrum accordingly.

If you use a filtering criterian that is different from the standard one in `nicerl2`, this model may not be applicable. I am working on ways to include non-standard selection criteria in the future.

### Known Issues
- If the script fails when running `fcurve`, then it is likely because a possible bug in `fcurve`. It cannot handle a long list of columns. The number of columns used here (15) cannot fit into the fortran character array used. A simple fix, until it is permanently fixed, is to change that manually and re-compile it.
    - For heasoft version 6.28 for example, the source code is in `heasoft-6.28/ftools/futils/tasks/fcurve/fcurve.f`.
    - Edit the lines that define `columns` amd `outcols` to use longer character length (the lines following `subroutine fcurve`). Change `character(80)` to `character(300)` for example.
    - Then within `heasoft-6.28/ftools/futils/tasks/fcurve`, recompile the code by running: `hmake; hmake install`
    
- Installing xgboost may be problematic on some systems. If you are running python through anaconda (recommended), then
  you can just install py-xgboost (conda install py-xgboost), that should be all that is needed.
Installing xgboost from pip may give you an error related to libomp. In that case there a few options:
    - install libomp with brew: brew install libomp; then install xgboost with pip: pip install xgboost
    - build xgboost from source. See instructions in: https://xgboost.readthedocs.io/en/latest/build.html
    - Install anaconda https://www.anaconda.com/products/individual, and install py-xgboost using: conda install
      py-xgboost.

- Please report other issues running the model script [here](https://docs.google.com/forms/d/11BAm5DWL85VLaAMTv_cgM0v8PB_7UBLiNeJOyqep_9k)

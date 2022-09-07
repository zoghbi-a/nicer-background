
### NICER
The Neutron star Interior Composition Explorer ([NICER](https://heasarc.gsfc.nasa.gov/docs/nicer/)) is an International Space Station (ISS) payload devoted to the study of high energy X-ray sources in the Universe. Primarily designed to study Neutron Stars, but it can also study black holes in stellar systems and also in active galactic nuclei (AGN).


Unlike detectors that have CCD detectors that allow one to simultaenously separate photons from the source from those of the background by selecting the relevant regoins on the CCD, NICER does not produce images, so estimating the background is a non-trivial task.

To help with background estimates, NICER observed regions of the sky that are known to contain no X-ray sources, called `BKGD_RXTE[1..8]`. This model used those observations to train a machine learning model to estimate the background in observations of targets of interest.

The basic idea is to use `MKF` parameters that come with every observations, that contain information about the telescope and the envirenment during the observations, to estimate the background.


### Content
This repository contains the trained model and spectral data that can be used to estimate the background of specific observations. The model has been trained using `xgboost`, and the final product is provided here so it can be used.

There are 2 components in the model data:
- `nicerBgML.py`: a python script that reads the model files (`model.npz`) and produces a background spectrum for a given obsID.
- [nicerBgML_0.4.t1.200e.tgz](https://osf.io/dg72b/download): The data of the model, and it includes two parts: the model files (`model.npz`) and the basis spectra `spec.*.pha`. The former is the numpy file that contains the trained model and related variables. The `spec.*.pha` are the basis spectra that are used to construct the background spectrum after the modeling. This file can be [downloaded here](https://osf.io/dg72b/download).

### Requirement
- The script uses `fcurve` and `mathpha` from `ftools` and `nicerl2`, so a functioning installation of `heasoft` is needed. The modeling was does using `heasoft-6.29c`, so it is recommended that the script is used with that version. Other versions of heasoft may fail to extract all the MKF parameters needed for the modeling.
- The following python libraries are needed:
    - `numpy`
    - `astropy`
    - `pandas`
    - `sklearn`
    - `py-xgboost==1.3.3`
    
The python libraries can be installed with `conda` (e.g. `pip install numpy astropy pandas sklearn py-xgboost`).

Note that py-xgboost is available only through conda not through pip. See the section "Known Issues" below.

- Version **0.4.t1.200e** requires a geomagnetic data files that can be downloaded from https://heasarc.gsfc.nasa.gov/FTP/caldb/data/gen/pcf/geomag (see discussion [here](https://heasarc.gsfc.nasa.gov/docs/nicer/analysis_threads/geomag/)).. Please download the 6 files: `dst_kyoto.fits`, `f107_petincton.fits`, `geomag.tar.gz`, `kp_noaa.fits`, `kp_potsdam.fits`, `solarphi_oulu.fits` into some directory and then provide the location of that directory as input to the `nicerBgML.py` script. See USAGE section below.


- See the **Known Issues** section below for a modification to the `fcurve` code that may be needed for the script to run correctly.

### USAGE:
- Download both `nicerBgML.py` and `nicerBgML.tgz` files.
- unpack `nicerBgML.tgz`

Running `nicerBgML.py -h` print some useful information on the usages:
```
usage: nicerBgML.py [-h] [--dataDir dataDir] [--modelFile modelFile] [-v] obsID kpDir

Estimate NICER background using Machine Learning. This is a basic version that uses 50 MPUs (standard minus 14 and 34). Version 0.4.t1.200e uses tBin=1
seconds and 50 spectral bins (nGrp). The main difference compared to other version is that we model the spectra in two bands: 0.2-0.4 and 0.4-15, so the model
has the largest energy coverage of previously-released models. Similar to the 0.3 version model, we use more MKF parameters including the space weather model.
- tBin is the time bin size used for constructing the model, and it is the time bin size that will be used when binning the MKF data. - nGrp is the number of
basis spectra used in the modeling The kpDir parameter should point to the directory containing the geomagnetic data: dst_kyoto.fits, f107_petincton.fits,
geomag.tar.gz, kp_noaa.fits, kp_potsdam.fits, solarphi_oulu.fits availabel in: https://heasarc.gsfc.nasa.gov/FTP/caldb/data/gen/pcf/geomag See
https://heasarc.gsfc.nasa.gov/docs/nicer/analysis_threads/geomag/ for details.

positional arguments:
  obsID                 The obsID for which the background spectrum is to be estimated
  kpDir                 Location of the geomagnetic data. Download from: https://heasarc.gsfc.nasa.gov/FTP/caldb/data/gen/pcf/geomag/; There are 6 files:
                        dst_kyoto.fits f107_petincton.fits geomag.tar.gz kp_noaa.fits kp_potsdam.fits solarphi_oulu.fits

optional arguments:
  -h, --help            show this help message and exit
  --dataDir dataDir     The path to the directory containing the model data, including the basis spectra (default: nicerBgML)
  --modelFile modelFile
                        The name of the model npz file. Search in current folder and in dataDir (default: model.npz)
  -v, --version         show program's version number and exit
  
```
- If the folder containing the model data is `nicerBgML`, then from some `obsID` (e.g. `4693011001`), we use:
```
> python nicerBgML.py --dataDir ./nicerBgML  4693011001 /location/of/geomagnetic/data/
```
If everything runs correctly, the background spectrum `spec.b.pha` will be created inside `4693011001/spec`

### VERSIONS:

- **0.4.t1.200e (Latest)**: This is an updated version, published on December 6, 2021. The input parameters to the model are similar to the previous verion, but it is optimized for the whole **0.2-15** keV band. It works by modeling the data in 2 bands: 0.2-0.4 and 0.4-15 keV. It is a classification model that samples the MKF parameters every 1 second and classifies the background data into 50 basis spectra. The root-mean-squared performance in the background estimates is `1.5` counts/s vs `73` in the 3C50 model. If the 1% outlier backgorund observations are discarded, the performance is `0.7` counts/s (vs `9.6` for the 3C50 model), all measured over the whole 0.2-15 keV band.

- **0.3.t1.35**: This version uses the latest heasoft updates (as of August 2021). The model is optimizd to work in the energy range **0.5-10** keV (unlike the previous version). It uses 40 MKF parameters, including those from the geomagnetic data. It is a classification model that samples the MKF parameters every 1 second and classifies the background data into 35 basis spectra. The root-mean-squared performance in the background estimates is `0.21` counts/s vs `4.04` in the 3C50 model. If the 1% outlier backgorund observations are discarded, the performance is `0.15` counts/s (vs `1.25` for the 3C50 model).

- **0.2.t4n20**: This is an enhanced version of 0.1.t4n20, released on July 11, 2021. It is based on more MKKF parameters, 27 in total, including the KP index from the geomagnetic data. It is also a classification model that samples the MKF parameters every 4 seconds that classifies the background data into 20 basis spectra. The root-mean-squared performance in the background estimates is `1.7` counts/s vs `3.2` in the 3C50 model. If the 1% outlier backgorund observations are discarded, the performance is `0.87` counts/s (vs `2.3` for the 3C50 model).

- **0.1.t4n20**: This is the first model presented at the NICER Observatory Science Working Group (OSWG) on June 30, 2021. It is based on a classification model that uses 15 parameters from the MKF file sampled every 4 seconds to classify the background data into 20 basis spectra. The root-mean-squared performance in the background estimates is `2.0` counts/s vs `3.2` in the 3C50 model. If the 1% outlier backgorund observations are discarded, the performance is `1.3` counts/s (vs `2.3` for the 3C50 model).


### WARNING
This is a basic version that uses 50 MPUs (standard 52 minus 14 and 34) using standard filtering criteria (`detlist=launch,-14,-34 min_fpm=50` in `nicerl2`). If  you use a different number of MPUs, you will have to scale the background spectrum accordingly.

If you use a filtering criterian that is different from the standard one in `nicerl2`, this model may not be applicable. I am working on ways to include non-standard selection criteria in the future.

### Known Issues
- If the script fails when running `fcurve`, then it is likely because a possible bug in `fcurve`. It cannot handle a long list of columns. The number of columns used here (15) cannot fit into the fortran character array used. A simple fix, until it is permanently fixed, is to change that manually and re-compile it.
    - For heasoft version 6.29 for example, the source code is in `heasoft-6.28/ftools/futils/tasks/fcurve/fcurve.f`.
    - Edit the lines that define `columns` amd `outcols` to use longer character length (the lines following `subroutine fcurve`). Change `character(80)` to `character(N)` for some large number `N` (e.g. 2000).
    - Then within `heasoft-6.29/ftools/futils`, recompile the code by running: `hmake; hmake install`
    
- Installing xgboost may be problematic on some systems. If you are running python through anaconda (recommended), then
  you can just install py-xgboost (conda install py-xgboost), that should be all that is needed.
Installing xgboost from pip may give you an error related to libomp. In that case there a few options:
    - install libomp with brew: brew install libomp; then install xgboost with pip: pip install xgboost
    - build xgboost from source. See instructions in: https://xgboost.readthedocs.io/en/latest/build.html
    - Install anaconda https://www.anaconda.com/products/individual, and install py-xgboost using: conda install
      py-xgboost.

- Please report other issues running the model script [here](https://github.com/zoghbi-a/nicer-background/issues)

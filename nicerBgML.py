#!/usr/bin/env python

import numpy as np
import subprocess as subp
import argparse
import os
from astropy.io import fits
from astropy.table import Table
import pandas as pd
from sklearn.pipeline import Pipeline


__version__ = '0.4.t1.200e'


if __name__ == '__main__':
    p   = argparse.ArgumentParser(
        description='''
        Estimate NICER background using Machine Learning.
        
        This is a basic version that uses 50 MPUs (standard minus 14 and 34).
        Version 0.4.t1.200e uses tBin=1 seconds and 50 spectral bins (nGrp). The main difference
        compared to other version is that we model the spectra in two bands: 0.2-0.4 and 0.4-15, so the model
        has the largest energy coverage of previously-released models. Similar to the 0.3 version model,
        we use more MKF parameters including the space weather model.
        - tBin is the time bin size used for constructing the model, and it is 
        the time bin size that will be used when binning the MKF data.
        - nGrp is the number of basis spectra used in the modeling
        
        The kpDir parameter should point to the directory containing the geomagnetic data:
        dst_kyoto.fits, f107_petincton.fits, geomag.tar.gz, kp_noaa.fits, kp_potsdam.fits, solarphi_oulu.fits
        availabel in: https://heasarc.gsfc.nasa.gov/FTP/caldb/data/gen/pcf/geomag
        See https://heasarc.gsfc.nasa.gov/docs/nicer/analysis_threads/geomag/ for details.
        
        ''',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter )

    p.add_argument("obsID", metavar="obsID", type=str,
            help="The obsID for which the background spectrum is to be estimated")
    p.add_argument("kpDir", metavar="kpDir", type=str,
            help=("Location of the geomagnetic data. Download from: "
                  "https://heasarc.gsfc.nasa.gov/FTP/caldb/data/gen/pcf/geomag/; "
                  "There are 6 files: dst_kyoto.fits f107_petincton.fits geomag.tar.gz "
                  "kp_noaa.fits kp_potsdam.fits solarphi_oulu.fits"
                  ))
    p.add_argument("--dataDir", metavar="dataDir", type=str, default='nicerBgML',
            help="The path to the directory containing the model data, including the basis spectra")
    p.add_argument("--modelFile", metavar="modelFile", type=str, default='model.npz',
            help="The name of the model npz file. Search in current folder and in dataDir")
    
    p.add_argument("-v", "--version", action='version', version=__version__)
    args = p.parse_args()
    
    
    # check if heasoft is initilized #
    if not 'FTOOLS' in os.environ:
        raise RuntimeError('heasoft does not appear to be initilized.')
    
    
    ## check in the input ##
    obsID = args.obsID
    if not os.path.exists(obsID):
        raise ValueError(f'There is no obsID folder named {obsID}')
    obsIDDir = obsID
    if len(obsID.split('/')) != 1:
        ss = obsID.split('/')
        obsID = ss[-1]

    kpDir = args.kpDir
    if not os.path.exists(kpDir):
        raise ValueError((f'There is no folder named {kpDir}. '
                          'Please download all files from: '
                          'https://heasarc.gsfc.nasa.gov/FTP/caldb/data/gen/pcf/geomag/'))
    
    dataDir = args.dataDir
    if not os.path.exists(dataDir):
        raise ValueError(f'Cannot find data directory {dataDir}')
    # a naive way to check if dataDir is relative or absolute
    if dataDir[0] != '/':
        dataDir = os.getcwd() + '/' + dataDir
        
    modelFile = args.modelFile
    if not os.path.exists(modelFile):
        if not os.path.exists(f'{dataDir}/{modelFile}'):
            raise ValueError(f'Cannot find model file {modelFile}')
        modelFile = f'{dataDir}/{modelFile}'
        
        
        
    # read the model file #
    print('reading model data ...')
    modData = np.load(modelFile, allow_pickle=True)
    mod       = modData['mod'][()]
    tBin      = modData['tBin']
    mkfCols   = modData['mkfCols'][()]
    XPreProc  = Pipeline(steps=[(f'step-{i}', x) for i,x in enumerate(modData['XPreProc'])])
    print('... Done'); print('-'*20)
    
    # extract mkf data #
    cwd = os.getcwd()
    os.chdir(obsIDDir)
    os.system('mkdir -p spec')
    os.chdir('spec')


    # bin the mkf file
    suff = f't{tBin}'
    pre = 'export HEADASNOQUERY=; export HEADASPROMPT=/dev/null;'
    
    # add the kp index to the mkf file
    print('Genrating MKF parameters ...')
    extraOptions = (f'geomag_path={kpDir} '
                     'filtcolumns=NICERV3,3C50 '
                     'detlist=launch,-14,-34 min_fpm=50 '
                     'tasks=MKF '
                    )
    cmd = f'nicerl2 {obsID} {extraOptions} clobber=yes'
    os.chdir(f'{cwd}/{obsIDDir}/..')
    info = subp.call(['/bin/bash', '-c', pre + cmd])
    if info != 0:
        raise RuntimeError(('Failed creating/updating MKF file.'))
    print('... Done'); print('-'*20)
    os.chdir(f'{cwd}/{obsIDDir}/spec')
    
    print('reading MKF data ...')
    cmd = (f'fcurve infile=../auxil/ni{obsID}.mkf gtifile=../xti/event_cl/ni{obsID}_0mpu7_cl.evt[GTI] '
           f'outfile=ni.{suff}.mkf.tmp timecol=TIME columns="{mkfCols}" '
           f'binsz={tBin*1.0} lowval=INDEF highval=INDEF binmode=Mean '
           f'outerr=NONE outlive=FRACEXP clobber=yes')
    subp.call(['/bin/bash', '-c', pre + cmd])
    cmd = (f'fselect ni.{suff}.mkf.tmp ni.{suff}.mkf "FRACEXP>0" clobber=yes')
    info = subp.call(['/bin/bash', '-c', pre + cmd])
    if info==0:
        os.system(f'rm ni.{suff}.mkf.tmp')
    else:
        print(('Running fcurve failed. For possible solutions, please have a look '
               'at the Known Issues section on the website!'))

    
    # read the mkf data
    mkfLcB = Table(fits.open(f'ni.{suff}.mkf')[1].data).to_pandas()
    if mkfLcB.shape[0] == 0:
        print('There are no data in the MKF file ... stopping')
        exit(0)
    
    print('... Done'); print('-'*20)
    
    
    print('getting model predictions ...')
    # apply the model pre-processing to this obsID
    XB = XPreProc.transform(mkfLcB.loc[:,mkfCols.split(',')])
    
    # model prediction #
    yPred = mod.predict(XB)
    
    # Calcualte the weights #
    gPred   = yPred.astype(int)
    weights = pd.DataFrame({'weights':gPred+1}).groupby('weights').apply(len)/len(gPred)
    weights = weights[weights > 0]
    print(weights)
    print('... Done'); print('-'*20)
    
    # create weighted background file #
    os.chdir(dataDir)
    expr = '+'.join([f'{x:6.6}*spec.{i}.pha' for i,x in weights.items()])
    cmd = f'mathpha "{expr}" R spec.b.pha CALC NULL 0 clobber=yes'
    print(cmd)
    info = subp.call(['/bin/bash', '-c', pre + cmd])
    if info != 0:
        raise RuntimeError(f'Combining the spectra failed: \n{cmd}')
    info = os.system(f'mv spec.b.pha {cwd}/{obsIDDir}/spec/')
    if info == 0:
        print(f'Background file {obsIDDir}/spec/spec.b.pha created successfully'); print('-'*20)
    

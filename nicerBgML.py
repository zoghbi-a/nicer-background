#!/usr/bin/env python

import numpy as np
import subprocess as subp
import argparse
import os
from astropy.io import fits
from astropy.table import Table
import pandas as pd
from sklearn.pipeline import Pipeline


__version__ = '0.1.t4n20'


if __name__ == '__main__':
    p   = argparse.ArgumentParser(
        description='''
        Estimate NICER background using Machine Learning.
        
        This is a basic version that uses 50 MPUs (standard minus 14 and 34).
        Version 0.1.t4n20 uses tBin=4 seconds and nGrp=20. 
        - tBin is the time bin size use for constructing the model, and it is 
        the time bin size that will be used when binning the MKF data.
        - nGrp is the number of basis spectra used in the modeling
        
        ''',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter )

    p.add_argument("obsID", metavar="obsID", type=str,
            help="The obsID for which the background spectrum is to be estimated")
    p.add_argument("--dataDir", metavar="dataDir", type=str, default='nicerBgML',
            help="The path to the directory containing the data")
    p.add_argument("--modelFile", metavar="modelFile", type=str, default='model.npz',
            help="The name of the model npz file. Search in current folder and in dataDir")
    
    p.add_argument("-v", "--version", action='version', version=__version__)
    args = p.parse_args()
    
    
    ## check in the input ##
    obsID = args.obsID
    if not os.path.exists(obsID):
        raise ValueError(f'There is no obsID folder named {obsID}')
    obsIDDir = obsID
    if len(obsID.split('/')) != 1:
        ss = obsID.split('/')
        obsID = ss[-1]
    
    dataDir = args.dataDir
    if not os.path.exists(dataDir):
        raise ValueError(f'Cannot find data directory {dataDir}')
        
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
    mpuFilter = modData['mpuFilter']
    mkfCols   = modData['mkfCols']
    XPreProc  = Pipeline(steps=[(f'step-{i}', x) for i,x in enumerate(modData['XPreProc'])])
    print('... Done'); print('-'*20)
    
    # extract mkf data #
    cwd = os.getcwd()
    os.chdir(obsIDDir)
    os.system('mkdir -p spec')
    os.chdir('spec')


    # bin the mkf file
    print('reading MKF data ...')
    suff = f't{tBin}'
    pre = 'export HEADASNOQUERY=; export HEADASPROMPT=/dev/null;'
    cmd = (f'fcurve infile=../auxil/ni{obsID}.mkf gtifile=../xti/event_cl/ni{obsID}_0mpu7_cl.evt[GTI] '
           f'outfile=ni.{suff}.mkf.tmp timecol=TIME columns="{mkfCols}" '
           f'binsz={tBin*1.0} lowval=INDEF highval=INDEF binmode=Mean '
           f'outerr=NONE outlive=FRACEXP clobber=yes')
    subp.call(['/bin/bash', '-c', pre + cmd])
    cmd = (f'fselect ni.{suff}.mkf.tmp ni.{suff}.mkf "FRACEXP>0" clobber=yes')
    info = subp.call(['/bin/bash', '-c', pre + cmd])
    if info==0:
        os.system(f'rm ni.{suff}.mkf.tmp')

    
    # read the mkf data
    mkfLcB = Table(fits.open(f'ni.{suff}.mkf')[1].data).to_pandas()
    if mkfLcB.shape[0] == 0:
        print('There are no data in the MKF file ... stopping')
        exit(0)
    
    print('... Done'); print('-'*20)
    
    
    print('getting model predictions ...')
    # apply the model pre-processing to this obsID
    XB = XPreProc.transform(mkfLcB.iloc[:,1:-1])
    
    # model prediction #
    yPred = mod.predict(XB)
    
    # Calcualte the weights #
    gPred   = yPred.astype(np.int)
    weights = pd.DataFrame({'weights':gPred+1}).groupby('weights').apply(len)/len(gPred)
    weights = weights[weights > 0]
    print(weights)
    print('... Done'); print('-'*20)
    
    # create weighted background file #
    os.chdir(f'{cwd}/{dataDir}')
    expr = '+'.join([f'{x:4.4}*spec.{i}.pha' for i,x in weights.items()])
    cmd = f'mathpha "{expr}" R spec.b.pha CALC NULL 0 clobber=yes'
    print(cmd)
    info = subp.call(['/bin/bash', '-c', pre + cmd])
    if info != 0:
        raise RuntimeError(f'Combining the spectra failed: \n{cmd}')
    info = os.system(f'mv spec.b.pha {cwd}/{obsIDDir}/spec/')
    if info == 0:
        print(f'Background file {obsIDDir}/spec/spec.b.pha created successfully'); print('-'*20)
    
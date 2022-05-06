#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Description of this script.
The description of the script .
It can be referred in the ArgumentParser constructor as __doc__.
"""

import argparse
from email.policy import default
import logging

import os
from pathlib import Path

from allensdk.api.queries.mouse_connectivity_api import MouseConnectivityApi
import nibabel as nib
import nrrd
import numpy as np
import pandas as pd
import ants

EPILOG = """
[1] Made by.., Subject..., Date... 
"""

def _build_arg_parser():
    p = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter,
                                description=__doc__)
    p.add_argument('id', type=int,
                    help='Id of the experiment in Allen Mouse Brain Connectivity Atlas. ')
    p.add_argument('-r', '--res', type=int, default=100, choices=[25, 50, 100],
                    help='Base resolution (µm) of the projection density to download. \n'
                         'Note: The final resolution will be 70µm anyways.')
    p.add_argument('-d', '--dir', default=".",
                    help='Absolute path of the ouptut file.')
    p.add_argument('-i', '--interp', action="store_true",
                    help='Interpolation method is NN by default. \n'
                         'Using --interp will change the methode to bS.')
                         
    p.add_argument('-f', dest='overwrite', action="store_true",
                    help='Force overwriting of the output file.')                   

    return p

def main():
    parser = _build_arg_parser()
    args = parser.parse_args()

    args.dir = Path(args.dir)
    args.dir.absolute()
    args.dir.mkdir(exist_ok=True, parents=True)

    avgt_file   = '/Users/mahdi/stage-2022-mahdi/utils/AVGT.nii.gz' # todo
    avgt_r_mm   = 70 / 1e3
    avgt_offset = np.array([-5.675, -8.79448, -8.450335, 0])

    mca = MouseConnectivityApi()
    
    roi = pd.DataFrame(mca.get_experiment_detail(args.id)).specimen[0]['stereotaxic_injections'][0]['primary_injection_structure']['acronym']

    if   args.res == 100 : mca_res = mca.VOXEL_RESOLUTION_100_MICRONS
    elif args.res == 50  : mca_res = mca.VOXEL_RESOLUTION_50_MICRONS
    elif args.res == 25  : mca_res = mca.VOXEL_RESOLUTION_25_MICRONS

    nrrd_file  = args.dir / f"{args.id}_{roi}_projection_density_{args.res}.nrrd"
    nifti_file = args.dir / f"{args.id}_{roi}_projection_density_{args.res}.nii.gz"

    mca.download_projection_density(
        nrrd_file,
        experiment_id = args.id, 
        resolution    = mca_res
        )

    allen_vol, header = nrrd.read(nrrd_file)
    os.remove(nrrd_file)

    allen_vol = np.moveaxis(allen_vol, (0,1,2), (1,2,0))
    allen_vol = np.flip(allen_vol, axis=2)
    allen_vol = np.flip(allen_vol, axis=1)

    affine = np.eye(4) * avgt_r_mm

    avgt_vol = nib.load(avgt_file).get_fdata().astype(np.float32)
    allen_vol = allen_vol.astype(np.float32)

    fixed  = ants.from_numpy( avgt_vol  ).resample_image((164, 212, 158),1,0)
    moving = ants.from_numpy( allen_vol ).resample_image((164, 212, 158),1,0)

    # todo
    transformations = [f'/Users/mahdi/stage-2022-mahdi/utils/transformations_allen2avgt/allen2avgt_{args.res}.nii.gz',
                       f'/Users/mahdi/stage-2022-mahdi/utils/transformations_allen2avgt/allen2avgtAffine_{args.res}.mat']

    interp = 'nearestNeighbor'
    if args.interp : 
        interp = 'bSpline'
        nifti_file = args.dir / f"{args.id}_{roi}_projection_density_{args.res}_{interp}.nii.gz"

    warped_moving = ants.apply_transforms(fixed = fixed,  moving = moving, 
                                          transformlist = transformations,
                                          interpolator  = interp)

    affine[:,3] = affine[:,3] + avgt_offset

    warped_vol = warped_moving.numpy()

    if args.interp :
        for z in range(158):
            for y in range(212):
                for x in range(164):
                    if warped_vol[x, y, z] < 0:
                        warped_vol[x, y, z] = 0.0
    
    img = nib.Nifti1Image(warped_vol, affine)
    nib.save(img, nifti_file)

    return nifti_file


if __name__ == "__main__":
    main()
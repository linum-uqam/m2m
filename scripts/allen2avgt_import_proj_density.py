#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    Import projection density from the Allen Mouse Brain Connectivity Atlas
    and align it on the Average Template.

    >>> python allen2avgt_import_proj_density.py id
    >>> python allen2avgt_import_proj_density.py id --res res --dir directory
    >>> python allen2avgt_import_proj_density.py id --interp
"""

import argparse
from email.policy import default
import logging

import os
from pathlib import Path
from tabnanny import check

import numpy as np
import pandas as pd

from allensdk.api.queries.mouse_connectivity_api import MouseConnectivityApi
from allensdk.core.mouse_connectivity_cache import MouseConnectivityCache

import nibabel as nib
import nrrd
import ants

EPILOG = """
Author : Mahdi
"""


def _build_arg_parser():
    p = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter,
                                epilog=EPILOG, description=__doc__)
    p.add_argument('id', type=int,
                   help='Id of the experiment in the Allen Mouse Brain Connectivity Atlas. ')
    p.add_argument('-r', '--res', type=int, default=100, choices=[25, 50, 100],
                   help='Resolution of the dowloaded projection density is 100µm by default.\n'
                        'Using --res <value> will set the resolution to value.')
    p.add_argument('-d', '--dir', default=".",
                   help='Path of the ouptut file directory is . by default.\n'
                        'Using --dir <dir> will change the output file\'s directory\n'
                        'or create a new one if does not exits.')
    p.add_argument('--smooth', action="store_true",
                   help='Interpolation method is nearestNeighbor by default.\n'
                        'Using --smooth will change the method to bSpline.')
    p.add_argument('-f', dest='overwrite', action="store_true",
                   help='Force overwriting of the output file.')
    p.add_argument('-c', '--cache', action="store_true",
                   help='Update the Allen Mouse Brain Connectivity Cache')
    return p


def check_id(parser, args):
    """
    Verify if the experiment id is part of the Allen Mouse Brain Connectivity Atlas.
    Read all experiments ids from the Allen Mouse Brain Connectivity Cache.
    Download the Cache files if does not exist or --cache used.

    Parameters
    ----------
    parser: argparse.ArgumentParser object
        Parser.
    args: argparse namespace
        Argument list.
    """
    experiments_path = './utils/cache/allen_mouse_conn_experiments.json'
    manifest_path = './utils/cache/mouse_conn_manifest.json'

    if os.path.isfile(experiments_path) and os.path.isfile(manifest_path) and args.cache:
        os.remove(experiments_path)
        os.remove(manifest_path)

    mcc = MouseConnectivityCache(manifest_file=manifest_path)
    ids = mcc.get_experiments(dataframe=True, file_name=experiments_path).id
    if args.id not in ids:
        parser.error("This experiment id doesn't exist. \n"
                     "Please check : https://connectivity.brain-map.org/")
        exit()


def check_file_exists(parser, args, path):
    """
    Verify that output does not exist or that if it exists, -f should be used.
    If not used, print parser's usage and exit.

    Parameters
    ----------
    parser: argparse.ArgumentParser object
        Parser.
    args: argparse namespace
        Argument list.
    path: string or path to file
        Required path to be checked.
    """
    if os.path.isfile(path) and not args.overwrite:
        parser.error('Output file {} exists. Use -f to force '
                     'overwriting'.format(path))

    path_dir = os.path.dirname(path)
    if path_dir and not os.path.isdir(path_dir):
        parser.error('Directory {}/ \n for a given output file '
                     'does not exists.'.format(path_dir))


def loc_injection_centroid(args):
    """
    Localize the position (Left or Right) of the injection centroid in the Mouse Brain.
    A resolution of 100µm is used to minimize downloading time.

    Parameters
    ----------
    args: argparse namespace
        Argument list.

    Return
    ------
    string : R or L
    """
    # Creating tmp files
    path_fraction = f"./utils/tmp/{args.id}_inj_fraction.nrrd"
    path_density = f"./utils/tmp/{args.id}_density.nrrd"

    mca = MouseConnectivityApi()

    # Disabling the download logger.
    logging.getLogger('allensdk.api.api.retrieve_file_over_http').disabled = True

    # Downloading the injection fraction and density of the experiment
    injection_density = mca.download_injection_density(path_density,
                                                       experiment_id=args.id, resolution=100)
    injection_fraction = mca.download_injection_fraction(path_fraction,
                                                         experiment_id=args.id, resolution=100)

    # Re-enabling the logger
    logging.getLogger('allensdk.api.api.retrieve_file_over_http').disabled = False

    # Loading the volumes
    dens_vol, header = nrrd.read(path_density)
    frac_vol, header = nrrd.read(path_fraction)

    # Removing tmp files
    os.remove(path_density)
    os.remove(path_fraction)

    # Downloading the injection centroid
    injection_centroid = mca.calculate_injection_centroid(injection_density=dens_vol,
                                                          injection_fraction=frac_vol)

    # Defining the Left-Right limit (+z axis)
    # Note: the bounding box is [2640, 1600, 2280]
    limit_LR = 1140/2

    # Returning the position
    if injection_centroid[2] >= limit_LR:
        return 'R'
    else:
        return 'L'


def main():
    # Building argparser
    parser = _build_arg_parser()
    args = parser.parse_args()

    # Verifying experiment id
    check_id(parser, args)

    # Configuring output directory
    args.dir = Path(args.dir)
    args.dir.mkdir(exist_ok=True, parents=True)

    # AVGT settings
    avgt_file = './utils/AVGT.nii.gz'
    avgt_r_mm = 70 / 1e3
    avgt_offset = np.array([-5.675, -8.79448, -8.450335, 0])

    mca = MouseConnectivityApi()

    # ROI of the experiment
    roi = pd.DataFrame(mca.get_experiment_detail(args.id)).specimen[0]['stereotaxic_injections'][0]['primary_injection_structure']['acronym']

    # Position of the injection centroid
    loc = loc_injection_centroid(args)

    # Choosing the downloaded resolution
    if args.res == 100:
        mca_res = mca.VOXEL_RESOLUTION_100_MICRONS
    elif args.res == 50:
        mca_res = mca.VOXEL_RESOLUTION_50_MICRONS
    elif args.res == 25:
        mca_res = mca.VOXEL_RESOLUTION_25_MICRONS

    # Configuring file names
    nrrd_file = args.dir / f"{args.id}_{roi}_{loc}_proj_density_{args.res}.nrrd"
    nifti_file = args.dir / f"{args.id}_{roi}_{loc}_proj_density_{args.res}.nii.gz"

    # Setting up the interpolation method
    interp = 'nearestNeighbor'
    if args.smooth:
        interp = 'bSpline'
        nifti_file = args.dir / f"{args.id}_{roi}_{loc}_proj_density_{args.res}_{interp}.nii.gz"

    # Verifying if outputs already exist
    check_file_exists(parser, args, nifti_file)

    # Downloading projection density (API)
    mca.download_projection_density(
        nrrd_file,
        experiment_id=args.id,
        resolution=mca_res
        )

    # Loading volume and deleting nrrd tmp file
    allen_vol, header = nrrd.read(nrrd_file)
    os.remove(nrrd_file)

    # Transforming manually to RAS+
    allen_vol = np.moveaxis(allen_vol, (0, 1, 2), (1, 2, 0))
    allen_vol = np.flip(allen_vol, axis=2)
    allen_vol = np.flip(allen_vol, axis=1)

    # Scale to AGVT
    affine = np.eye(4) * avgt_r_mm

    # Loading allen volume and converting both arrays to float32
    avgt_vol = nib.load(avgt_file).get_fdata().astype(np.float32)
    allen_vol = allen_vol.astype(np.float32)

    # Creating and reshaping ANTsPyx images for registration
    # Moving : Allen volume
    # Fixed : AVGT volume
    fixed = ants.from_numpy(avgt_vol).resample_image((164, 212, 158), 1, 0)
    moving = ants.from_numpy(allen_vol).resample_image((164, 212, 158), 1, 0)

    # Loading pre-calculated transformations (ANTsPyx registration)
    transformations = [f'./utils/transformations_allen2avgt/allen2avgt_{args.res}.nii.gz',
                       f'./utils/transformations_allen2avgt/allen2avgtAffine_{args.res}.mat']

    # Applying thoses transformations
    warped_moving = ants.apply_transforms(fixed=fixed,  moving=moving,
                                          transformlist=transformations,
                                          interpolator=interp)

    # Applying a translation to Allen volume (Same origin as AGVT in MI-Brain)
    affine[:, 3] = affine[:, 3] + avgt_offset

    # Converting the warped volume to numpy array
    warped_vol = warped_moving.numpy()

    # Deleting negatives values if bSpline method was used (--smooth)
    if args.smooth:
        negatives_values = warped_vol < 0
        warped_vol[negatives_values] = 0

    # Creating and Saving the Nifti volume
    img = nib.Nifti1Image(warped_vol, affine)
    nib.save(img, nifti_file)


if __name__ == "__main__":
    main()

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
    p.add_argument('-c', '--nocache', action="store_true",
                   help='Update the Allen Mouse Brain Connectivity Cache')
    p.add_argument('--roi', action='store_true',
                   help='Generate a additionnal Nifti file containing\n'
                        'a spherical mask at the injection centroid of the experiment.')
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

    if os.path.isfile(experiments_path) and os.path.isfile(manifest_path) and args.nocache:
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
    string: R or L
    list: coordinates of the injection centroid
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
                                                          injection_fraction=frac_vol,
                                                          resolution=100)

    # Defining the Left-Right limit (+z axis)
    # Note: the bounding box is [13200, 8000, 11400]
    limit_LR = 11400/2
    is_right = injection_centroid[2] >= limit_LR

    # Returning the position and its location
    if is_right:
        return 'R', injection_centroid
    else:
        return 'L', injection_centroid


def pretransform_PIR_to_RAS(vol):
    """
    Manually transform a PIR reference space to RAS+.

    Parameters
    ----------
    vol: ndarray
        PIR volume to transform.

    Return
    ------
    ndarray: vol
        Transformed volume into RAS+
    """
    # Switching axis
    # +x, +y, +z (RAS) -> +z, -x, -y (PIR)
    vol = np.moveaxis(vol, (0, 1, 2), (1, 2, 0))
    vol = np.flip(vol, axis=2)
    vol = np.flip(vol, axis=1)

    return vol


def registrate_allen2avgt_ants(args, allen_vol, avgt_vol):
    """
    Align a 3D allen volume on AVGT.
    Using ANTsPyX registration.

    Parameters
    ----------
    args: argparse namespace
        Argument list.
    allen_vol: float32 ndarray
        Allen volume to registrate
    avgt_vol: float32 ndarray
        AVGT reference volume

    Return
    ------
    ndarray: Warped volume.
    """
    # Creating and reshaping ANTsPyx images for registration
    # Moving : Allen volume
    # Fixed : AVGT volume
    fixed = ants.from_numpy(avgt_vol).resample_image((164, 212, 158), 1, 0)
    moving = ants.from_numpy(allen_vol).resample_image((164, 212, 158), 1, 0)

    # Loading pre-calculated transformations (ANTsPyx registration)
    transformations = [f'./utils/transformations_allen2avgt/allen2avgt_{args.res}.nii.gz',
                       f'./utils/transformations_allen2avgt/allen2avgtAffine_{args.res}.mat']

    # Applying thoses transformations
    interp = 'nearestNeighbor'
    if args.smooth:
        interp = 'bSpline'

    warped_moving = ants.apply_transforms(fixed=fixed,  moving=moving,
                                          transformlist=transformations,
                                          interpolator=interp)

    return warped_moving.numpy()


def draw_spherical_mask(shape, radius, center):
    """
    Generate an n-dimensional spherical mask.

    Parameters
    ----------
    shape: tuple
        Shape of the volume created.
    radius: int/float
        Radius of the spherical mask.
    center: tuple
        Position of the center of the spherical mask.

    Return
    ------
    ndarray: Volume containing the spherical mask.
    """
    # Assuming shape and center have the same length and contain ints
    # (the units are pixels / voxels (px for short),
    # radius is a int or float in px)
    assert len(center) == len(shape)
    semisizes = (radius,) * len(shape)

    # Generating the grid for the support points
    # centered at the position indicated by center
    grid = [slice(-x0, dim - x0) for x0, dim in zip(center, shape)]
    center = np.ogrid[grid]

    # Calculating the distance of all points from center
    # scaled by the radius
    vol = np.zeros(shape, dtype=float)
    for x_i, semisize in zip(center, semisizes):
        vol += (x_i / semisize) ** 2

    # the inner part of the sphere will have distance below or equal to 1
    return vol <= 1.0


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
    loc = loc_injection_centroid(args)[0]

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
    if args.smooth:
        nifti_file = args.dir / f"{args.id}_{roi}_{loc}_proj_density_{args.res}_bSpline.nii.gz"
    roi_file = args.dir / f"{args.id}_{roi}_{loc}_spherical_mask_{args.res}.nii.gz"

    # Verifying if outputs already exist
    check_file_exists(parser, args, nifti_file)
    check_file_exists(parser, args, roi_file)

    # Downloading projection density (API)
    mca.download_projection_density(nrrd_file, experiment_id=args.id, resolution=mca_res)

    # Loading volume and deleting nrrd tmp file
    allen_vol, header = nrrd.read(nrrd_file)
    os.remove(nrrd_file)

    # Transforming manually to RAS+
    allen_vol = pretransform_PIR_to_RAS(allen_vol)

    # Loading allen volume and converting both arrays to float32
    avgt_vol = nib.load(avgt_file).get_fdata().astype(np.float32)
    allen_vol = allen_vol.astype(np.float32)

    # Applying ANTsPyX registration
    warped_vol = registrate_allen2avgt_ants(args=args, allen_vol=allen_vol, avgt_vol=avgt_vol)

    # Creating affine matrix to match AVGT position and scale in MI-Brain
    affine = np.eye(4) * avgt_r_mm
    affine[:, 3] = affine[:, 3] + avgt_offset

    # Deleting negatives values if bSpline method was used (--smooth)
    if args.smooth:
        warped_vol[warped_vol < 0] = 0

    # Creating and Saving the Nifti volume
    img = nib.Nifti1Image(warped_vol, affine)
    nib.save(img, nifti_file)

    # Creating and Saving the spherical mask if --roi was used
    if args.roi:
        # Converting the coordinates in voxels depending the resolution
        inj_centroid_um = loc_injection_centroid(args)[1]
        inj_centroid_voxels = (inj_centroid_um[0]/args.res,
                               inj_centroid_um[1]/args.res,
                               inj_centroid_um[2]/args.res)

        # Configuring the bounding box
        bbox_allen = (13200//args.res, 8000//args.res, 11400//args.res)

        # Drawing the spherical mask
        roi_sphere_allen = draw_spherical_mask(shape=bbox_allen, center=inj_centroid_voxels,
                                               radius=400//args.res).astype(np.float32)

        # Transforming manually to RAS+
        roi_sphere_allen = pretransform_PIR_to_RAS(roi_sphere_allen)

        # Applying ANTsPyX registration
        roi_sphere_avgt = registrate_allen2avgt_ants(args=args, allen_vol=roi_sphere_allen,
                                                     avgt_vol=avgt_vol)

        # Deleting non needed interpolated values
        roi_sphere_avgt = (roi_sphere_avgt >= 1).astype(np.int32)

        # Creating and Saving the Nifti spherical mask
        sphere = nib.Nifti1Image(roi_sphere_avgt, affine)
        nib.save(sphere, roi_file)


if __name__ == "__main__":
    main()

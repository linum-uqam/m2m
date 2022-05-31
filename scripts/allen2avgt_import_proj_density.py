#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    Import a projection density map of an experiment in the
    Allen Mouse Brain Connectivity Atlas and align it on the Average Template.

    >>> python allen2avgt_import_proj_density.py id --map
    >>> python allen2avgt_import_proj_density.py id --map -r res --dir dir
    >>> python allen2avgt_import_proj_density.py id --map --smooth

    Download a spherical roi mask located at the injection centroid of an
    experiment in the Allen Mouse Brain Connectivity Atlas and
    align it on the Average Template.

    >>> python allen2avgt_import_proj_density.py id --roi
    >>> python allen2avgt_import_proj_density.py id --roi -r res --dir dir

    Save experiment injection coordinates (Allen and MI-Brain) in a json file.

"""

import argparse
from email.policy import default
import json
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
                   help='Experiment id in the Allen Mouse Brain '
                        'Connectivity Atlas dataset.')
    p.add_argument('-r', '--res', type=int, default=100, choices=[25, 50, 100],
                   help='Resolution of the downloaded projection density '
                        'is 100µm by default.\n'
                        'Using -r <value> will set the resolution to value.')
    p.add_argument('-d', '--dir', default=".",
                   help='Path of the ouptut file directory is . by default.\n'
                        'Using --dir <dir> will change the output file\'s '
                        'directory or create a new one if does not exits.')
    p.add_argument('--map', action='store_true',
                   help='Using --map will download a Nifti file containing '
                        'the projeciton density of the experiment.')
    p.add_argument('--smooth', action="store_true",
                   help='Interpolation method for the registration '
                        'is nearestNeighbor by default.\n'
                        'Using --smooth will change the method to bSpline.')
    p.add_argument('--roi', action='store_true',
                   help='Using --map will download a Nifti file containing '
                        'a spherical mask at the injection centroid\n'
                        'of the experiment.')
    p.add_argument('-f', dest='overwrite', action="store_true",
                   help='Force overwriting of the output file.')
    p.add_argument('-c', '--nocache', action="store_true",
                   help='Update the Allen Mouse Brain Connectivity Cache')
    return p


def check_id(parser, args):
    """
    Verify if the experiment id is part of the
    Allen Mouse Brain Connectivity Atlas.

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

    if args.nocache:
        if os.path.isfile(experiments_path) and os.path.isfile(manifest_path):
            os.remove(experiments_path)
            os.remove(manifest_path)

    mcc = MouseConnectivityCache(manifest_file=manifest_path)
    ids = mcc.get_experiments(dataframe=True, file_name=experiments_path).id
    if args.id not in ids:
        parser.error("This experiment id doesn't exist. \n"
                     "Please check : https://connectivity.brain-map.org/")


def check_args(parser, args):
    """
    Verify that the arguments are called the right way

    Parameters
    ----------
    parser: argparse.ArgumentParser object
        Parser.
    args: argparse namespace
        Argument list.
    """
    if not args.map and not args.roi:
        parser.error("Please precise the file to download. \n"
                     "Use --map to download the projection density map.\n"
                     "Use --roi to download the spherical roi mask.")


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
    Return the position of the injection centroid in the Mouse Brain.
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
    allen_logger = 'allensdk.api.api.retrieve_file_over_http'

    # Disabling the download logger.
    logging.getLogger(allen_logger).disabled = True

    # Downloading the injection fraction and density of the experiment
    injection_density = mca.download_injection_density(path_density,
                                                       experiment_id=args.id,
                                                       resolution=100)
    injection_fraction = mca.download_injection_fraction(path_fraction,
                                                         experiment_id=args.id,
                                                         resolution=100)

    # Re-enabling the logger
    logging.getLogger(allen_logger).disabled = False

    # Loading the volumes
    dens_vol, header = nrrd.read(path_density)
    frac_vol, header = nrrd.read(path_fraction)

    # Removing tmp files
    os.remove(path_density)
    os.remove(path_fraction)

    # Downloading the injection centroid
    injection_centroid = mca.calculate_injection_centroid(
        injection_density=dens_vol,
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


def get_mib_coords(args):
    """
    Get MI-Brain voxels coords
    of the experiment injection centroid.

    Parameters
    ----------
    args: argparse namespace
        Argument list.

    Return
    ------
    list: MI-Brain coords
    """
    # Loading transform matrix
    file_mat = f'./utils/transformations_allen2avgt/allen2avgtAffine_{args.res}.mat'

    # Defining invert transformation
    itx = ants.read_transform(file_mat).invert()

    # Converting injection centroid position to voxels
    allen_pir_um = loc_injection_centroid(args)[1]
    allen_pir_vox = [allen_pir_um[0]/args.res, allen_pir_um[1]/args.res,
                     allen_pir_um[2]/args.res]

    # Converting injection centroid voxels position to ras
    p, i, r = 13200//args.res, 8000//args.res, 11400//args.res
    x, y, z = allen_pir_vox[0], allen_pir_vox[1], allen_pir_vox[2]
    x_, y_, z_ = z, p-x, i-y
    allen_ras_vox = [x_, y_, z_]

    # Converting injection centroid voxels ras position to mi-brain voxels
    mib_vox = itx.apply_to_point(allen_ras_vox)

    return mib_vox


def save_mib_coords(dic, path):
    """
    Saving MI-brain injection centroid coords
    in a json file

    Parameters
    ----------
    dic: dictionnary
        Json content.
    path: string or path to file
        Path to the output file.
    """
    # Saving into json file
    json_object = json.dumps(dic, indent=4)
    with open(path, "w") as outfile:
        outfile.write(json_object)


def main():
    # Building argparser
    parser = _build_arg_parser()
    args = parser.parse_args()

    # Verifying arguments
    check_args(parser, args)

    # Verifying experiment id
    check_id(parser, args)

    # Configuring output directory
    args.dir = Path(args.dir)
    args.dir.mkdir(exist_ok=True, parents=True)

    # AVGT settings
    avgt_file = './utils/AVGT.nii.gz'
    avgt_affine = nib.load(avgt_file).affine
    avgt_vol = nib.load(avgt_file).get_fdata().astype(np.float32)

    mca = MouseConnectivityApi()

    # Experiment infos
    roi = pd.DataFrame(mca.get_experiment_detail(args.id)).specimen[0]['stereotaxic_injections'][0]['primary_injection_structure']['acronym']
    loc = loc_injection_centroid(args)[0]
    pos = loc_injection_centroid(args)[1]

    # Creating and Saving MI-brain injection centroid coords in json file

    # Configuring file name
    coords_file = args.dir / f"{args.id}_{roi}_{loc}_inj_centroid_coords_{args.res}.json"

    # Verifying if file already exist
    check_file_exists(parser, args, coords_file)

    # Getting mi-brain voxel coordinates
    mib_coords = get_mib_coords(args)

    # Creating json content
    dic = {"id": args.id, "roi": roi, "location": loc,
           "allen_micron": pos.tolist(), "mibrain_voxels": mib_coords}

    # Saving in json file
    save_mib_coords(dic, coords_file)

    # Choosing the downloaded resolution
    if args.res == 100:
        mca_res = mca.VOXEL_RESOLUTION_100_MICRONS
    elif args.res == 50:
        mca_res = mca.VOXEL_RESOLUTION_50_MICRONS
    elif args.res == 25:
        mca_res = mca.VOXEL_RESOLUTION_25_MICRONS

    # Downloading and Saving the projection density map if --map was used
    if args.map:
        # Configuring files names
        nrrd_file = args.dir / f"{args.id}_{roi}_{loc}_proj_density_{args.res}.nrrd"
        nifti_file = args.dir / f"{args.id}_{roi}_{loc}_proj_density_{args.res}.nii.gz"
        if args.smooth:
            nifti_file = args.dir / f"{args.id}_{roi}_{loc}_proj_density_{args.res}_bSpline.nii.gz"

        # Verifying if output already exist
        check_file_exists(parser, args, nifti_file)

        # Downloading projection density (API)
        mca.download_projection_density(
            nrrd_file,
            experiment_id=args.id,
            resolution=mca_res)

        # Loading volume and deleting nrrd tmp file
        allen_vol, header = nrrd.read(nrrd_file)
        os.remove(nrrd_file)

        # Transforming manually to RAS+
        allen_vol = pretransform_PIR_to_RAS(allen_vol)

        # Loading allen volume converting to float32
        allen_vol = allen_vol.astype(np.float32)

        # Applying ANTsPyX registration
        warped_vol = registrate_allen2avgt_ants(
            args=args,
            allen_vol=allen_vol,
            avgt_vol=avgt_vol)

        # Deleting negatives values if bSpline method was used (--smooth)
        if args.smooth:
            warped_vol[warped_vol < 0] = 0

        # Creating and Saving the Nifti volume
        img = nib.Nifti1Image(warped_vol, avgt_affine)
        nib.save(img, nifti_file)

    # Creating and Saving the spherical mask if --roi was used
    if args.roi:
        # Configuring file name
        roi_file = args.dir / f"{args.id}_{roi}_{loc}_spherical_mask_{args.res}.nii.gz"

        # Verifying if output already exist
        check_file_exists(parser, args, roi_file)

        # Converting the coordinates in voxels depending the resolution
        inj_centroid_um = loc_injection_centroid(args)[1]
        inj_centroid_voxels = (inj_centroid_um[0]/args.res,
                               inj_centroid_um[1]/args.res,
                               inj_centroid_um[2]/args.res)

        # Configuring the bounding box
        bbox_allen = (13200//args.res, 8000//args.res, 11400//args.res)

        # Drawing the spherical mask
        roi_sphere_allen = draw_spherical_mask(
            shape=bbox_allen,
            center=inj_centroid_voxels,
            radius=400//args.res).astype(np.float32)

        # Transforming manually to RAS+
        roi_sphere_allen = pretransform_PIR_to_RAS(roi_sphere_allen)

        # Applying ANTsPyX registration
        roi_sphere_avgt = registrate_allen2avgt_ants(
            args=args,
            allen_vol=roi_sphere_allen,
            avgt_vol=avgt_vol)

        # Deleting non needed interpolated values
        roi_sphere_avgt = roi_sphere_avgt.astype(np.int32)

        # Creating and Saving the Nifti spherical mask
        sphere = nib.Nifti1Image(roi_sphere_avgt, avgt_affine)
        nib.save(sphere, roi_file)


if __name__ == "__main__":
    main()

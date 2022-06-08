#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    Import a projection density map of an experiment in the
    Allen Mouse Brain Connectivity Atlas and align it on the Average Template.

    >>> python allen2avgt_import_proj_density.py id --map
    >>> python allen2avgt_import_proj_density.py id --map -r res --dir dir
    >>> python allen2avgt_import_proj_density.py id --map --smooth

    Download a spherical roi mask located at the injection coordinates of an
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
from re import A
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
                        'a spherical mask at the injection coordinates\n'
                        'of the experiment.')
    p.add_argument('-f', dest='overwrite', action="store_true",
                   help='Force overwriting of the output file.')
    p.add_argument('-c', '--nocache', action="store_true",
                   help='Update the Allen Mouse Brain Connectivity Cache')
    return p


def get_mcc(args):
    """
    Get Allen Mouse Connectivity Cache.\n
    Update it by removing and downloading cache file
    using --nocache.

    Parameters
    ----------
    args: argparse namespace
        Argument list.

    Return
    ------
    dataframe : Allen Mouse Connectivity experiments
    """
    experiments_path = './utils/cache/allen_mouse_conn_experiments.json'
    manifest_path = './utils/cache/mouse_conn_manifest.json'

    if args.nocache:
        if os.path.isfile(experiments_path) and os.path.isfile(manifest_path):
            os.remove(experiments_path)
            os.remove(manifest_path)

    mcc = MouseConnectivityCache(manifest_file=manifest_path)
    experiments = mcc.get_experiments(dataframe=True,
                                      file_name=experiments_path)

    return pd.DataFrame(experiments)


def check_id(parser, args, allen_experiments):
    """
    Verify if the experiment id is part of the
    Allen Mouse Brain Connectivity Atlas.

    Read all experiments ids from the Allen Mouse Brain Connectivity Cache.\n
    Download the Cache files if does not exist or --cache used.

    Parameters
    ----------
    parser: argparse.ArgumentParser object
        Parser.
    args: argparse namespace
        Argument list.
    experiments : dataframe
        Allen Mouse Connectivity experiments.
    """
    ids = allen_experiments.id

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


def loc_injection_coordinates(args, allen_experiments):
    """
    Return the injection coordinates of
    an experiment and its position.

    Parameters
    ----------
    args: argparse namespace
        Argument list.
    experiments : dataframe
        Allen Mouse Connectivity experiments

    Return
    ------
    string: R or L
    list: coordinates of the injection coordinates
    """
    inj_coord = allen_experiments.loc[args.id]['injection-coordinates']

    # Returning the position and its location
    # Right is >= than z/2
    if inj_coord[2] >= 11400/2:
        return 'R', inj_coord
    else:
        return 'L', inj_coord


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
    tx_nifti = './utils/transformations_allen2avgt/allen2avgt_{}.nii.gz'
    tx_mat = './utils/transformations_allen2avgt/allen2avgtAffine_{}.mat'
    transformations = [tx_nifti.format(args.res),
                       tx_mat.format(args.res)]

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


def get_mib_coords(args, allen_experiments):
    """
    Get MI-Brain voxels coords
    of the experiment injection coordinates.

    Parameters
    ----------
    args: argparse namespace
        Argument list.

    Return
    ------
    list: MI-Brain coords
    """
    # Loading transform matrix
    tx_mat = './utils/transformations_allen2avgt/allen2avgtAffine_{}.mat'
    file_mat = tx_mat.format(args.res)

    # Defining invert transformation
    itx = ants.read_transform(file_mat).invert()

    # Converting injection coordinates position to voxels
    allen_pir_um = loc_injection_coordinates(args, allen_experiments)[1]
    allen_pir_vox = [allen_pir_um[0]/args.res, allen_pir_um[1]/args.res,
                     allen_pir_um[2]/args.res]

    # Converting injection coordinates voxels position to ras
    p, i, r = 13200//args.res, 8000//args.res, 11400//args.res
    x, y, z = allen_pir_vox[0], allen_pir_vox[1], allen_pir_vox[2]
    x_, y_, z_ = z, p-x, i-y
    allen_ras_vox = [x_, y_, z_]

    # Converting injection coordinates voxels ras position to mi-brain voxels
    mib_vox = itx.apply_to_point(allen_ras_vox)

    return mib_vox


def save_mib_coords(dic, path):
    """
    Saving MI-brain injection coordinates coords
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

    # Mouse Connectivity settings
    # API
    mca = MouseConnectivityApi()
    # experiments from Cache
    allen_experiments = get_mcc(args)

    # Verifying arguments
    check_args(parser, args)

    # Verifying experiment id
    check_id(parser, args, allen_experiments)

    # Configuring output directory
    args.dir = Path(args.dir)
    args.dir.mkdir(exist_ok=True, parents=True)

    # AVGT settings
    avgt_file = './utils/AVGT.nii.gz'
    avgt_affine = nib.load(avgt_file).affine
    avgt_vol = nib.load(avgt_file).get_fdata().astype(np.float32)

    # Experiment infos
    roi = allen_experiments.loc[args.id]['structure-abbrev']
    loc = loc_injection_coordinates(args, allen_experiments)[0]
    pos = loc_injection_coordinates(args, allen_experiments)[1]

    # Creating and Saving MI-brain injection coordinates coords in json file

    # Configuring file name
    json_ = "{}_{}_{}_inj_coords_{}.json"
    coords_file = args.dir / json_.format(args.id, roi, loc, args.res)

    # Verifying if file already exist
    check_file_exists(parser, args, coords_file)

    # Getting mi-brain voxel coordinates
    mib_coords = get_mib_coords(args, allen_experiments)

    # Creating json content
    dic = {"id": args.id, "roi": roi, "location": loc,
           "allen_micron": pos, "mibrain_voxels": mib_coords}

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
        nrrd_ = "{}_{}_{}_proj_density_{}.nrrd"
        nifti_ = "{}_{}_{}_proj_density_{}.nii.gz"
        smooth_ = "{}_{}_{}_proj_density_{}_bSpline.nii.gz"

        nrrd_file = args.dir / nrrd_.format(args.id, roi, loc, args.res)
        nifti_file = args.dir / nifti_.format(args.id, roi, loc, args.res)
        if args.smooth:
            nifti_file = args.dir / smooth_.format(args.id, roi, loc, args.res)

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
        roi_ = "{}_{}_{}_spherical_mask_{}.nii.gz"

        roi_file = args.dir / roi_.format(args.id, roi, loc, args.res)

        # Verifying if output already exist
        check_file_exists(parser, args, roi_file)

        # Converting the coordinates in voxels depending the resolution
        inj_coord_um = loc_injection_coordinates(args, allen_experiments)[1]
        inj_coord_voxels = (inj_coord_um[0]/args.res,
                            inj_coord_um[1]/args.res,
                            inj_coord_um[2]/args.res)

        # Configuring the bounding box
        bbox_allen = (13200//args.res, 8000//args.res, 11400//args.res)

        # Drawing the spherical mask
        roi_sphere_allen = draw_spherical_mask(
            shape=bbox_allen,
            center=inj_coord_voxels,
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

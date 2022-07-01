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

    >>> python allen2avgt_import_proj_density.py id --infos
    >>> python allen2avgt_import_proj_density.py id --infos --dir dir

    Save a binarised projection density map.

    >>> python allen2avgt_import_proj_density.py id --bin --threshold
    >>> python allen2avgt_import_proj_density.py id --bin --threshold --res r

    . . .
"""

import argparse
import json
import logging

import os
from pathlib import Path

import numpy as np

from allensdk.api.queries.mouse_connectivity_api import MouseConnectivityApi
import nrrd

import sys
sys.path.append(".")

from allen2tract.control import (add_cache_arg, add_output_dir_arg,
                                 add_overwrite_arg, add_resolution_arg,
                                 check_file_exists)

from allen2tract.transform import (pretransform_vol_PIR_RAS,
                                   registrate_allen2avgt_ants,
                                   get_mib_coords)

from allen2tract.util import (get_injection_infos,
                              get_mcc,
                              draw_spherical_mask,
                              save_nii)

EPILOG = """
Author : Mahdi
"""


def _build_arg_parser():
    p = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter,
                                epilog=EPILOG, description=__doc__)
    p.add_argument('id', type=int,
                   help='Experiment id in the Allen Mouse Brain '
                        'Connectivity Atlas dataset.')
    p.add_argument('--map', action='store_true',
                   help='Save the projeciton density map of the experiment.\n'
                        '(.nii.gz)')
    p.add_argument('--smooth', action="store_true",
                   help='Interpolation method for the registration '
                        'is nearestNeighbor by default.\n'
                        'Using --smooth will change the method to bSpline.')
    p.add_argument('--roi', action='store_true',
                   help='Save a spherical mask at the injection coordinates\n'
                        'of the experiment. (.nii.gz)')
    p.add_argument('--bin', action="store_true",
                   help='Binarise the projection density map (.nii.gz)'
                        'with a certain --threshold.')
    p.add_argument('--threshold', type=float, default=.5,
                   help='Treshold for the binarised map.')
    p.add_argument('--infos', action="store_true",
                   help='Save informations about the experiment:\n'
                        '- Injeciton coordinates (MI-Brain, Allen)\n'
                        '- Hemisphere (L or R)\n'
                        '- Injeciton ROI\n')
    add_resolution_arg(p)
    add_output_dir_arg(p)
    add_cache_arg(p)
    add_overwrite_arg(p)
    return p


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
    if not args.map and not args.roi and not args.infos and not args.bin:
        parser.error("Please precise the file to download. \n"
                     "Use --map to download the projection density map.\n"
                     "Use --roi to download the spherical roi mask.\n"
                     "User --infos to download the experiment infos.\n"
                     "Use --bin to download the binarised map.")


def main():
    # Building argparser
    parser = _build_arg_parser()
    args = parser.parse_args()

    # Mouse Connectivity settings
    # API
    mca = MouseConnectivityApi()
    # experiments from Cache
    allen_experiments = get_mcc(args)[0]

    # Verifying arguments
    check_args(parser, args)

    # Verifying experiment id
    ids = allen_experiments.id

    if args.id not in ids:
        parser.error("This experiment id doesn't exist. \n"
                     "Please check : https://connectivity.brain-map.org/")

    # Configuring output directory
    args.dir = Path(args.dir)
    args.dir.mkdir(exist_ok=True, parents=True)

    # Experiment infos
    # injection region, location, position (inj_coords_um)
    roi = get_injection_infos(allen_experiments, args.id)[0]
    loc = get_injection_infos(allen_experiments, args.id)[2]
    pos = get_injection_infos(allen_experiments, args.id)[1]

    # Creating and Saving MI-brain injection coordinates coords in json file

    # Saving experiments infos if --infos was used
    if args.infos:
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
        json_object = json.dumps(dic, indent=4)
        with open(coords_file, "w") as outfile:
            outfile.write(json_object)

    # Downloading and Saving the projection density map if --map was used
    if args.map or args.bin:
        # Configuring files names
        nrrd_ = "{}_{}_{}_proj_density_{}.nrrd"
        nifti_ = "{}_{}_{}_proj_density_{}.nii.gz"
        smooth_ = "{}_{}_{}_proj_density_{}_bSpline.nii.gz"
        bin_ = "{}_{}_{}_proj_density_{}_bin{}.nii.gz"

        nrrd_file = args.dir / nrrd_.format(args.id, roi, loc, args.res)
        nifti_file = args.dir / nifti_.format(args.id, roi, loc, args.res)
        if args.smooth:
            nifti_file = args.dir / smooth_.format(args.id, roi, loc, args.res)
        if args.bin:
            bin_file = args.dir / bin_.format(args.id, roi, loc, args.res,
                                              args.threshold)
            check_file_exists(parser, args, bin_file)

        # Verifying if output already exist
        check_file_exists(parser, args, nifti_file)

        # Downloading projection density (API)
        mca.download_projection_density(
            nrrd_file,
            experiment_id=args.id,
            resolution=args.res)

        # Loading volume and deleting nrrd tmp file
        allen_vol, header = nrrd.read(nrrd_file)
        os.remove(nrrd_file)

        # Transforming manually to RAS+
        allen_vol = pretransform_vol_PIR_RAS(allen_vol)

        # Loading allen volume converting to float32
        allen_vol = allen_vol.astype(np.float32)

        # Applying ANTsPyX registration
        warped_vol = registrate_allen2avgt_ants(
            res=args.res,
            allen_vol=allen_vol,
            smooth=args.smooth)

        # Deleting negatives values if bSpline method was used (--smooth)
        if args.smooth:
            warped_vol[warped_vol < 0] = 0

        if args.map:
            # Creating and Saving the Nifti map
            save_nii(warped_vol, nifti_file)

        if args.bin:
            # Creating and Saving the Nifti bin map
            bin_vol = (warped_vol >= args.threshold).astype(np.int32)
            save_nii(bin_vol, bin_file)

    # Creating and Saving the spherical mask if --roi was used
    if args.roi:
        # Configuring file name
        roi_ = "{}_{}_{}_spherical_mask_{}.nii.gz"

        roi_file = args.dir / roi_.format(args.id, roi, loc, args.res)

        # Verifying if output already exist
        check_file_exists(parser, args, roi_file)

        # Converting the coordinates in voxels depending the resolution
        inj_coord_voxels = (pos[0]/args.res,
                            pos[1]/args.res,
                            pos[2]/args.res)

        # Configuring the bounding box
        bbox_allen = (13200//args.res, 8000//args.res, 11400//args.res)

        # Drawing the spherical mask
        roi_sphere_allen = draw_spherical_mask(
            shape=bbox_allen,
            center=inj_coord_voxels,
            radius=400//args.res).astype(np.float32)

        # Transforming manually to RAS+
        roi_sphere_allen = pretransform_vol_PIR_RAS(roi_sphere_allen)

        # Applying ANTsPyX registration
        roi_sphere_avgt = registrate_allen2avgt_ants(
            res=args.res,
            allen_vol=roi_sphere_allen,
            smooth=args.smooth)

        # Deleting non needed interpolated values
        roi_sphere_avgt = roi_sphere_avgt.astype(np.int32)

        # Creating and Saving the Nifti spherical mask
        save_nii(roi_sphere_avgt, roi_file)


if __name__ == "__main__":
    main()
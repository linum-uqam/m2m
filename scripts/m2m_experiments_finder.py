#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    Find Allen Mouse Brain Connectivity (AMBCA) experiments.

    Experiments are searched in the AMBCA Dataset
    giving a set of User Data Space (UDS) voxel coordinates [x, y, z].\n

    Important: Select the same resolution as your matrix
    We higly recommend to work with high resolution (starting from 50)
    in order to search experiments more precisely.\n

    Examples:
    ---------
    Generate projection density maps for each experiment.\n
    Maps are downloaded from the AMBCA API.\n

    All files are stored in a same folder.\n

    Injection coordinate search: (--injection)

    >>> m2m_experiments_finder.py path/to/.mat path/to/ref.nii.gz
        resolution x y z --injection --nb_of_exps n

    Spatial search: (--spatial):

    >>> m2m_experiments_finder.py path/to/.mat path/to/ref.nii.gz
        resolution x y z --injection --nb_of_exps n
"""

import argparse
import sys
from pathlib import Path

import numpy as np

from m2m.allensdk_utils import (download_proj_density_vol,
                                get_injection_infos,
                                get_mcc_exps,
                                get_mcc_stree,
                                search_experiments)
from m2m.control import (add_cache_arg,
                         add_output_dir_arg,
                         add_overwrite_arg,
                         add_resolution_arg,
                         check_file_exists,
                         add_matrix_arg,
                         add_reference_arg,
                         check_input_file)
from m2m.transform import (pretransform_vol_PIR_UserDataSpace,
                           registrate_allen2UserDataSpace,
                           get_allen_coords)
from m2m.util import (save_nifti,
                      load_user_template)

EPILOG = """
Author : Mahdi
"""


def _build_arg_parser():
    p = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter,
                                epilog=EPILOG, description=__doc__)
    add_matrix_arg(p)
    add_reference_arg(p)
    p.add_argument('x', type=int,
                   help='X-component of UDS voxel coordinates')
    p.add_argument('y', type=int,
                   help='Y-component of UDS voxel coordinates')
    p.add_argument('z', type=int,
                   help='Y-component of UDS voxel coordinates')
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument('--injection', action="store_true",
                   help='Use `experiment_injection_coordinate_search` '
                        'to find experiments.\n'
                        'https://allensdk.readthedocs.io/en/latest/'
                        'allensdk.api.queries.mouse_connectivity_api.html')
    g.add_argument('--spatial', action="store_true",
                   help='Use `experiment_spatial_search` '
                        'to find experiments.\n'
                        'https://allensdk.readthedocs.io/en/latest/'
                        'allensdk.api.queries.mouse_connectivity_api.html')
    p.add_argument('--nb_of_exps', type=int, default=1,
                   help='Number of experiments needed. 1 by default.')
    add_resolution_arg(p)
    add_output_dir_arg(p)
    add_cache_arg(p)
    add_overwrite_arg(p)
    return p


def check_coords_in_bbox(parser, args):
    """
    Verify that the provided coordinates are within the reference
    volume bounding box.

    Parameters
    ----------
    parser: argparse.ArgumentParser object
        Parser.
    args: argparse namespace
        Argument list.
    """
    # Load the reference
    reference = load_user_template(args.reference)

    # Verifying coords
    x, y, z = range(0, reference.shape[0]), range(0, reference.shape[1]), range(0, reference.shape[2])
    if args.x not in x or \
            args.y not in y or \
            args.z not in z:
        parser.error('Invalid red coordinates'
                     f'x, y, z values must be in {reference.shape} at {args.res} microns')


def main():
    # Building argparser
    parser = _build_arg_parser()
    args = parser.parse_args()

    # Loading reference
    check_input_file(parser, args.reference)
    if not (args.reference).endswith(".nii") and \
            not (args.reference).endswith(".nii.gz"):
        parser.error("reference must be a nifti file.")
    user_vol = load_user_template(args.reference)

    # Checking that the coords are in the bounding box
    check_coords_in_bbox(parser, args)

    # Checking file mat
    check_input_file(parser, args.file_mat)

    # Getting experiments from Mouse Connectivity Cache
    allen_experiments = get_mcc_exps(args.nocache)

    # Configuring output directory
    args.dir = Path(args.dir)
    args.dir.mkdir(exist_ok=True, parents=True)

    # Creating UDS vector coords
    uds_coords = [args.x, args.y, args.z]

    # Getting Allen coords
    allen_coords = get_allen_coords(uds_coords, args.res,
                                    args.file_mat, user_vol)
    # Searching Allen experiments
    allen_exps = search_experiments(args.injection, args.spatial,
                                    allen_coords)

    # Checking if allen_exps is not empty
    if len(allen_exps) == 0:
        sys.exit("No experiment founded for [{},{},{}]".format(args.x, args.y, args.z))

    # Checking if there are enough allen_exps compared to the nb_of_exps needed
    if args.nb_of_exps > 1:
        if len(allen_exps) < args.nb_of_exps:
            print("Only {} experiments founded at [{},{},{}],"
                  "processing...".format(len(allen_exps), args.x, args.y, args.z))

            # Resetting the number of experiments needed to the total number available
            nb_of_exps = len(allen_exps)

            # Retrieving experiments ids
            if nb_of_exps > 1:
                exps_ids = allen_exps[0:args.nb_of_exps-1]['id']
            else:
                exps_ids = allen_exps[0]['id']
    else:
        exps_ids = allen_exps[0]['id']
    exps_ids = [exps_ids]

    print("{} experiments founded, downloading...".format(exps_ids))

    # Preparing files names
    # Creating subdir
    if args.injection:
        method = "injected"
    if args.spatial:
        method = "with_high_signal"
    subdir_ = f"experiments_{method}_at_{args.x}_{args.y}_{args.z}_at_{args.res}_microns"
    subdir = Path(args.dir / subdir_)
    subdir.mkdir(exist_ok=True, parents=True)

    # Iterating on each experiments
    for id in exps_ids:

        # Retrieving experiment information
        roi = get_injection_infos(allen_experiments, id)[0]
        loc = get_injection_infos(allen_experiments, id)[2]

        # Projection density maps Niftis and Nrrd files
        nrrd_file = "{}_{}.nrrd".format(id, args.res)
        nifti_file = subdir / "{}_{}_{}_proj_density_{}.nii.gz".format(id,
                                                              roi, loc, args.res)
        check_file_exists(parser, args, nifti_file)

        # Downloading projection density maps
        exp_vol = download_proj_density_vol(nrrd_file, id,
                                            args.res, args.nocache)

        # Transforming manually to RAS+
        exp_vol = pretransform_vol_PIR_UserDataSpace(exp_vol, user_vol)

        # Converting Allen volumes to float32
        exp_vol = exp_vol.astype(np.float32)

        # Applying ANTsPyX registration
        warped_vol = registrate_allen2UserDataSpace(args.file_mat,
                                                    exp_vol, user_vol, allen_res=args.res)

        # Saving Niftis files
        save_nifti(warped_vol, user_vol.affine, nifti_file)


if __name__ == "__main__":
    main()

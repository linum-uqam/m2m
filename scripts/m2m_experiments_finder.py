#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    Find experiments in the Allen Mouse Brain Connectivity Atlas (AMBCA)
    dataset giving a set of User Data Space (UDS) voxel coordinates [x, y, z].\n

    The script then saves the experiment identifiers in a .csv file,
    which can be used as input for the "m2m_import_proj_density.py" script.\n

    Important: Select the same resolution as your matrix
    We higly recommend to work with high resolution (starting from 50)
    in order to search experiments more precisely.\n

    Example:
    --------
    1. Find experiments identifiers (a or b):
        a. Injection coordinate search: (--injection)
        >>> m2m_experiments_finder.py resolution path/to/.mat path/to/ref.nii.gz
            path/to/output.csv x y z --injection --nb_of_exps n

        b.Spatial search: (--spatial):
        >>> m2m_experiments_finder.py resolution path/to/.mat path/to/ref.nii.gz
            path/to/output.csv x y z --spatial --nb_of_exps n

    2. Call m2m_import_proj_density.py with theses indentifiers as an input:
       (see m2m_import_proj_density.py documentation)
"""

import argparse
import sys
from pathlib import Path

import csv

from m2m.allensdk_utils import search_experiments
from m2m.control import (add_cache_arg,
                         add_output_dir_arg,
                         add_overwrite_arg,
                         add_resolution_arg,
                         add_matrix_arg,
                         add_reference_arg,
                         check_file_exists,
                         check_input_file)
from m2m.transform import get_allen_coords
from m2m.util import load_user_template

EPILOG = """
Author : Mahdi
"""


def _build_arg_parser():
    p = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter,
                                epilog=EPILOG, description=__doc__)
    add_resolution_arg(p)
    add_matrix_arg(p)
    add_reference_arg(p)
    p.add_argument('out_csv', help='Path to output csv (.csv)')
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
        parser.error('Invalid coordinates '
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

    # Verifying output file
    check_file_exists(parser, args, args.out_csv)
    if not (args.out_csv).endswith(".csv"):
        parser.error("out_csv must be a csv file.")

    # Configuring output directory
    args.dir = Path(args.dir)
    args.dir.mkdir(exist_ok=True, parents=True)

    # Preparing file name
    csv_ = args.dir / args.out_csv

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
        sys.exit("No experiments found for [{},{},{}]".format(args.x, args.y, args.z))

    # Checking if there are enough allen_exps compared to the nb_of_exps needed
    if args.nb_of_exps > 1:
        if len(allen_exps) < args.nb_of_exps:
            print("Only {} experiments found at [{},{},{}], "
                  "processing...".format(len(allen_exps), args.x, args.y, args.z))

            # Resetting the number of experiments needed to the total number available
            nb_of_exps = len(allen_exps)

            # Retrieving experiments ids
            if nb_of_exps > 1:
                exps_ids = [allen_exps[i]['id'] for i in range(0, nb_of_exps)]
            else:
                exps_ids = [allen_exps[0]['id']]
        else:
            exps_ids = [allen_exps[i]['id'] for i in range(0, args.nb_of_exps)]
    else:
        exps_ids = [allen_exps[0]['id']]

    print("{} experiments found, saving ids...".format(len(exps_ids)))

    # Saving ids
    with open(csv_, 'w', newline='') as csv_file:
        writer = csv.writer(csv_file)

        # Write the header
        writer.writerow(['id'])

        # Write the data rows
        for id in exps_ids:
            writer.writerow([id])

    print('{} saved'.format(args.out_csv))


if __name__ == "__main__":
    main()

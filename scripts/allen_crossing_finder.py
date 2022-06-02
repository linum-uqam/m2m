#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
"""

import argparse
from email.policy import default
import json
import logging

import os
from pathlib import Path
import sys
from tabnanny import check

import numpy as np
import pandas as pd

from allensdk.api.queries.mouse_connectivity_api import MouseConnectivityApi
from allensdk.api.queries.reference_space_api import ReferenceSpaceApi
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
    p.add_argument('--red', nargs=3, type=int, required=True,
                   help='MI-Brain voxels coordinates of first experiment.\n'
                        'First experiment will be colored in red.')
    p.add_argument('--green', nargs=3, type=int, required=True,
                   help='MI-Brain voxels coordinates of second experiment.\n'
                        'Second experiment will be colored in green.')
    p.add_argument('--blue', nargs=3, type=int,
                   help='MI-Brain voxels coordinates of third experiment.\n'
                        'Third experiment will be colored in blue.')
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
    p.add_argument('--threshold', type=float, default=0.30,
                   help='Combined projection density threshold for finding '
                        'masks of crossing ROIs.\n'
                        'Threshold is 0.30 by default.\n'
                        '--threshold <value> will set threshold to value.')
    p.add_argument('-r', '--res', type=int, default=100, choices=[25, 50, 100],
                   help='Resolution of downloaded files is 100µm by default.\n'
                        '--res <value> will set the resolution to value.')
    p.add_argument('-d', '--dir', default=".",
                   help='Path of the ouptut file directory is . by default.\n'
                        '--dir <dir> will change the output file\'s '
                        'directory or create a new one if does not exits.')
    p.add_argument('-f', dest='overwrite', action="store_true",
                   help='Force overwriting of the output file.')
    p.add_argument('-c', '--nocache', action="store_true",
                   help='Update the Allen Mouse Brain Connectivity Cache')
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
    # Verifying threshold
    if 1.0 < args.threshold < 0.0:
        parser.error('Please enter a valid threshold value. '
                     'Pick a float value from 0.0 to 1.0')

    # Verifying coords
    x, y, z = range(0, 165), range(0, 213), range(0, 159)

    if args.red[0] not in x or args.red[1] not in y or args.red[2] not in z:
        parser.error('Red coords invalid. '
                     'x, y, z values must be in [164, 212, 158].')

    if args.green[0] not in x or args.green[1] not in y or args.green[2] not in z:
        parser.error('Green coords invalid. '
                     'x, y, z values must be in [164, 212, 158].')

    if args.blue:
        if args.blue[0] not in x or args.blue[1] not in y or args.blue[2] not in z:
            parser.error('Blue coords invalid. '
                         'x, y, z values must be in [164, 212, 158].')


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


def get_allen_coords(mib_coords, res=25):
    """
    Compute the Allen coordinates from
    MI-Brain coordinates.\n
    Resolution is fixed to 25 to ensure
    best precision.

    Parameters
    ----------
    args: argparse namespace
        Argument list.
    res: int
        Resolution of the transformation matrix.

    Return
    ------
    list: Allen coordinates in micron.
    """
    # Reading transform matrix
    file_mat = f'./utils/transformations_allen2avgt/allen2avgtAffine_{res}.mat'
    tx = ants.read_transform(file_mat)

    # Getting allen voxels RAS+ coords
    allen_ras = tx.apply_to_point(mib_coords)

    # Converting to PIR (microns)
    p, i, r = 13200//res, 8000//res, 11400//res
    r_, a, s = r, p, i
    x, y, z = allen_ras[0], allen_ras[1], allen_ras[2]
    x_, y_, z_ = (a-y)*res, (s-z)*res, x*res
    allen_pir = [x_, y_, z_]

    return list(map(int, allen_pir))


def search_experiments(args, seed_point):
    """
    Retrieve Allen experiments
    from a seed point.\n
    Using `injection coordinate search` or
    `spatial search`.

    Parameters
    ----------
    args: argparse namespace
        Argument list.
    seed_point : list of int
        Coordinate of the seed point
        in Allen reference space.

    Return
    ------
    dic : Allen experiments founded.
    """
    mcc = MouseConnectivityApi()

    # Injection coordinate search
    if args.injection:
        exps = mcc.experiment_injection_coordinate_search(
            seed_point=seed_point)

    # Spatial search
    if args.spatial:
        exps = mcc.experiment_spatial_search(
            seed_point=seed_point)

    return exps


def get_experiment_id(experiments, index, color):
    try:
        id = experiments[index]['id']
    except (KeyError, TypeError):
        sys.exit("No experiment founded : {}".format(color))

    return id


def main():
    # Building argparser
    parser = _build_arg_parser()
    args = parser.parse_args()

    # Verying args validity
    check_args(parser, args)

    # Getting allen coords
    allen_red_coords = get_allen_coords(args.red)
    allen_green_coords = get_allen_coords(args.green)
    if args.blue:
        allen_blue_coords = get_allen_coords(args.blue)

    # Getting Allen experiments
    red_exps = search_experiments(args, allen_red_coords)
    green_exps = search_experiments(args, allen_green_coords)
    if args.blue:
        blue_exps = search_experiments(args, allen_blue_coords)

    # Retrieving experiments ids
    red_id = get_experiment_id(red_exps, 0, "red")
    green_id = get_experiment_id(green_exps, 0, "green")
    if args.blue:
        blue_id = get_experiment_id(blue_exps, 0, "blue")

    if red_id == green_id:
        green_id = get_experiment_id(green_exps, 1, "green")
    if args.blue:
        if red_id == blue_id:
            blue_id = get_experiment_id(blue_exps, 1, "blue")
            if green_id == blue_id:
                blue_id = get_experiment_id(blue_exps, 2, "blue")
        elif green_id == blue_id:
            blue_id = get_experiment_id(blue_exps, 1, "blue")
            if red_id == blue_id:
                blue_id = get_experiment_id(blue_exps, 2, "blue")

    if red_id != green_id != blue_id:
        print(red_id, green_id, blue_id)
    # Aligning and saving projection density volumes

    # Creating and saving RGB volume

    # Searching crossing regions

    # Creating and saving ROI mask


if __name__ == "__main__":
    main()

#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    Extract a bundle of streamlines from a tractogram.\n
    Keep streamlines if any coordinate in the streamline is within
    the distance between the center of each voxel
    and the corner of the voxel.\n

    Streamlines in a sphere:

    >>> allen_tract_filter.py path/to/input.trk path/to/output.trk
    >>> path/to/reference.nii.gz
    >>> --sphere --center x y z --radius r --dir dir

    Use --donwload_sphere to download the spherical mask and
    precise its path

    Streamlines in a binary mask:

    >>> allen_tract_filter.py path/to/input.trk path/to/output.trk
    >>> path/to/reference.nii.gz --in_mask path_to_mask
"""

import argparse
import logging

import os
from pathlib import Path

import numpy as np
import nibabel as nib

import sys
sys.path.append(".")

from allen2tract.control import (add_overwrite_arg,
                                 check_input_file,
                                 check_file_exists,
                                 add_reference_arg)

from allen2tract.util import (draw_spherical_mask,
                              load_avgt, save_nii)

from allen2tract.tract import filter_tract_near_roi

EPILOG = """
Author : Mahdi
"""


def _build_arg_parser():
    p = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter,
                                epilog=EPILOG, description=__doc__)
    p.add_argument('in_tract', help='Path to allen tractogram (trk)')
    p.add_argument('out_tract', help='Path to output tractogram (trk)')
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument('--sphere', action="store_true",
                   help='Keep streamlines inside a spherical mask.\n'
                        'Precise its center and radius.')
    p.add_argument('--center', nargs=3, type=int,
                   help='Center of the spherical mask.\n'
                        'MI-brain coordinates (in voxels)')
    p.add_argument('--radius', type=float,
                   help='Radius of the spherical mask (in voxels).')
    p.add_argument('--download_sphere',
                   help='Path to .nii.gz spherical mask')
    g.add_argument('--in_mask',
                   help='Keep streamlines inside a ROI.\n'
                        'Path to .nii.gz binary mask.')
    add_reference_arg(p)
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
    if args.sphere and not args.radius:
        parser.error('--radius missing.')
    if args.sphere and not args.center:
        parser.error('--center missing.')

    if args.in_mask and args.radius:
        parser.error('--radius not needed here.')
    if args.in_mask and args.center:
        parser.error('--center not needed here.')
    if args.in_mask and args.download_sphere:
        parser.error('Cannot download spherical mask in this case.\n'
                     'Use --sphere instead.')


def main():
    # Building argparser
    parser = _build_arg_parser()
    args = parser.parse_args()

    # Verying args validity
    check_args(parser, args)

    # Checking input tract
    check_input_file(parser, args.in_tract)
    check_input_file(parser, args.reference)

    # Checking outputs
    check_file_exists(parser, args, args.out_tract)
    if args.download_sphere:
        check_file_exists(parser, args, args.download_sphere)

    # if --mask
    if args.in_mask:
        # Checking input file
        check_input_file(parser, args.in_mask)
        if not args.in_mask.endswith('.nii.gz'):
            parser.error('Invalid --mask format.\n'
                         '(.nii.gz) required.')

        # Loading the binary mask
        mask = nib.load(args.in_mask).get_fdata()

    # if --sphere
    if args.sphere:
        # Retrieve center coordinates
        x, y, z = args.center[0], args.center[1], args.center[2],
        center = (x, y, z)

        # Drawing the spherical mask
        mask = draw_spherical_mask(
            shape=load_avgt().shape,
            radius=args.radius,
            center=center)

        if args.download_sphere:
            # Saving the spherical mask
            save_nii(mask.astype(np.int32), args.download_sphere)

    # Saving the filtered tract
    filter_tract_near_roi(mask=mask, in_tract=args.in_tract,
                          out_tract=args.out_tract,
                          reference=args.reference)


if __name__ == "__main__":
    main()

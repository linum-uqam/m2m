#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
"""

import argparse
import json
import logging

import os
from pathlib import Path

import numpy as np
import nibabel as nib

from utils.control import (add_output_dir_arg,
                           add_overwrite_arg,
                           check_input_file,
                           check_file_exists)

from utils.util import (draw_spherical_mask,
                        load_avgt, save_nii)

from utils.tract import filter_tract_near_roi

EPILOG = """
Author : Mahdi
"""


def _build_arg_parser():
    p = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter,
                                epilog=EPILOG, description=__doc__)
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument('--sphere', action="store_true",
                   help='Keep streamlines inside a spherical mask.\n'
                        'Precise its center and radius.')
    p.add_argument('--center', nargs=3, type=int,
                   help='Center of the spherical mask.\n'
                        'MI-brain voxels coordinates')
    p.add_argument('--radius', type=float,
                   help='Radius of the spherical mask.')
    p.add_argument('--download_sphere', action="store_true",
                   help='Download the spherical mask.\n'
                        '.nii.gz output')
    g.add_argument('--in_mask',
                   help='Keep streamlines inside a ROI.\n'
                        'Path to .nii.gz binary mask.')
    add_output_dir_arg(p)
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

    # Configuring output directory
    args.dir = Path(args.dir)
    args.dir.mkdir(exist_ok=True, parents=True)

    # if --mask
    if args.in_mask:
        # Checking input file
        check_input_file(parser, args.in_mask)
        if not args.in_mask.endswith('.nii.gz'):
            parser.error('Invalid --mask format.\n'
                         '(.nii.gz) required.')

        # Preparing output file
        out_ = "avgt_wildtype_in_{}_tractogram.trk"
        mask_path = args.in_mask
        mask_name = os.path.basename(mask_path)
        index_of_dot = mask_name.rindex('_')
        mask_name_without_extension = mask_name[:index_of_dot]
        out_tract = os.path.join(args.dir,
                                 out_.format(mask_name_without_extension))
        check_file_exists(parser, args, out_tract)

        # Loading the binary mask
        mask = nib.load(args.in_mask).get_fdata()

    # if --sphere
    if args.sphere:
        # Retrieve center coordinates
        x, y, z = args.center[0], args.center[1], args.center[2],
        center = (x, y, z)

        # Drawing the spherical mask
        mask = draw_spherical_mask(
            shape = load_avgt().shape,
            radius=args.radius,
            center=center)

        # Preparing output file
        out_ = "avgt_wildtype_in_sphere_{}_{}_{}_r{}_tractogram.trk"
        out_tract = os.path.join(args.dir,
                                 out_.format(x, y, z, args.radius))
        check_file_exists(parser, args, out_tract)

        if args.download_sphere:
            # Saving the spherical mask
            out_ = "spherical_mask_{}_{}_{}_r{}.nii.gz"
            out_sphere = os.path.join(args.dir,
                                     out_.format(x, y, z, args.radius))
            check_file_exists(parser, args, out_sphere)

            save_nii(mask.astype(np.int32), out_sphere)

    # Saving the filtered tract
    filter_tract_near_roi(mask=mask, fname=out_tract)


if __name__ == "__main__":
    main()

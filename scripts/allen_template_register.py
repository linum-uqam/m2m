#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    Align allen templates to avgt template.

    Note: allen templates usually are PIR oriented
          and are .nrrd files

    >>> allen_template_register.py path/to/input.nrrd
        path/to/output.nii.gz resolution


"""

import argparse
import logging

import os
from pathlib import Path

import numpy as np
import nibabel as nib
import nrrd

import sys
sys.path.append(".")

from allen2tract.control import (add_overwrite_arg,
                                 check_input_file,
                                 check_file_exists)

from allen2tract.util import save_nii

from allen2tract.transform import (registrate_allen2avgt_ants,
                                   pretransform_vol_PIR_RAS)

EPILOG = """
Author : Mahdi
"""


def _build_arg_parser():
    p = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter,
                                epilog=EPILOG, description=__doc__)
    p.add_argument('in_nrrd', help='Path to allen template (.nrrd)')
    p.add_argument('out_nii', help='Path to registred template (.nii.gz)')
    p.add_argument('res', type=int, choices=[25, 50, 100],
                   help='Resolution of input template')
    add_overwrite_arg(p)
    return p


def main():
    # Building argparser
    parser = _build_arg_parser()
    args = parser.parse_args()

    # Verifying input file
    check_input_file(parser, args.in_nrrd)

    # Verifying output file
    check_file_exists(parser, args, args.out_nii)

    # Loading template
    allen_vol, hdr = nrrd.read(args.in_nrrd)

    # Transforming manually to RAS+
    allen_vol = pretransform_vol_PIR_RAS(allen_vol)

    # Loading allen volume converting to float32
    allen_vol = allen_vol.astype(np.float32)

    # Applying ANTsPyX registration
    warped_vol = registrate_allen2avgt_ants(
        res=args.res,
        allen_vol=allen_vol,
        smooth=True)

    # Creating and Saving the Nifti volume
    save_nii(warped_vol, args.out_nii)


if __name__ == "__main__":
    main()

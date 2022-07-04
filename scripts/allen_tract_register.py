#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    Align allen tractograms to avgt template.

    Note : allen tractogrames may have overlapping points.\n
    Please use scil_remove_invalid_streamlines.py to remove
    them : https://github.com/scilus/scilpy

    >>> allen_tract_register.py path/to/input.trk
        path/to/output.trk
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
                                 check_file_exists)

from allen2tract.util import load_avgt

from allen2tract.tract import (get_streamlines, get_tract, get_avgt_wildtype,
                               get_header, save_tract)

from allen2tract.transform import registrate_allen_streamlines

EPILOG = """
Author : Mahdi
"""


def _build_arg_parser():
    p = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter,
                                epilog=EPILOG, description=__doc__)
    p.add_argument('in_tract', help='Path to allen tractogram (trk)')
    p.add_argument('out_tract', help='Path to output tractogram (trk)')
    add_overwrite_arg(p)
    return p


def main():
    # Building argparser
    parser = _build_arg_parser()
    args = parser.parse_args()

    # Verying args validity
    check_input_file(parser, args.in_tract)

    # Configuring output files
    check_file_exists(parser, args, args.out_tract)

    # Loading tractogram
    tract = get_tract(args.in_tract)

    # Registrating streamlines
    new_streamlines = registrate_allen_streamlines(
                                            get_streamlines(tract))

    # Creating affine for MI-Brain display
    rotation = np.array([
        [1,  0,  0, 0],
        [0, -1,  0, 0],
        [0,  0, -1, 0],
        [0,  0,  0, 1]
        ])
    translation = np.array([
        [1, 0, 0,  0],
        [0, 1, 0, -212],
        [0, 0, 1, -158],
        [0, 0, 0,  1]
        ])
    affine = load_avgt().affine @ rotation @ translation

    # Saving tractogram
    save_tract(
        fname=args.out_tract,
        streamlines=new_streamlines,
        affine=affine,
        header=get_header(get_avgt_wildtype())
    )


if __name__ == "__main__":
    main()

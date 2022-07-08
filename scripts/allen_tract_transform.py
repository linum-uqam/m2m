#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    Align tractograms comming from allen to avgt template.

    Note : allen tractogrames may have overlapping points.\n
    Please use scil_remove_invalid_streamlines.py to remove
    them : https://github.com/scilus/scilpy

    >>> allen_tract_register.py path/to/input.trk
        path/to/output.trk path/to/output_reference.nii.gz
"""

import argparse
import logging
import os
from pathlib import Path
import numpy as np
import nibabel as nib
import sys
from allen2tract.control import (add_overwrite_arg,
                                 check_input_file,
                                 check_file_exists,
                                 add_reference_arg)
from allen2tract.tract import (get_tract, save_tract)
from allen2tract.transform import registrate_allen_streamlines

EPILOG = """
Author : Mahdi
"""


def _build_arg_parser():
    p = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter,
                                epilog=EPILOG, description=__doc__)
    p.add_argument('in_tract', help='Path to allen tractogram (trk)')
    p.add_argument('out_tract', help='Path to output tractogram (trk)')
    add_reference_arg(p)
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

    # Loading reference
    ref = nib.load(args.reference)

    # Loading in tractogram
    tract = get_tract(args.in_tract, 'same',
                      check_bbox=False, check_hdr=False)

    # Registrating streamlines
    new_streamlines = registrate_allen_streamlines(tract.streamlines)

    # Saving tractogram
    save_tract(
        fname=args.out_tract,
        streamlines=new_streamlines,
        reference=str(args.reference),
        check_bbox=False
    )


if __name__ == "__main__":
    main()

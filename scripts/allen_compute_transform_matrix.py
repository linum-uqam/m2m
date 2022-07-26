#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    Compute an Affine transformation matrix for a specific resolution
    in the Allen using ANTsPyX to align Allen average template on
    User reference template.

    >>> allen_compute_transform_matrix.py path/to/reference.nii.gz
        path/to/matrix.mat resolution
"""

import argparse
import os
from allen2tract.control import (add_cache_arg,
                                 add_overwrite_arg,
                                 add_reference_arg,
                                 check_input_file,
                                 check_file_exists,
                                 add_resolution_arg)
from allen2tract.transform import (compute_transform_matrix,
                                   pretransform_vol_PIR_UserDataSpace)
from allen2tract.allensdk_utils import download_template_vol
from allen2tract.util import load_user_template

EPILOG = """
Author : Mahdi
"""


def _build_arg_parser():
    p = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter,
                                epilog=EPILOG, description=__doc__)
    add_reference_arg(p)
    p.add_argument('out_mat', help='Path to output matrix (.mat)')
    add_resolution_arg(p)
    add_cache_arg(p)
    add_overwrite_arg(p)
    return p


def main():
    # Building argparser
    parser = _build_arg_parser()
    args = parser.parse_args()

    # Verying args validity
    check_input_file(parser, args.reference)
    if not (args.reference).endswith(".nii") or \
            not (args.reference).endswith(".nii.gz"):
        parser.error("reference must be a nifti file.")
    check_file_exists(parser, args, args.out_mat)
    if not (args.out_mat).endswith(".mat"):
        parser.error("out_mat must be .mat file.")

    # Downloading allen template
    nrrd_file = "allen_template_{}.nrrd".format(args.res)
    allen_vol = download_template_vol(nrrd_file, args.res, args.nocache)

    # Loading User template
    user_vol = load_user_template(str(args.reference))

    # Pretransform volumes orientations
    allen_reorient = pretransform_vol_PIR_UserDataSpace(allen_vol, user_vol)

    # Registrating with ANTsPyX
    affine_mat = compute_transform_matrix(allen_reorient, user_vol)

    # Saving the matrix
    os.rename(affine_mat, args.out_mat)


if __name__ == "__main__":
    main()

#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    Compute an 3 Affines transformations matrices for each resolution
    in the Allen (25, 50, 100) using ANTsPyX. 

    Thoses matrices are needed for the other scripts in order 
    to align Allen data on User Data Space.

    >>> allen_compute_transform_matrix.py path/to/reference.nii.gz
        path/to/matrix25.mat path/to/matrix50.mat path/to/matrix100.mat
"""

import argparse
import os
from allen2tract.control import (add_cache_arg,
                                 add_overwrite_arg,
                                 add_reference_arg,
                                 check_input_file,
                                 check_file_exists)
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
    p.add_argument('out_mat_25',
                   help='Path to output matrix (res=25) (.mat)')
    p.add_argument('out_mat_50',
                   help='Path to output matrix (res=50) (.mat)')
    p.add_argument('out_mat_100',
                   help='Path to output matrix (res=100) (.mat)')
    add_cache_arg(p)
    add_overwrite_arg(p)
    return p


def main():
    # Building argparser
    parser = _build_arg_parser()
    args = parser.parse_args()

    # Checking input reference
    check_input_file(parser, args.reference)
    if not (args.reference).endswith(".nii") and \
            not (args.reference).endswith(".nii.gz"):
        parser.error("reference must be a nifti file.")
    # Loading User template
    user_vol = load_user_template(str(args.reference))

    # Checking out matrices
    out_matrices = [args.out_mat_25, args.out_mat_50, args.out_mat_100]
    for mat in out_matrices:
        check_file_exists(parser, args, mat)
        if not (mat).endswith(".mat"):
            parser.error("{} must be .mat file.".format(mat))

    # Configuring resolutions
    allen_res = [25, 50, 100]

    for res in allen_res:
        # Selectionning the right file to save
        if res == 25:
            out_mat = args.out_mat_25
        elif res == 50:
            out_mat = args.out_mat_50
        elif res == 100:
            out_mat= args.out_mat_100

        # Downloading allen template
        nrrd_file = "allen_template_{}.nrrd".format(res)
        allen_vol = download_template_vol(nrrd_file, res, args.nocache)

        # Pretransform volumes orientations
        allen_reorient = pretransform_vol_PIR_UserDataSpace(allen_vol, user_vol)

        # Registrating with ANTsPyX
        affine_mat = compute_transform_matrix(allen_reorient, user_vol)

        # Saving the matrix
        os.rename(affine_mat, out_mat)


if __name__ == "__main__":
    main()

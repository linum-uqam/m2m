#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Transform the Allen tractogram (Wildtype, RAS@50um) to the User's Data Space (UDS).

Please note that Allen tractogram may have overlapping points, you can
use scil_remove_invalid_streamlines to remove them : https://github.com/scilus/scilpy
"""

import argparse
import nibabel as nib
import numpy as np
import os

from m2m.control import (add_overwrite_arg,
                         check_input_file,
                         check_file_exists,
                         add_reference_arg,
                         get_cached_dir)
from m2m.data import download_to_cache
from m2m.tract import (filter_tract_near_roi,
                       get_tract,
                       save_tract)
from m2m.transform import registrate_allen_streamlines
from m2m.util import (draw_spherical_mask,
                      load_user_template,
                      save_nifti)

EPILOG = """
Author : Joel Lefebvre
"""


def _build_arg_parser():
    p = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter,
                                epilog=EPILOG, description=__doc__)
    p.add_argument('out_tract', help='Path to output tractogram (trk)')
    p.add_argument('file_mat', help='Path to transform matrix (.mat)')
    add_reference_arg(p)
    return p


def main():
    # Building argparser
    parser = _build_arg_parser()
    args = parser.parse_args()

    # Loading reference
    check_input_file(parser, args.reference)
    if not args.reference.endswith(".nii") and \
            not args.reference.endswith(".nii.gz"):
        parser.error("reference must be a nifti file.")
    user_vol = load_user_template(args.reference)

    # Checking outputs
    check_file_exists(parser, args, args.out_tract)
    if not args.out_tract.endswith(".trk"):
        parser.error("out_tract must be a trk file.")

    # Checking file mat
    check_input_file(parser, args.file_mat)

    # Downloading the Allen Tractogram (Wildtype, 50 micron)
    trk_file = download_to_cache("allen_tractogram_wildtype_50um.trk")

    # Loading tractogram
    trk_reference = download_to_cache("allen_template_ras_50um.nii.gz")
    trk = get_tract(trk_file, trk_reference, check_bbox=False, check_hdr=False)

    # Transforming streamlines
    trk.to_vox()
    input_trk_resolution = 50  # micron
    streamlines = registrate_allen_streamlines(trk.streamlines, args.file_mat, user_vol, input_trk_resolution)

    # Saving the tractogram
    print("Saving the transformed tractogram")
    save_tract(args.out_tract, streamlines, args.reference, check_bbox=False)


if __name__ == "__main__":
    main()

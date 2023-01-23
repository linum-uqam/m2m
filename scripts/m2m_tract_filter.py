#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    Link to download Allen tractogram (resolution=50):
    https://drive.google.com/file/d/1E-w9HsdhJxGaC3KcoVCFx8ejcN4DyrFp/view?usp=sharing

    Extract a bundle of streamlines from Allen tractogram.\n
    Keep streamlines if any coordinate in the streamline is within
    the distance between the center of each voxel
    and the corner of the voxel.\n

    Please note that Allen tractogram may have overlapping points, you can
    use scil_remove_invalid_streamlines to remove them :
    https://github.com/scilus/scilpy


    First call of the script :
    --------------------------
    - Download the Allen tractogram
    - Call :

    >>> m2m_tract_filter.py path/to/output.trk path/to/reference.nii.gz
        --file_mat path/to/file_mat.mat --in_tract path/to/allentrk.trk
        [see (a) or (b) to ROI filters]

    (note: matrix should be .mat computed at resolution=50)

    ROI filters:
    ------------
    (a) Streamlines in a sphere:

    Add to the command line:

    >>> --sphere --center x y z --radius r

    Use --donwload_sphere to download the spherical mask and
    precise its path

    (b) Streamlines in a binary mask:

    Add to the command line:

    >>> --in_mask path_to_mask

    Ones fist call is done:
    -----------------------
    No more need to add --file_mat and --in_tract to the command line

    Example:
    
    >>> m2m_tract_filter.py path/to/output.trk path/to/reference.nii.gz
        [see (a) or (b) to ROI filters]
"""

import argparse
import os
import numpy as np
import nibabel as nib
from m2m.control import (add_overwrite_arg,
                         check_input_file,
                         check_file_exists,
                         add_reference_arg,
                         get_cached_dir)
from m2m.util import (draw_spherical_mask,
                      load_user_template,
                      save_nifti)
from m2m.transform import registrate_allen_streamlines
from m2m.tract import (filter_tract_near_roi,
                       get_tract,
                       save_tract)

EPILOG = """
Author : Mahdi
"""


def _build_arg_parser():
    p = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter,
                                epilog=EPILOG, description=__doc__)
    p.add_argument('out_tract', help='Path to output tractogram (trk)')
    p.add_argument('--in_tract', help='Path to allen tractogram (trk)')
    p.add_argument('--file_mat', help='Path to transform matrix (.mat)')
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

    # Loading reference
    check_input_file(parser, args.reference)
    if not (args.reference).endswith(".nii") and \
            not (args.reference).endswith(".nii.gz"):
        parser.error("reference must be a nifti file.")
    user_vol = load_user_template(args.reference)

    # Checking outputs
    check_file_exists(parser, args, args.out_tract)
    if not (args.out_tract).endswith(".trk"):
        parser.error("out_tract must be a trk file.")

    if args.download_sphere:
        check_file_exists(parser, args, args.download_sphere)

    # Setting Allen tractogram (in UserDataSpace) path.
    # Saving it in first call of script
    # Reading it in following calls
    trk_file = os.path.join(get_cached_dir("data"),
                            "allen_wildtype_transfromed.trk")

    # Aligning and saving allen tractogram in user data space
    # First call of the script see (-h)
    if args.in_tract and args.file_mat and not os.path.isfile(trk_file):
        # Checking file mat
        check_input_file(parser, args.file_mat)

        # Checking input tract
        check_input_file(parser, args.in_tract)

        # Loading tractogram
        trk_reference = os.path.join(get_cached_dir("data"),
                                     'allen_template_50_ras.nii.gz')
        trk = get_tract(args.in_tract, trk_reference, False, False)

        # Transforming streamlines
        trk.to_vox()
        sl = registrate_allen_streamlines(trk.streamlines,
                                          args.file_mat, user_vol, 50)

        # Saving the tractogram
        save_tract(trk_file, sl, args.reference, check_bbox=False)

    elif (not args.in_tract or not args.file_mat) and \
            not os.path.isfile(trk_file):
        parser.error("Please use --in_tract and --file_mat "
                     "in first call (see -h)")

    elif (args.in_tract or args.file_mat) and os.path.isfile(trk_file):
        parser.error("Allen trk already saved in your data space, "
                     "no more need to use --in_tract and --file_mat")

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
            shape=user_vol.shape,
            radius=args.radius,
            center=center)

        if args.download_sphere:
            # Saving the spherical mask
            save_nifti(mask.astype(np.int32), args.download_sphere)

    # Saving the filtered tract
    filter_tract_near_roi(mask=mask, in_tract=trk_file,
                          out_tract=args.out_tract,
                          reference=args.reference)


if __name__ == "__main__":
    main()

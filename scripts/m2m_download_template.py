#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Download the Allen mouse brain template, and setting the correct RAS+ direction and spacing.
"""

import argparse
from allensdk.api.queries.reference_space_api import ReferenceSpaceApi
from pathlib import Path
import numpy as np
import nibabel as nib

from m2m.transform import (registrate_allen2UserDataSpace)
from m2m.util import (load_user_template,
                      save_nifti, )

ALLEN_RESOLUTIONS = [10, 25, 50, 100]


def _build_arg_parser():
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    p.add_argument("output",
                   help="Output nifti filename")
    p.add_argument("-r", "--resolution", default=100, type=int, choices=ALLEN_RESOLUTIONS,
                   help="Template resolution in micron. Default=%(default)s")

    # Add optional arguments to align the template to the user space
    p.add_argument_group("Align the template to the user space")
    p.add_argument("-m", "--file_mat", default=None, type=str,
                   help="Path to the transform matrix (.mat)")
    p.add_argument("-R", "--reference", default=None, type=str,
                     help="Path to the reference volume (.nii.gz)")

    return p


def main():
    parser = _build_arg_parser()
    args = parser.parse_args()

    # Prepare the output directory
    output = Path(args.output)
    extension = ""
    if output.name.endswith(".nii"):
        extension = ".nii"
    elif output.name.endswith(".nii.gz"):
        extension = ".nii.gz"
    assert extension in [".nii", ".nii.gz"], "The output file must be a nifti file."
    output.absolute()
    output.parent.mkdir(exist_ok=True, parents=True)

    # Preparing the filenames
    nrrd_file = output.parent / f"allen_template_{args.resolution}.nrrd"

    # Downloading the template
    rpa = ReferenceSpaceApi(base_uri=str(output.parent))
    vol, metadata = rpa.download_template_volume(resolution=args.resolution, file_name=nrrd_file)

    # Converting to PIR to RAS+
    vol = np.moveaxis(vol, [0, 1, 2], [1, 2, 0])
    vol = np.flip(vol, axis=1)  # To move from A->P to P->A
    vol = np.flip(vol, axis=2)  # To move from S->I to I->S

    # Preparing the affine
    r_mm = args.resolution / 1e3  # Convert the resolution from micron to mm
    affine = np.eye(4) * r_mm
    affine[3, 3] = 1

    # Save the volume
    img = nib.Nifti1Image(vol, affine)
    nib.save(img, str(output))
    nrrd_file.unlink()  # Removes the nrrd file

    # If the affine matrix was provided, apply it
    if args.reference is not None and args.file_mat is not None:
        user_vol = load_user_template(args.reference)

        # Load the allen template
        allen_vol = load_user_template(str(output))
        allen_vol = allen_vol.get_fdata()

        # Applying ANTsPyX registration
        warped_vol = registrate_allen2UserDataSpace(
            args.file_mat,
            allen_vol,
            user_vol,
            allen_res=args.resolution,
            smooth=True
        )

        # Deleting negatives values introduced by b-spline interpolation
        warped_vol[warped_vol < 0] = 0

        # Saving the warped volume
        save_nifti(warped_vol, user_vol.affine, args.output)


if __name__ == "__main__":
    main()

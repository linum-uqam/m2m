#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Download the Allen mouse brain annotation for the Adule Mouse (3D), and setting the correct RAS+ direction and spacing.
"""

import argparse
from allensdk.api.queries.reference_space_api import ReferenceSpaceApi
from allensdk.core.reference_space_cache import ReferenceSpaceCache
from pathlib import Path
import SimpleITK as sitk

ALLEN_RESOLUTIONS = [10, 25, 50, 100]


def _build_arg_parser():
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    p.add_argument("output",
                   help="Output nifti filename")
    p.add_argument("output_json",
                   help="Output json annotation information file.")
    #p.add_argument("--itksnap_info_file", default=None,
    #               help="Optional txt annotation information file name. Can be used by ITKSnap")
    p.add_argument("-r", "--resolution", default=100, type=int, choices=ALLEN_RESOLUTIONS,
                   help="Template resolution in micron. Default=%(default)s")
    p.add_argument("--apply_transform", action="store_true",
                   help="Apply the transform to align the volume to RAS+ instead of relying only on the volume metadata")

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
    nrrd_file = output.parent / f"allen_annotation_{args.resolution}.nrrd"

    # Downloading the annotation
    reference_space_key = "annotation/ccf_2017"
    manifest_file = output.parent / "manifest.json"
    rpa = ReferenceSpaceApi(base_uri=str(output.parent))
    rspc = ReferenceSpaceCache(args.resolution, reference_space_key, manifest = manifest_file)
    #rpa.download_template_volume(resolution=args.resolution, file_name=nrrd_file)
    rpa.download_annotation_volume(ccf_version="annotation/ccf_2017", resolution=args.resolution, file_name=nrrd_file)

    # Loading the nrrd file
    vol = sitk.ReadImage(str(nrrd_file))

    # Preparing the affine to align the template in the RAS+
    r_mm = args.resolution / 1e3  # Convert the resolution from micron to mm
    vol.SetSpacing([r_mm] * 3)  # Set the spacing in mm
    if args.apply_transform:
        vol = sitk.PermuteAxes(vol, (2, 0, 1))
        vol = sitk.Flip(vol, (False, False, True))
        vol.SetDirection([1, 0, 0, 0, 1, 0, 0, 0, 1])
    else:
        vol.SetDirection([0, 0, -1, 1, 0, 0, 0, -1, 0])  # Set the correct axes directions.
    sitk.WriteImage(vol, str(output))
    nrrd_file.unlink()  # Removes the nrrd file

    # Download the brain structure information - WIP
    # ID 1 is the adult mouse structure graph
    #tree = rspc.get_structure_tree(file_name=args.output_json, structure_graph_id=1)
    #if args.itksnap_info_file is not None:
    #   info = tree.export_label_description()
    #     with open(args.itksnap_info_file, 'w') as f:
    #        f.write(info.to_string(index=False))

if __name__ == "__main__":
    main()

#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    By default, download all File flags (see arguments) and
    align them on User Data Space.

    Important: Select the same resolution as your matrix

    Minimum mandatory requires to call the script : (a)

    >>> m2m_import_proj_density.py id path/to/ref.nii.gz
        path/to/matrix.mat resolution
    
    Find an id here : https://connectivity.brain-map.org/

    If --not_all is set, only the files specified will be output.

    Examples
    --------
    ((a) correpond to the previous mandatory command line)

    Import a projection density map of an experiment in the
    Allen Mouse Brain Connectivity Atlas and align it on UserDataSpace.
    
    >>> (a) --not_all --map

    >>> (a) --not_all --map --smooth

    Download a spherical roi mask located at the injection coordinates of an
    experiment in the Allen Mouse Brain Connectivity Atlas and
    align it on UserDataSpace.

    >>> (a) --not_all --roi

    Save experiment injection coordinates (Allen and MI-Brain) in a json file.

    >>> (a) --not_all --infos

    Save a binarized projection density map.

    >>> (a) --not_all --bin --threshold
    
"""

import argparse
import json
from pathlib import Path
import numpy as np
from m2m.control import (add_cache_arg,
                         add_matrix_arg,
                         add_output_dir_arg,
                         add_overwrite_arg,
                         add_reference_arg,
                         add_resolution_arg,
                         check_file_exists,
                         check_input_file)
from m2m.transform import (get_user_coords,
                           pretransform_vol_PIR_UserDataSpace,
                           registrate_allen2UserDataSpace,
                           select_allen_bbox)
from m2m.allensdk_utils import (download_proj_density_vol,
                                get_injection_infos,
                                get_mcc_exps)
from m2m.util import (draw_spherical_mask,
                      load_user_template,
                      save_nifti, )

EPILOG = """
Author : Mahdi
"""


def _build_arg_parser():
    p = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter,
                                epilog=EPILOG, description=__doc__)
    p.add_argument('id', type=int,
                   help='Experiment id in the Allen Mouse Brain '
                        'Connectivity Atlas dataset.')
    add_reference_arg(p)
    add_matrix_arg(p)
    p.add_argument('--smooth', action="store_true",
                   help='Interpolation method for the registration '
                        'is nearestNeighbor by default.\n'
                        'Using --smooth will change the method to bSpline.')
    p.add_argument('--threshold', type=float, default=.5,
                   help='Threshold for the binarised map.')
    p.add_argument('--not_all', action="store_true",
                   help='If set, only saves the files specified')
    add_resolution_arg(p)
    add_output_dir_arg(p)
    add_cache_arg(p)
    add_overwrite_arg(p)
    g = p.add_argument_group(title='File flags')
    g.add_argument('--map', action="store_true",
                   help='Save the projection density map of the experiment '
                        '(.nii.gz)')
    g.add_argument('--roi', action="store_true",
                   help='Save a spherical mask at the injection coordinates'
                        'of the experiment (.nii.gz)')
    g.add_argument('--bin', action="store_true",
                   help='Save a binarized projection density map (.nii.gz)'
                        'with a certain --threshold.')
    g.add_argument('--infos', action="store_true",
                   help='Save informations about the experiment (.json):\n'
                        '- Injection coordinates (MI-Brain, Allen)\n'
                        '- Hemisphere (L or R)\n'
                        '- Injection ROI\n')
    return p


def main():
    # Building argparser
    parser = _build_arg_parser()
    args = parser.parse_args()

    # Loading reference
    check_input_file(parser, args.reference)
    if not (args.reference).endswith(".nii") and \
            not (args.reference).endswith(".nii.gz"):
        parser.error("reference must be a nifti file.")
    user_vol = load_user_template(args.reference)

    # Checking file mat
    check_input_file(parser, args.file_mat)

    # Getting experiments from Cache
    allen_experiments = get_mcc_exps(args.nocache)

    # Verifying experiment id
    ids = allen_experiments.id

    if args.id not in ids:
        parser.error("This experiment id : {}, doesn't exist. \n"
                     "Please check : https://connectivity.brain-map.org/"
                     .format(args.id))

    # Configuring output directory
    args.dir = Path(args.dir)
    args.dir.mkdir(exist_ok=True, parents=True)

    # Experiment infos
    # injection region, location, position (inj_coords_um)
    roi = get_injection_infos(allen_experiments, args.id)[0]
    loc = get_injection_infos(allen_experiments, args.id)[2]
    pos = get_injection_infos(allen_experiments, args.id)[1]

    # Configuring outputs filenames
    args_list = [args.map, args.roi, args.infos, args.bin]

    if not args.not_all and any(args_list):
        parser.error("Please specify --not_all to download "
                     "a specific file")

    if not args.not_all:
        args.map = True
        args.roi = True
        args.infos = True
        args.bin = True

    if args.not_all and not any(args_list):
        parser.error("Please precise at least one file to download. \n"
                     "Use --map to download the projection density map.\n"
                     "Use --roi to download the spherical roi mask.\n"
                     "User --infos to download the experiment infos.\n"
                     "Use --bin to download the binarised map.")

    file_map = args.dir / "{}_{}_{}_proj_density_{}.nii.gz"\
                          .format(args.id, roi, loc, args.res)
    if args.smooth:
        file_map = args.dir / "{}_{}_{}_proj_density_{}_bSpline.nii.gz"\
                              .format(args.id, roi, loc, args.res)
    file_roi = args.dir / "{}_{}_{}_spherical_mask_{}.nii.gz"\
                          .format(args.id, roi, loc, args.res)
    file_infos = args.dir / "{}_{}_{}_inj_coords_{}.json"\
                            .format(args.id, roi, loc, args.res)
    file_bin = args.dir / "{}_{}_{}_proj_density_{}_bin{}.nii.gz"\
                          .format(args.id, roi, loc, args.res, args.threshold)

    file_list = [file_map, file_roi, file_infos, file_bin]

    # Verifying if files exists
    for file in file_list:
        if args_list[file_list.index(file)] or not args.not_all:
            check_file_exists(parser, args, file)

    # Creating and Saving MI-brain injection coordinates coords in json file
    # Saving experiments infos if --infos was used
    if args.infos:
        # Getting mi-brain voxel coordinates
        # mib_coords = get_mib_coords(args, allen_experiments)
        mib_coords = get_user_coords(pos, args.res, args.file_mat,
                                     user_vol)

        # Creating json content
        dic = {"id": str(args.id), "roi": roi, "location": loc,
               "allen_micron": str(pos), "mibrain_voxels": str(mib_coords)}

        # Saving in json file
        json_object = json.dumps(dic, indent=4)
        with open(file_infos, "w") as outfile:
            outfile.write(json_object)

    # Downloading and Saving the projection density map if --map was used
    if args.map or args.bin:
        # Configuring files names
        nrrd_file = "{}_{}.nrrd".format(args.id, args.res)

        # Downloading projection density (API)
        allen_vol = download_proj_density_vol(nrrd_file, args.id,
                                              args.res, args.nocache)

        # Transforming manually to RAS+
        allen_vol = pretransform_vol_PIR_UserDataSpace(allen_vol, user_vol)

        # Applying ANTsPyX registration
        warped_vol = registrate_allen2UserDataSpace(
            args.file_mat,
            allen_vol,
            user_vol,
            allen_res=args.res,
            smooth=args.smooth
        )

        # Deleting negatives values if bSpline method was used (--smooth)
        if args.smooth:
            warped_vol[warped_vol < 0] = 0

        if args.map:
            # Creating and Saving the Nifti map
            save_nifti(warped_vol, user_vol.affine, file_map)

        if args.bin:
            # Creating and Saving the Nifti bin map
            bin_vol = (warped_vol >= args.threshold).astype(np.int32)
            save_nifti(bin_vol, user_vol.affine, file_bin)

    # Creating and Saving the spherical mask if --roi was used
    if args.roi:
        # Converting the coordinates in voxels depending the resolution
        inj_coord_voxels = (pos[0]/args.res,
                            pos[1]/args.res,
                            pos[2]/args.res)

        # Configuring the bounding box
        bbox_allen = select_allen_bbox(args.res)

        # Drawing the spherical mask
        roi_sphere_allen = draw_spherical_mask(
            shape=bbox_allen,
            center=inj_coord_voxels,
            radius=400//args.res)

        # Transforming manually to RAS+
        roi_sphere_allen = pretransform_vol_PIR_UserDataSpace(roi_sphere_allen,
                                                              user_vol)

        # Applying ANTsPyX registration
        roi_sphere_avgt = registrate_allen2UserDataSpace(
            args.file_mat,
            roi_sphere_allen,
            user_vol,
            allen_res=args.res,
        )

        # Deleting non needed interpolated values
        roi_sphere_avgt = roi_sphere_avgt.astype(np.int32)

        # Creating and Saving the Nifti spherical mask
        save_nifti(roi_sphere_avgt, user_vol.affine, file_roi)


if __name__ == "__main__":
    main()

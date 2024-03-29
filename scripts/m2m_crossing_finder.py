#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    Find crossing regions (ROIs) between Allen Mouse Brain Connectivity
    experiments.
    Experiments are found by search in the Allen Mouse Brain Connectivity API
    giving two or three User Data Space (UDS) voxel coordinates.\n

    - Generate projection density maps for each experiment.
      Maps are downloaded from the Allen Mouse Brain Connectivity API.\n

    - Generate a RGB projection density volume combining each
      experiments founded. (--red, --green, --blue).
      At least two colors (coordinates) are mandatory.\n

    - Generate a mask at crossing regions if projection density is
      superior to threshold (--threshold) for each experiment founded.
      Masks are download from Allen Mouse Brain Altas.\n

    - Generate a json file enumarating each crossing regions.\n

    All files are stored in a same folder.\n

    Examples:
    ---------

    Important: Select the same resolution as your matrix
    We higly recommend to work with high resolution (starting from 50)
    in order to search experiments more precisely.

    2 colors:

    Injection coordinate search: (--injection)

    >>> m2m_crossing_finder.py path/to/.mat path/to/ref.nii.gz
        resolution --red x y z --green x y z --injection --dir dir

    Spatial search: (--spatial):

    >>> m2m_crossing_finder.py path/to/.mat path/to/ref.nii.gz
        resolution --red x y z --green x y z --spatial --dir dir

    3 colors:

    >>> m2m_crossing_finder.py path/to/.mat path/to/ref.nii.gz
        resolution --red x y z --green x y z --blue x y z --injection --dir dir
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from m2m.allensdk_utils import (download_proj_density_vol,
                                download_struct_mask_vol,
                                get_structure_parents_infos,
                                get_unionized_list,
                                get_injection_infos,
                                get_mcc_exps,
                                get_mcc_stree,
                                search_experiments)
from m2m.control import (add_cache_arg,
                         add_output_dir_arg,
                         add_overwrite_arg,
                         add_resolution_arg,
                         check_file_exists,
                         add_matrix_arg,
                         add_reference_arg,
                         check_input_file)
from m2m.transform import (pretransform_vol_PIR_UserDataSpace,
                           registrate_allen2UserDataSpace,
                           get_allen_coords,
                           select_allen_bbox)
from m2m.util import (save_nifti,
                      load_user_template)

EPILOG = """
Author : Mahdi
"""


def _build_arg_parser():
    p = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter,
                                epilog=EPILOG, description=__doc__)
    add_matrix_arg(p)
    add_reference_arg(p)
    p.add_argument('--red', nargs=3, type=int, required=True,
                   help='UDS voxels coordinates of first experiment.\n'
                        'First experiment will be colored in red.')
    p.add_argument('--green', nargs=3, type=int, required=True,
                   help='UDS voxels coordinates of second experiment.\n'
                        'Second experiment will be colored in green.')
    p.add_argument('--blue', nargs=3, type=int,
                   help='UDS voxels coordinates of third experiment.\n'
                        'Third experiment will be colored in blue.')
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument('--injection', action="store_true",
                   help='Use `experiment_injection_coordinate_search` '
                        'to find experiments.\n'
                        'https://allensdk.readthedocs.io/en/latest/'
                        'allensdk.api.queries.mouse_connectivity_api.html')
    g.add_argument('--spatial', action="store_true",
                   help='Use `experiment_spatial_search` '
                        'to find experiments.\n'
                        'https://allensdk.readthedocs.io/en/latest/'
                        'allensdk.api.queries.mouse_connectivity_api.html')
    p.add_argument('--threshold', type=float, default=0.10,
                   help='Combined projection density threshold for finding '
                        'masks of crossing ROIs.\n'
                        'Threshold is 0.10 by default.\n'
                        '--threshold <value> will set threshold to value.')
    add_resolution_arg(p)
    add_output_dir_arg(p)
    add_cache_arg(p)
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
    # Verifying threshold
    if 0.0 > args.threshold > 1.0:
        parser.error('Please enter a valid threshold value. '
                     'Pick a float value from 0.0 to 1.0')


def check_coords_in_bbox(parser, args):
    """
    Verify that the provided coordinates are within the reference volume bounding box.

    Parameters
    ----------
    parser: argparse.ArgumentParser object
        Parser.
    args: argparse namespace
        Argument list.
    """
    # Load the reference
    reference = load_user_template(args.reference)

    # Verifying coords
    x, y, z = range(0, reference.shape[0]), range(0, reference.shape[1]), range(0, reference.shape[2])
    if args.red[0] not in x or \
            args.red[1] not in y or \
            args.red[2] not in z:
        parser.error('Invalid red coordinates'
                     f'x, y, z values must be in {reference.shape}')
    if args.green[0] not in x or \
            args.green[1] not in y or \
            args.green[2] not in z:
        parser.error('Invalid green coordinates. '
                     f'x, y, z values must be in {reference.shape}.')
    if args.blue:
        if args.blue[0] not in x or \
                args.blue[1] not in y or \
                args.blue[2] not in z:
            parser.error('Invalid blue coordinates. '
                         f'x, y, z values must be in {reference.shape}.')


def get_experiment_id(experiments, index, color):
    """
    Retrieve an experiment id at a specific index in a list of
    Allen experiments found with `search_experiments`.\n
    Notify if there is no experiments.

    Parameters
    ----------
    experiments: dic
        Allen experiments.
    index: int
        Index of the experiment needed.
    color: string
        Color of the experiment.
        Used to notify if error.

    Return
    ------
    id : Allen experiment id founded.
    """
    try:
        id = experiments[index]['id']
    except (KeyError, TypeError):
        sys.exit("No experiment founded : {}".format(color))

    return id


def main():
    # Building argparser
    parser = _build_arg_parser()
    args = parser.parse_args()

    # Verifying args validity
    check_args(parser, args)

    # Loading reference
    check_input_file(parser, args.reference)
    if not (args.reference).endswith(".nii") and \
            not (args.reference).endswith(".nii.gz"):
        parser.error("reference must be a nifti file.")
    user_vol = load_user_template(args.reference)

    # Checking that the coords are in the bounding box
    check_coords_in_bbox(parser, args)

    # Checking file mat
    check_input_file(parser, args.file_mat)

    # Getting experiments from Mouse Connectivity Cache
    allen_experiments = get_mcc_exps(args.nocache)
    stree = get_mcc_stree(args.nocache)

    # Configuring output directory
    args.dir = Path(args.dir)
    args.dir.mkdir(exist_ok=True, parents=True)

    # Getting Allen coords
    allen_red_coords = get_allen_coords(args.red, args.res,
                                        args.file_mat, user_vol)
    allen_green_coords = get_allen_coords(args.green, args.res,
                                          args.file_mat, user_vol)
    if args.blue:
        allen_blue_coords = get_allen_coords(args.blue, args.res,
                                             args.file_mat, user_vol)

    # Searching Allen experiments
    red_exps = search_experiments(args.injection, args.spatial,
                                  allen_red_coords)
    green_exps = search_experiments(args.injection, args.spatial,
                                    allen_green_coords)
    if args.blue:
        blue_exps = search_experiments(args.injection, args.spatial,
                                       allen_blue_coords)

    # Retrieving experiments ids
    red_id = get_experiment_id(red_exps, 0, "red")
    green_id = get_experiment_id(green_exps, 0, "green")
    if args.blue:
        blue_id = get_experiment_id(blue_exps, 0, "blue")

    if red_id == green_id:
        green_id = get_experiment_id(green_exps, 1, "green")
    if args.blue:
        if red_id == blue_id:
            blue_id = get_experiment_id(blue_exps, 1, "blue")
            if green_id == blue_id:
                blue_id = get_experiment_id(blue_exps, 2, "blue")
        elif green_id == blue_id:
            blue_id = get_experiment_id(blue_exps, 1, "blue")
            if red_id == blue_id:
                blue_id = get_experiment_id(blue_exps, 2, "blue")

    # Preparing files names
    # Creating subdir
    subdir_ = f"{red_id}_{green_id}_{args.res}_{args.threshold}"
    if args.blue:
        subdir_ = f"{red_id}_{green_id}_{blue_id}_{args.res}_{args.threshold}"
    subdir = Path(args.dir / subdir_)
    subdir.mkdir(exist_ok=True, parents=True)

    # Retrieving experiment information
    rroi = get_injection_infos(allen_experiments, red_id)[0]
    rloc = get_injection_infos(allen_experiments, red_id)[2]
    groi = get_injection_infos(allen_experiments, green_id)[0]
    gloc = get_injection_infos(allen_experiments, green_id)[2]
    if args.blue:
        broi = get_injection_infos(allen_experiments, blue_id)[0]
        bloc = get_injection_infos(allen_experiments, blue_id)[2]

    # Projection density maps Niftis and Nrrd files
    nrrd_ = "{}_{}.nrrd"
    nifti_ = "{}_{}_{}_proj_density_{}.nii.gz"

    nrrd_red = nrrd_.format(red_id, args.res)
    nifti_red = subdir / nifti_.format(red_id, rroi, rloc, args.res)
    check_file_exists(parser, args, nifti_red)

    nrrd_green = nrrd_.format(green_id, args.res)
    nifti_green = subdir / nifti_.format(green_id, groi, gloc, args.res)
    check_file_exists(parser, args, nifti_green)

    if args.blue:
        nrrd_blue = nrrd_.format(blue_id, args.res)
        nifti_blue = subdir / nifti_.format(blue_id, broi, bloc, args.res)
        check_file_exists(parser, args, nifti_blue)

    # RGB volume Nifti file
    rg = "r-{}_g-{}_proj_density_{}.nii.gz"
    rgb = "r-{}_g-{}_b-{}_proj_density_{}.nii.gz"

    nifti_rgb = subdir / rg.format(red_id, green_id, args.res)
    if args.blue:
        nifti_rgb = subdir / rgb.format(red_id, green_id, blue_id, args.res)
    check_file_exists(parser, args, nifti_rgb)

    # X-ROIs mask Nifti file
    mask_ = "{}_{}_x-rois_mask_{}_{}.nii.gz"
    xrois_nifti = subdir / mask_.format(
        red_id, green_id, args.res, args.threshold)
    if args.blue:
        mask_ = "{}_{}_{}_x-rois_mask_{}_{}.nii.gz"
        xrois_nifti = subdir / mask_.format(
            red_id, green_id, blue_id, args.res, args.threshold)
    check_file_exists(parser, args, xrois_nifti)

    # X-ROIs json file
    json_ = "{}_{}_x-rois_{}.json"
    xrois_json = subdir / json_.format(red_id, green_id, args.threshold)
    if args.blue:
        json_ = "{}_{}_{}_x-rois_{}.json"
        xrois_json = subdir / json_.format(red_id, green_id, blue_id,
                                           args.threshold)
    check_file_exists(parser, args, xrois_json)

    # Downloading projection density maps
    red_vol = download_proj_density_vol(nrrd_red, red_id,
                                        args.res, args.nocache)
    green_vol = download_proj_density_vol(nrrd_green, green_id,
                                          args.res, args.nocache)
    if args.blue:
        blue_vol = download_proj_density_vol(nrrd_blue, blue_id,
                                             args.res, args.nocache)

    # Transforming manually to RAS+
    red_vol = pretransform_vol_PIR_UserDataSpace(red_vol, user_vol)
    green_vol = pretransform_vol_PIR_UserDataSpace(green_vol, user_vol)
    if args.blue:
        blue_vol = pretransform_vol_PIR_UserDataSpace(blue_vol, user_vol)

    # Converting Allen volumes to float32
    red_vol = red_vol.astype(np.float32)
    green_vol = green_vol.astype(np.float32)
    if args.blue:
        blue_vol = blue_vol.astype(np.float32)

    # Applying ANTsPyX registration
    warped_red = registrate_allen2UserDataSpace(args.file_mat,
                                                red_vol, user_vol, allen_res=args.res)
    warped_green = registrate_allen2UserDataSpace(args.file_mat,
                                                  green_vol, user_vol, allen_res=args.res)
    if args.blue:
        warped_blue = registrate_allen2UserDataSpace(args.file_mat,
                                                     blue_vol, user_vol, allen_res=args.res)

    # Saving Niftis files
    save_nifti(warped_red, user_vol.affine, nifti_red)
    save_nifti(warped_green, user_vol.affine, nifti_green)
    if args.blue:
        save_nifti(warped_blue, user_vol.affine, nifti_blue)

    # Retrieving user_volume shape
    user_shape = user_vol.shape

    # Creating RBGA volume (combining maps)
    rgb_vol = np.zeros((user_shape[0], user_shape[1], user_shape[2], 1, 1),
                       [('R', 'u1'), ('G', 'u1'), ('B', 'u1'), ('A', 'u1')])

    # Filling the volume with RBG values
    for i in range(user_shape[0]):
        for j in range(user_shape[1]):
            for k in range(user_shape[2]):
                if args.blue:
                    if warped_red[i, j, k] == 0 and \
                            warped_green[i, j, k] == 0 and \
                            warped_blue[i, j, k] == 0:
                        rgb_vol[i, j, k] = (0, 0, 0, 0)
                    else:
                        rgb_vol[i, j, k] = (warped_red[i, j, k] * 255,
                                            warped_green[i, j, k] * 255,
                                            warped_blue[i, j, k] * 255,
                                            255)
                else:
                    if warped_red[i, j, k] == 0 and \
                            warped_green[i, j, k] == 0:
                        rgb_vol[i, j, k] = (0, 0, 0, 0)
                    else:
                        rgb_vol[i, j, k] = (warped_red[i, j, k] * 255,
                                            warped_green[i, j, k] * 255,
                                            0,
                                            255)

    # Saving Nifti
    save_nifti(rgb_vol, user_vol.affine, nifti_rgb)

    # Getting Mouse Brain structures ids and names
    # in structure set id "Mouse Connectivity - Target Search"
    structures = stree.get_structures_by_set_id([184527634])
    structures_ids = pd.DataFrame(structures).id.tolist()
    structures_acronym = pd.DataFrame(structures).acronym.tolist()
    structures_names = pd.DataFrame(structures).name.tolist()

    # Getting structures unionized
    unionizes_red = get_unionized_list(red_id, structures_ids)
    unionizes_green = get_unionized_list(green_id, structures_ids)
    if args.blue:
        unionizes_blue = get_unionized_list(blue_id, structures_ids)

    # Searching crossing regions
    hem_ids = [1, 2, 3]
    xrois_ids = []
    xrois_acronyms = []
    xrois_names = []

    for id in unionizes_red.structure_id.tolist():
        # Iterating in each structure
        red_struct = unionizes_red[unionizes_red.structure_id == id]
        green_struct = unionizes_green[unionizes_green.structure_id == id]
        if args.blue:
            blue_struct = unionizes_blue[unionizes_blue.structure_id == id]
        # Iterating in each hemisphere
        for hid in hem_ids:
            red_hem = red_struct[red_struct.hemisphere_id == hid]
            green_hem = green_struct[green_struct.hemisphere_id == hid]
            if args.blue:
                blue_hem = blue_struct[blue_struct.hemisphere_id == hid]
            # Getting projection density value
            red_proj = red_hem.projection_density.tolist()[0]
            green_proj = green_hem.projection_density.tolist()[0]
            if args.blue:
                blue_proj = blue_hem.projection_density.tolist()[0]
            # Saving crossing rois
            if red_proj >= args.threshold and \
                    green_proj >= args.threshold:
                if id not in xrois_ids:
                    structure_name = structures_names[
                        structures_ids.index(id)]
                    structure_acronym = structures_acronym[
                        structures_ids.index(id)]
                    xrois_ids.append(id)
                    xrois_names.append(structure_name)
                    xrois_acronyms.append(structure_acronym)
            if args.blue:
                if blue_proj >= args.threshold and \
                        green_proj >= args.threshold:
                    if id not in xrois_ids:
                        structure_name = structures_names[
                            structures_ids.index(id)]
                        structure_acronym = structures_acronym[
                            structures_ids.index(id)]
                        xrois_ids.append(id)
                        xrois_names.append(structure_name)
                        xrois_acronyms.append(structure_acronym)
                if blue_proj >= args.threshold and \
                        red_proj >= args.threshold:
                    if id not in xrois_ids:
                        structure_name = structures_names[
                            structures_ids.index(id)]
                        structure_acronym = structures_acronym[
                            structures_ids.index(id)]
                        xrois_ids.append(id)
                        xrois_names.append(structure_name)
                        xrois_acronyms.append(structure_acronym)

    # Verifying if x-rois were found
    if len(xrois_names) == 0:
        sys.exit("No crossing-ROIs found...\n"
                 "Please try a lower threshold or "
                 "select others coordinates.")
    else:
        # Configuring X-ROIs json file
        parents_ids_paths = []
        parents_names_paths = []
        for id in xrois_ids:
            parents_ids_path = get_structure_parents_infos(id)[0]
            parents_ids_paths.append(parents_ids_path)
            parents_names_path = get_structure_parents_infos(id)[1]
            parents_names_paths.append(parents_names_path)

        xrois = []
        for i in range(len(xrois_ids)):
            roi = {
                "acronym": xrois_acronyms[i],
                "name": xrois_names[i],
                "parents_names": parents_names_paths[i],
                "parents_ids": parents_ids_paths[i],
                "id": xrois_ids[i]
            }
            xrois.append(roi)

        exps_infos = []
        exps_ids = [red_id, green_id]
        exps_locs = [rloc, gloc]
        exps_rois = [rroi, groi]
        if args.blue:
            exps_ids.append(blue_id)
            exps_locs.append(bloc)
            exps_rois.append(broi)

        for i in range(len(exps_ids)):
            exp = {
                "id": exps_ids[i],
                "region": exps_rois[i],
                "location": exps_locs[i]
            }
            exps_infos.append(exp)

        dic = {"experiments": exps_infos, "x-rois": xrois}

        json_object = json.dumps(dic, indent=4)
        with open(xrois_json, "w") as outfile:
            outfile.write(json_object)

        # Downloading each ROIs masks
        # then merging them into one X-ROIs mask
        bbox_allen = select_allen_bbox(args.res)
        mask_combined = np.zeros(bbox_allen)

        for structure_id in xrois_ids:
            # Creating temporary file
            mask_nrrd = "{}_{}.nrrd".format(structure_id, args.res)
            # Downloading structure mask
            mask = download_struct_mask_vol(mask_nrrd, structure_id,
                                            args.res, args.nocache)
            mask_combined += mask

        # Converting X-ROIs mask to RAS+
        mask_combined = pretransform_vol_PIR_UserDataSpace(mask_combined,
                                                           user_vol)

        # Applying ANTsPy registration
        warped_mask_combined = registrate_allen2UserDataSpace(
            args.file_mat, mask_combined, user_vol, allen_res=args.res)

        # Improving display in MI-Brain
        warped_mask_combined = (warped_mask_combined != 0).astype(np.int32)
        warped_mask_combined[warped_mask_combined > 1] = 1

        # Saving Nifti file
        save_nifti(warped_mask_combined, user_vol.affine, xrois_nifti)


if __name__ == "__main__":
    main()

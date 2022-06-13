#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    Find crossing regions (ROIs) between Allen Mouse Brain Connectivity
    experiments.
    Experiments are found by search in the Allen Mouse Brain Connectivity API
    giving two or three MI-Brain voxel coordinates.\n

    Generate projection density maps for each experiments.
    Maps are downloaded from the Allen Mouse Brain Connectivity API.\n

    Generate a RGB projection density volume combining each
    experiments founded. (--red, --green, --blue).
    At least two colors (coordinates) are mandatory.\n

    Generate a mask at crossing regions if projection density is
    superior to threshold (--threshold) for each experiment founded.
    Masks are download from Allen Mouse Brain Altas.\n

    Generate a json file enumarating each crossing regions.\n

    All files are stored in a same folder.\n

    Examples:
    ---------

    2 colors:

    Injection coordinate search: (--injection)

    >>> allen_crossing_finder.py --red x y z --green x y z
    >>> --injection --dir dir

    Spatial search: (--spatial):

    >>> allen_crossing_finder.py --red x y z --green x y z
    >>> --spatial --dir dir

    3 colors:

    >>> allen_crossing_finder.py --red x y z --green x y z
    >>> --blue x y z --injection --dir dir
"""

import argparse
from email.policy import default
import json
import logging

import os
from pathlib import Path
import sys
from tabnanny import check

import numpy as np
import pandas as pd

from allensdk.api.queries.mouse_connectivity_api import MouseConnectivityApi
from allensdk.api.queries.reference_space_api import ReferenceSpaceApi
from allensdk.core.mouse_connectivity_cache import MouseConnectivityCache
from allensdk.api.queries.tree_search_api import TreeSearchApi

import nibabel as nib
import nrrd
import ants

EPILOG = """
Author : Mahdi
"""


def _build_arg_parser():
    p = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter,
                                epilog=EPILOG, description=__doc__)
    p.add_argument('--red', nargs=3, type=int, required=True,
                   help='MI-Brain voxels coordinates of first experiment.\n'
                        'First experiment will be colored in red.')
    p.add_argument('--green', nargs=3, type=int, required=True,
                   help='MI-Brain voxels coordinates of second experiment.\n'
                        'Second experiment will be colored in green.')
    p.add_argument('--blue', nargs=3, type=int,
                   help='MI-Brain voxels coordinates of third experiment.\n'
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
    p.add_argument('-r', '--res', type=int, default=100, choices=[25, 50, 100],
                   help='Resolution of downloaded files is 100µm by default.\n'
                        '--res <value> will set the resolution to value.')
    p.add_argument('-d', '--dir', default=".",
                   help='Path of the ouptut file directory is . by default.\n'
                        '--dir <dir> will change the output file\'s '
                        'directory or create a new one if does not exits.')
    p.add_argument('-f', dest='overwrite', action="store_true",
                   help='Force overwriting of the output file.')
    p.add_argument('-c', '--nocache', action="store_true",
                   help='Update the Allen Mouse Brain Connectivity Cache')
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
    if 1.0 < args.threshold < 0.0:
        parser.error('Please enter a valid threshold value. '
                     'Pick a float value from 0.0 to 1.0')

    # Verifying coords
    x, y, z = range(0, 165), range(0, 213), range(0, 159)

    if args.red[0] not in x or \
       args.red[1] not in y or \
       args.red[2] not in z:
        parser.error('Red coords invalid. '
                     'x, y, z values must be in [164, 212, 158].')

    if args.green[0] not in x or \
       args.green[1] not in y or \
       args.green[2] not in z:
        parser.error('Green coords invalid. '
                     'x, y, z values must be in [164, 212, 158].')

    if args.blue:
        if args.blue[0] not in x or \
           args.blue[1] not in y or \
           args.blue[2] not in z:
            parser.error('Blue coords invalid. '
                         'x, y, z values must be in [164, 212, 158].')


def check_file_exists(parser, args, path):
    """
    Verify that output does not exist or that if it exists, -f should be used.
    If not used, print parser's usage and exit.

    Parameters
    ----------
    parser: argparse.ArgumentParser object
        Parser.
    args: argparse namespace
        Argument list.
    path: string or path to file
        Required path to be checked.
    """
    if os.path.isfile(path) and not args.overwrite:
        parser.error('Output file {} exists. Use -f to force '
                     'overwriting'.format(path))

    path_dir = os.path.dirname(path)
    if path_dir and not os.path.isdir(path_dir):
        parser.error('Directory {}/ \n for a given output file '
                     'does not exists.'.format(path_dir))


def get_allen_coords(mib_coords, res=25):
    """
    Compute the Allen coordinates from
    MI-Brain coordinates.\n
    Resolution is fixed to 25 to ensure
    best precision.

    Parameters
    ----------
    args: argparse namespace
        Argument list.
    res: int
        Resolution of the transformation matrix.

    Return
    ------
    list: Allen coordinates in micron.
    """
    # Reading transform matrix
    file_mat = f'./utils/transformations_allen2avgt/allen2avgtAffine_{res}.mat'
    tx = ants.read_transform(file_mat)

    # Getting allen voxels RAS+ coords
    allen_ras = tx.apply_to_point(mib_coords)

    # Converting to PIR (microns)
    p, i, r = 13200//res, 8000//res, 11400//res
    r_, a, s = r, p, i
    x, y, z = allen_ras[0], allen_ras[1], allen_ras[2]
    x_, y_, z_ = (a-y)*res, (s-z)*res, x*res
    allen_pir = [x_, y_, z_]

    return list(map(int, allen_pir))


def search_experiments(args, seed_point):
    """
    Retrieve Allen experiments
    from a seed point.\n
    Using `injection coordinate search` or
    `spatial search`.

    Parameters
    ----------
    args: argparse namespace
        Argument list.
    seed_point: list of int
        Coordinate of the seed point
        in Allen reference space.

    Return
    ------
    dic: Allen experiments founded.
    """
    mca = MouseConnectivityApi()

    # Injection coordinate search
    if args.injection:
        exps = mca.experiment_injection_coordinate_search(
            seed_point=seed_point)

    # Spatial search
    if args.spatial:
        exps = mca.experiment_spatial_search(
            seed_point=seed_point)

    return exps


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


def loc_injection_coordinates(id, allen_experiments):
    """
    Return the injection coordinate position
    of an experiment. (Left or Right)

    Parameters
    ----------
    id: long
        Allen experiment id.
    experiments: dataframe
        Allen Mouse Connectivity experiments.

    Return
    ------
    string: Injection location (R or L).
    """
    inj_coord = allen_experiments.loc[id]['injection-coordinates']

    # Returning the position and its location
    # Right is >= than z/2
    if inj_coord[2] >= 11400/2:
        return 'R'
    else:
        return 'L'


def get_mcc(args):
    """
    Get Allen Mouse Connectivity Cache.\n
    Update it by removing and downloading cache file
    using --nocache.

    Parameters
    ----------
    args: argparse namespace
        Argument list.

    Return
    ------
    dataframe :
        Allen Mouse Connectivity experiments
        Allen Mouse Brain structure tree
    """
    experiments_path = './utils/cache/allen_mouse_conn_experiments.json'
    manifest_path = './utils/cache/mouse_conn_manifest.json'
    structures_path = './utils/cache/structures.json'

    if args.nocache:
        if os.path.isfile(experiments_path) and os.path.isfile(manifest_path):
            os.remove(experiments_path)
            os.remove(manifest_path)
            os.remove(structures_path)

    mcc = MouseConnectivityCache(manifest_file=manifest_path)
    experiments = mcc.get_experiments(dataframe=True,
                                      file_name=experiments_path)
    stree = mcc.get_structure_tree(file_name=structures_path)

    return pd.DataFrame(experiments), stree


def get_experiment_info(allen_experiments, id):
    """
    Retrieve the injection ROI and location (L/R)
    of an Allen experiment.

    Parameters
    ----------
    allen_experiments: dataframe
        Allen experiments.
    id: long
        Experiment id.

    Returns
    -------
    string: Roi acronym.
    string: Injection location (R or L).
    """
    roi = allen_experiments.loc[id]['structure-abbrev']
    loc = loc_injection_coordinates(id, allen_experiments)

    return roi, loc


def pretransform_PIR_to_RAS(vol):
    """
    Manually transform a PIR reference space to RAS+.

    Parameters
    ----------
    vol: ndarray
        PIR volume to transform.

    Return
    ------
    ndarray: vol
        Transformed volume into RAS+
    """
    # Switching axis
    # +x, +y, +z (RAS) -> +z, -x, -y (PIR)
    vol = np.moveaxis(vol, (0, 1, 2), (1, 2, 0))
    vol = np.flip(vol, axis=2)
    vol = np.flip(vol, axis=1)

    return vol


def registrate_allen2avgt_ants(args, allen_vol, avgt_vol):
    """
    Align a 3D allen volume on AVGT.
    Using ANTsPyX registration.

    Parameters
    ----------
    args: argparse namespace
        Argument list.
    allen_vol: float32 ndarray
        Allen volume to registrate
    avgt_vol: float32 ndarray
        AVGT reference volume

    Return
    ------
    ndarray: Warped volume.
    """
    # Creating and reshaping ANTsPyx images for registration
    # Moving : Allen volume
    # Fixed : AVGT volume
    fixed = ants.from_numpy(avgt_vol).resample_image((164, 212, 158), 1, 0)
    moving = ants.from_numpy(allen_vol).resample_image((164, 212, 158), 1, 0)

    # Loading pre-calculated transformations (ANTsPyx registration)
    tx_nifti = './utils/transformations_allen2avgt/allen2avgt_{}.nii.gz'
    tx_mat = './utils/transformations_allen2avgt/allen2avgtAffine_{}.mat'
    transformations = [tx_nifti.format(args.res),
                       tx_mat.format(args.res)]

    # Applying thoses transformations
    interp = 'nearestNeighbor'
    warped_moving = ants.apply_transforms(fixed=fixed,  moving=moving,
                                          transformlist=transformations,
                                          interpolator=interp)

    return warped_moving.numpy()


def get_unionized_list(exp_id, struct_ids):
    """
    Get the unionized structures
    of an Allen experiment.

    Parameters
    ----------
    exp_id: long
        Id of Allen experiment.
    struct_ids: list
        Ids of structures in Allen
        Mouse Brain Atlas.

    Returns
    -------
    dataframe: Unionized structures.
    """
    # Diving mouse brain structures ids
    # into 5 arrays (for API call purposes)
    struct_ids_a = struct_ids[0:len(struct_ids)//5]
    struct_ids_b = struct_ids[len(struct_ids)//5:len(struct_ids)*2//5]
    struct_ids_c = struct_ids[len(struct_ids)*2//5:len(struct_ids)*3//5]
    struct_ids_d = struct_ids[len(struct_ids)*3//5:len(struct_ids)*4//5]
    struct_ids_e = struct_ids[len(struct_ids)*4//5:len(struct_ids)]

    # Getting structures unionized
    mca = MouseConnectivityApi()
    unionizes_a = mca.get_structure_unionizes(
        experiment_ids=[exp_id],
        is_injection=False,
        structure_ids=struct_ids_a)
    unionizes_b = mca.get_structure_unionizes(
        experiment_ids=[exp_id],
        is_injection=False,
        structure_ids=struct_ids_b)
    unionizes_c = mca.get_structure_unionizes(
        experiment_ids=[exp_id],
        is_injection=False,
        structure_ids=struct_ids_c)
    unionizes_d = mca.get_structure_unionizes(
        experiment_ids=[exp_id],
        is_injection=False,
        structure_ids=struct_ids_d)
    unionizes_e = mca.get_structure_unionizes(
        experiment_ids=[exp_id],
        is_injection=False,
        structure_ids=struct_ids_e)

    # Creating dataframes
    unionizes_a = pd.DataFrame(unionizes_a)[
        ['hemisphere_id',
         'structure_id',
         'projection_density']]
    unionizes_b = pd.DataFrame(unionizes_b)[
        ['hemisphere_id',
         'structure_id',
         'projection_density']]
    unionizes_c = pd.DataFrame(unionizes_c)[
        ['hemisphere_id',
         'structure_id',
         'projection_density']]
    unionizes_d = pd.DataFrame(unionizes_d)[
        ['hemisphere_id',
         'structure_id',
         'projection_density']]
    unionizes_e = pd.DataFrame(unionizes_e)[
        ['hemisphere_id',
         'structure_id',
         'projection_density']]

    # Returning concat dataframe
    fnames = [unionizes_a, unionizes_b, unionizes_c,
              unionizes_d, unionizes_e]
    return pd.concat(fnames)


def get_structure_parents_infos(structure_id):
    """
    Get the path of ids and names of the
    parents of a Allen Mouse Brain Atlas structure.

    Parameters
    ----------
    structure_id: long
        Allen Mouse Brain Atlas structure id.

    Returns
    -------
    string: Path of parents ids's
    string: Path of parents names's
    """
    # Getting ancestor tree of the structure
    tsa = TreeSearchApi()
    tree = tsa.get_tree(kind='Structure', db_id=structure_id,
                        ancestors=True)
    df_tree = pd.DataFrame(tree)

    # Retrieving parents ids and names path
    parents_ids_path = df_tree.structure_id_path[len(df_tree)-1]
    parents = df_tree.safe_name[0:len(df_tree)].tolist()
    parents_names_path = "\n\_".join(map(str, parents))

    return parents_ids_path, parents_names_path


def main():
    # Building argparser
    parser = _build_arg_parser()
    args = parser.parse_args()

    # Verying args validity
    check_args(parser, args)

    # Getting experiments from Mouse Connectivity Cache
    allen_experiments = get_mcc(args)[0]
    stree = get_mcc(args)[1]
    # API
    mca = MouseConnectivityApi()

    # Configuring output directory
    args.dir = Path(args.dir)
    args.dir.mkdir(exist_ok=True, parents=True)

    # AVGT settings
    avgt_file = './utils/AVGT.nii.gz'
    avgt_affine = nib.load(avgt_file).affine
    avgt_vol = nib.load(avgt_file).get_fdata().astype(np.float32)

    # Getting Allen coords
    allen_red_coords = get_allen_coords(args.red)
    allen_green_coords = get_allen_coords(args.green)
    if args.blue:
        allen_blue_coords = get_allen_coords(args.blue)

    # Searching Allen experiments
    red_exps = search_experiments(args, allen_red_coords)
    green_exps = search_experiments(args, allen_green_coords)
    if args.blue:
        blue_exps = search_experiments(args, allen_blue_coords)

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
    subdir_path = f"{red_id}_{green_id}_crossing_{args.res}"
    subdir = Path(args.dir / subdir_path)
    subdir.mkdir(exist_ok=True, parents=True)
    if args.blue:
        subdir_path = f"{red_id}_{green_id}_{blue_id}_crossing_{args.res}"
        subdir = Path(args.dir / subdir_path)
        subdir.mkdir(exist_ok=True, parents=True)

    # Retrieving experiment informations
    rroi, rloc = get_experiment_info(allen_experiments, red_id)
    groi, gloc = get_experiment_info(allen_experiments, green_id)
    if args.blue:
        broi, bloc = get_experiment_info(allen_experiments, blue_id)

    # Projection density maps Niftis and Nrrd files
    nrrd_ = "{}_{}_{}_proj_density_{}.nrrd"
    nifti_ = "{}_{}_{}_proj_density_{}.nii.gz"

    nrrd_red = subdir / nrrd_.format(red_id, rroi, rloc, args.res)
    nifti_red = subdir / nifti_.format(red_id, rroi, rloc, args.res)
    check_file_exists(parser, args, nifti_red)

    nrrd_green = subdir / nrrd_.format(green_id, groi, gloc, args.res)
    nifti_green = subdir / nifti_.format(green_id, groi, gloc, args.res)
    check_file_exists(parser, args, nifti_green)

    if args.blue:
        nrrd_blue = subdir / nrrd_.format(blue_id, broi, bloc, args.res)
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
    mask_ = "{}_{}_x-rois_mask_{}.nii.gz"
    xrois_nifti = subdir / mask_.format(red_id, green_id, args.res)
    if args.blue:
        mask_ = "{}_{}_{}_x-rois_mask_{}.nii.gz"
        xrois_nifti = subdir / mask_.format(
            red_id, green_id, blue_id, args.res)
    check_file_exists(parser, args, xrois_nifti)

    # X-ROIs json file
    json_ = "{}_{}_x-rois.json"
    xrois_json = subdir / json_.format(red_id, green_id)
    if args.blue:
        json_ = "{}_{}_{}_x-rois.json"
        xrois_json = subdir / json_.format(red_id, green_id, blue_id)
    check_file_exists(parser, args, xrois_json)

    # Downloading projetion density maps
    mca.download_projection_density(
        nrrd_red,
        experiment_id=red_id,
        resolution=args.res)

    mca.download_projection_density(
        nrrd_green,
        experiment_id=green_id,
        resolution=args.res)

    if args.blue:
        mca.download_projection_density(
            nrrd_blue,
            experiment_id=blue_id,
            resolution=args.res)

    # Getting Allen volumes and deleting nrrd tmps files
    red_vol, header = nrrd.read(nrrd_red)
    green_vol, header = nrrd.read(nrrd_green)
    if args.blue:
        blue_vol, header = nrrd.read(nrrd_blue)
        os.remove(nrrd_blue)
    os.remove(nrrd_red)
    os.remove(nrrd_green)

    # Transforming manually to RAS+
    red_vol = pretransform_PIR_to_RAS(red_vol)
    green_vol = pretransform_PIR_to_RAS(green_vol)
    if args.blue:
        blue_vol = pretransform_PIR_to_RAS(blue_vol)

    # Converting Allen volumes to float32
    red_vol = red_vol.astype(np.float32)
    green_vol = green_vol.astype(np.float32)
    if args.blue:
        blue_vol = blue_vol.astype(np.float32)

    # Applying ANTsPyX registration
    warped_red = registrate_allen2avgt_ants(
        args=args,
        allen_vol=red_vol,
        avgt_vol=avgt_vol)

    warped_green = registrate_allen2avgt_ants(
        args=args,
        allen_vol=green_vol,
        avgt_vol=avgt_vol)

    if args.blue:
        warped_blue = registrate_allen2avgt_ants(
            args=args,
            allen_vol=blue_vol,
            avgt_vol=avgt_vol)

    # Saving Niftis files
    red_img = nib.Nifti1Image(warped_red, avgt_affine)
    nib.save(red_img, nifti_red)

    green_img = nib.Nifti1Image(warped_green, avgt_affine)
    nib.save(green_img, nifti_green)

    if args.blue:
        blue_img = nib.Nifti1Image(warped_blue, avgt_affine)
        nib.save(blue_img, nifti_blue)

    # Creating RBGA volume (combining maps)
    rgb_vol = np.zeros((164, 212, 158, 1, 1),
                       [('R', 'u1'), ('G', 'u1'), ('B', 'u1'), ('A', 'u1')])

    # Filling the volume with RBG values
    for i in range(164):
        for j in range(212):
            for k in range(158):
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
    rgb_img = nib.Nifti1Image(rgb_vol, avgt_affine)
    nib.save(rgb_img, nifti_rgb)

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
            if args.blue:
                if red_proj >= args.threshold and \
                   green_proj >= args.threshold and \
                   blue_proj >= args.threshold:
                    if id not in xrois_ids:
                        structure_name = structures_names[
                            structures_ids.index(id)]
                        xrois_ids.append(id)
                        xrois_names.append(structure_name)
            else:
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

    # Verifying if x-rois were found
    if len(xrois_names) == 0:
        sys.exit("No crossing-ROIs founded ...\n"
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
        exps_ids = [red_id,  green_id]
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
        rsa = ReferenceSpaceApi()

        bbox_allen = (13200//args.res, 8000//args.res, 11400//args.res)
        mask_combined = np.zeros(bbox_allen)

        for structure_id in xrois_ids:
            # Creating temporary file
            mask_nrrd = subdir / f"{structure_id}_mask.nrrd"
            # Downloading structure mask
            rsa.download_structure_mask(
                structure_id=structure_id,
                ccf_version=rsa.CCF_VERSION_DEFAULT,
                resolution=args.res,
                file_name=mask_nrrd
                )
            # Adding it in the combined volume
            mask, header = nrrd.read(mask_nrrd)
            mask_combined += mask
            os.remove(mask_nrrd)

        # Converting X-ROIs mask to RAS+
        mask_combined = pretransform_PIR_to_RAS(mask_combined)

        # Applying ANTsPy registration
        warped_mask_combined = registrate_allen2avgt_ants(
            args=args,
            allen_vol=mask_combined,
            avgt_vol=avgt_vol
        )

        # Improving display in MI-Brain
        warped_mask_combined = (warped_mask_combined != 0).astype(np.int32)
        warped_mask_combined[warped_mask_combined > 1] = 1

        # Saving Nifti file
        msk = nib.Nifti1Image(warped_mask_combined, avgt_affine)
        nib.save(msk, xrois_nifti)


if __name__ == "__main__":
    main()

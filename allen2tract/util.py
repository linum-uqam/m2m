import os
from pathlib import Path
import pandas as pd
import numpy as np
import nibabel as nib
from allensdk.core.mouse_connectivity_cache import MouseConnectivityCache
from allensdk.api.queries.mouse_connectivity_api import MouseConnectivityApi
from allensdk.api.queries.reference_space_api import ReferenceSpaceApi
from allensdk.api.queries.tree_search_api import TreeSearchApi
import nrrd
from allen2tract.control import get_cached_dir


def load_avgt():
    """
    Load AVGT reference template.
    """
    avgt_file = os.path.join(get_cached_dir("data"), 'AVGT.nii.gz')
    return nib.load(avgt_file)


def save_nii(vol, path):
    """
    Create a Nifti image and
    save it.

    Parameters
    ----------
    vol: ndarray
        Image data.
    path: string
        Path to the output file.
    """
    affine = load_avgt().affine
    img = nib.Nifti1Image(vol, affine)
    nib.save(img, path)


def get_mcc(nocache, res):
    """
    Get Allen Mouse Connectivity Cache.

    Parameters
    ----------
    nocache: bool
        Whether use cache of not.

    Returns
    -------
    mcc: MouseConnectivityCache()
    """
    manifest_path = os.path.join(get_cached_dir("cache"),
                                 'mouse_conn_manifest.json')

    if nocache:
        if os.path.isfile(manifest_path):
            os.remove(manifest_path)

    return MouseConnectivityCache(resolution=res, manifest_file=manifest_path)


def get_mcc_exps(nocache):
    """
    Get Mouse Connectivity Cache experiments

    Parameters
    ----------
    nocache: bool
        Whether use cache of not

    Return
    ------
    dataframe : Allen Mouse Connectivity experiments
    """
    mcc = get_mcc(nocache, None)
    experiments_path = os.path.join(get_cached_dir("cache"),
                                    'allen_mouse_conn_experiments.json')

    if nocache:
        if os.path.isfile(experiments_path):
            os.remove(experiments_path)

    experiments = mcc.get_experiments(dataframe=True,
                                      file_name=experiments_path)

    return pd.DataFrame(experiments)


def get_mcc_stree(nocache):
    """
    Get allen Mouse Brain structure tree

    Parameters
    ----------
    nocache: bool
        Whether use cache of not

    Return
    ------
    dataframe : Allen Mouse Brain structure tree
    """
    mcc = get_mcc(nocache, None)
    structures_path = os.path.join(get_cached_dir("cache"), 'structures.json')

    if nocache:
        if os.path.isfile(structures_path):
            os.remove(structures_path)

    return mcc.get_structure_tree(file_name=structures_path)


def get_injection_infos(allen_experiments, id):
    """
    Retrieve the injection coordinates, region
    and location (L/R) of an Allen experiment.

    Parameters
    ----------
    allen_experiments: dataframe
        Allen experiments.
    id: long
        Experiment id.

    Returns
    -------
    string: Roi acronym.
    list: coordinates of the injection coordinates
    string: Injection location (R or L).
    """
    roi = allen_experiments.loc[id].structure_abbrev
    inj_x = allen_experiments.loc[id].injection_x
    inj_y = allen_experiments.loc[id].injection_y
    inj_z = allen_experiments.loc[id].injection_z
    pos = [inj_x, inj_y, inj_z]
    if inj_z >= 11400/2:
        loc = 'R'
    else:
        loc = 'L'

    return roi, pos, loc


def draw_spherical_mask(shape, radius, center):
    """
    Generate an n-dimensional spherical mask.

    Parameters
    ----------
    shape: tuple
        Shape of the volume created.
    radius: int/float
        Radius of the spherical mask.
    center: tuple
        Position of the center of the spherical mask.

    Return
    ------
    ndarray: Volume containing the spherical mask.
    """
    # Assuming shape and center have the same length and contain ints
    # (the units are pixels / voxels (px for short),
    # radius is a int or float in px)
    assert len(center) == len(shape)
    semisizes = (radius,) * len(shape)

    # Generating the grid for the support points
    # centered at the position indicated by center
    grid = [slice(-x0, dim - x0) for x0, dim in zip(center, shape)]
    center = np.ogrid[grid]

    # Calculating the distance of all points from center
    # scaled by the radius
    vol = np.zeros(shape, dtype=float)
    for x_i, semisize in zip(center, semisizes):
        vol += (x_i / semisize) ** 2

    # the inner part of the sphere will have distance below or equal to 1
    return vol <= 1.0


def download_proj_density_vol(file, id, res, nocache):
    """
    """
    cache_dir = Path(get_cached_dir('cache_proj_density'))
    cache_dir.mkdir(exist_ok=True, parents=True)
    if not os.path.isfile(cache_dir / file):
        mcc = get_mcc(nocache, res)
        mcc.get_projection_density(
            file_name=cache_dir / file,
            experiment_id=id)
    vol, hdr = nrrd.read(cache_dir / file)
    if nocache:
        os.remove(cache_dir / file)
    return vol


def download_struct_mask_vol(file, id, res, nocache):
    """
    """
    cache_dir = Path(get_cached_dir('cache_struct_mask'))
    cache_dir.mkdir(exist_ok=True, parents=True)
    if not os.path.isfile(cache_dir / file):
        rsa = ReferenceSpaceApi()
        rsa.download_structure_mask(
            structure_id=id,
            ccf_version=rsa.CCF_VERSION_DEFAULT,
            resolution=res,
            file_name=cache_dir / file
                )
    vol, hdr = nrrd.read(cache_dir / file)
    if nocache:
        os.remove(cache_dir / file)
    return vol


def get_unionized_list(exp_id, structs_ids):
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
    mcc = get_mcc(nocache=False, res=None)
    u_list = mcc.get_structure_unionizes(
        experiment_ids=[exp_id],
        is_injection=False,
        structure_ids=structs_ids,
    )
    return pd.DataFrame(u_list)[['hemisphere_id',
                                 'structure_id', 'projection_density']]


def search_experiments(injection, spatial, seed_point):
    """
    Retrieve Allen experiments
    from a seed point.\n
    Using `injection coordinate search` or
    `spatial search`.

    Parameters
    ----------
    injection: bool
        Using `injection coordinate search`.
    spatial: bool
        Using `spatial search`.
    seed_point: list of int
        Coordinate of the seed point
        in Allen reference space.

    Return
    ------
    dic: Allen experiments founded.
    """
    mca = MouseConnectivityApi()

    # Injection coordinate search
    if injection:
        exps = mca.experiment_injection_coordinate_search(
            seed_point=seed_point)

    # Spatial search
    if spatial:
        exps = mca.experiment_spatial_search(
            seed_point=seed_point)

    return exps


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
    parents_names_path = " / ".join(map(str, parents))

    return parents_ids_path, parents_names_path

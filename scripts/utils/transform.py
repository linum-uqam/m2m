import numpy as np
import ants

from utils.util import (get_injection_infos, load_avgt)


def pretransform_vol_PIR_RAS(vol):
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


def pretransform_point_PIR_RAS(point, res):
    """
    Transform a point in the Allen Mouse Brain Atlas
    PIR reference space (microns) to the AVGT RAS
    reference space (voxels).

    Parameters
    ----------
    point: list
        Allen PIR microns coordinates.
    res: int
        Allen resolution.

    Returns
    -------
    list: RAS voxels coords
    """
    p, i, r = 13200//res, 8000//res, 11400//res
    x, y, z = point[0]/res, point[1]/res, point[2]/res
    x_, y_, z_ = z, p-x, i-y

    return [x_, y_, z_]


def pretransform_point_RAS_PIR(point, res):
    """
    Transform a point in the Allen Mouse Brain Atlas
    reference space in RAS+ (voxels) to the Allen
    Mouse Brain Atlas PIR reference space (microns).

    Parameters
    ----------
    point: list
        Allen PIR microns coordinates.
    res: int
        Allen resolution.

    Returns
    -------
    list: PIR microns coords
    """
    p, i, r = 13200//res, 8000//res, 11400//res
    r_, a, s = r, p, i
    x, y, z = point[0], point[1], point[2]
    x_, y_, z_ = (a-y)*res, (s-z)*res, x*res

    return [x_, y_, z_]


def load_allen2avgt_transformations(res):
    """
    Load ANTsPy transform file.

    Parameters
    ----------
    res: int in [25, 50 ,100]
        Resolution of the transformation.
        Depending the resolution of the file to register.

    Return
    ------
    list: Transform list.
    """
    tx_nifti = './data/transformations_allen2avgt/allen2avgt_{}.nii.gz'
    tx_mat = './data/transformations_allen2avgt/allen2avgtAffine_{}.mat'
    return [tx_nifti.format(res), tx_mat.format(res)]


def registrate_allen2avgt_ants(res, allen_vol, smooth=False):
    """
    Align a 3D allen volume on AVGT.
    Using ANTsPyX registration.

    Parameters
    ----------
    res: int in [25, 50 ,100]
        Resolution of the transformation.
    allen_vol: float32 ndarray
        Allen volume to registrate.
    smooth: boolean
        bSpline interpolation.

    Return
    ------
    ndarray: Warped volume.
    """
    # Creating and reshaping ANTsPyx images for registration
    # Moving : Allen volume
    # Fixed : AVGT volume
    avgt_vol = load_avgt().get_fdata().astype(np.float32)
    fixed = ants.from_numpy(avgt_vol)
    moving = ants.from_numpy(allen_vol)

    # Loading pre-calculated transformations (ANTsPyx registration)
    transformations = load_allen2avgt_transformations(res)

    # Applying thoses transformations
    interp = 'nearestNeighbor'
    if smooth:
        interp = 'bSpline'

    warped_moving = ants.apply_transforms(fixed=fixed,  moving=moving,
                                          transformlist=transformations,
                                          interpolator=interp)

    return warped_moving.numpy()


def get_mib_coords(args, allen_experiments):
    """
    Get MI-Brain voxels coords
    of the experiment injection coordinates.

    Parameters
    ----------
    args: argparse namespace
        Argument list.

    Return
    ------
    list: MI-Brain coords
    """
    # Loading transform matrix
    file_mat = load_allen2avgt_transformations(args.res)[1]

    # Defining invert transformation
    itx = ants.read_transform(file_mat).invert()

    # Converting injection coordinates position to voxels
    allen_pir_um = get_injection_infos(allen_experiments, args.id)[1]

    # Converting injection coordinates voxels position to ras
    allen_ras_vox = pretransform_point_PIR_RAS(allen_pir_um, args.res)

    # Converting injection coordinates voxels ras position to mi-brain voxels
    mib_vox = itx.apply_to_point(allen_ras_vox)

    return mib_vox


def get_allen_coords(mib_coords, res=25):
    """
    Compute the Allen coordinates from
    MI-Brain coordinates.\n
    Resolution is fixed to 25 to ensure
    best precision.

    Parameters
    ----------
    mib_coords: tuple
        MI-Brain voxel coordinates.
    res: int
        Resolution of the transformation matrix.

    Return
    ------
    list: Allen coordinates in micron.
    """
    # Reading transform matrix
    file_mat = load_allen2avgt_transformations(res)[1]
    tx = ants.read_transform(file_mat)

    # Getting allen voxels RAS+ coords
    allen_ras = tx.apply_to_point(mib_coords)

    # Converting to PIR (microns)
    allen_pir = pretransform_point_RAS_PIR(allen_ras, res)

    return list(map(int, allen_pir))

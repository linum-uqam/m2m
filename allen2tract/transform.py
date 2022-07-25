from pickle import GET
import numpy as np
from tqdm import tqdm
import os
from allen2tract.allensdk_utils import get_injection_infos
import nibabel as nib
import matplotlib
matplotlib.use('TkAgg')
import ants
import functools as ftools
from scipy.io import loadmat
from dipy.tracking.life import transform_streamlines


def get_ornt_PIR_UserDataSpace(user_vol):
    """
    """
    ornt_pir = nib.orientations.axcodes2ornt(('P', 'I', 'R'))

    user_axcodes = nib.aff2axcodes(user_vol.affine)
    ornt_user = nib.orientations.axcodes2ornt(user_axcodes)

    ornt_pir2user = nib.orientations.ornt_transform(ornt_pir, ornt_user)

    return ornt_pir2user


def get_ornt_UserDataSpace_PIR(user_vol):
    """
    """
    ornt_pir = nib.orientations.axcodes2ornt(('P', 'I', 'R'))

    user_axcodes = nib.aff2axcodes(user_vol.affine)
    ornt_user = nib.orientations.axcodes2ornt(user_axcodes)

    ornt_user2pir = nib.orientations.ornt_transform(ornt_user, ornt_pir)

    return ornt_user2pir


def pretransform_vol_PIR_UserDataSpace(vol, user_vol):
    """
    Transform a PIR reference space to User Data Space.

    Parameters
    ----------
    vol: ndarray
        PIR volume to transform.
    user_vol: volume (from nib.load())
        X-oriented volume.

    Return
    ------
    ndarray: vol
        Transformed volume into User Data Space
    """
    vol_reorient = nib.orientations.apply_orientation(
        vol,
        get_ornt_PIR_UserDataSpace(user_vol)) # passer en para # checker l'impact autres scripts
    
    return vol_reorient


def pretransform_vol_UserDataSpace_PIR(user_vol, vol):
    """
    Transform a User volume to Allen Space.

    Parameters
    ----------
    user_vol: (from nib.load())
        user volume to transform.
    vol: ndarray
        PIR oriented volume.

    Return
    ------
    ndarray: vol
        Transformed volume into Allen Space
    """
    vol_reorient = nib.orientations.apply_orientation(
        vol,
        get_ornt_UserDataSpace_PIR(user_vol)) # passer en para pour accelerer

    return vol_reorient


def select_allen_bbox(res):
    """
    """
    return (13200//res, 8000//res, 11400//res)


def pretransform_point_PIR_UserDataSpace(point,
                                         allen_bbox, user_vol):
    """
    """
    # Creating a fake volume to reorient the point
    fake_allen_vol = np.zeros(allen_bbox, np.int32)
    fake_allen_vol[point[0], point[1], point[2]] = 1
    fake_allen_vol_reorient = pretransform_vol_PIR_UserDataSpace(
        fake_allen_vol, user_vol)

    # Getting the reoriented point in UserDataSpace
    x, y, z = np.where(fake_allen_vol_reorient == np.amax(
                       fake_allen_vol_reorient))

    return [x[0], y[0], z[0]]


def pretransform_point_UserDataSpace_PIR(point,
                                         allen_bbox, user_vol):
    """
    """
    # Creating a fake volume to reorient the point
    fake_allen_vol = np.zeros(allen_bbox, np.int32)
    fake_allen_vol_reorient = pretransform_vol_PIR_UserDataSpace(
        fake_allen_vol, user_vol)
    fake_allen_vol_reorient[point[0], point[1], point[2]] = 1

    # Getting the reoriented point in PIR voxels
    fake_allen_vol_reverted = pretransform_vol_UserDataSpace_PIR(
        user_vol, fake_allen_vol_reorient)
    x, y, z = np.where(fake_allen_vol_reverted == np.amax(
                       fake_allen_vol_reverted))

    return [x[0], y[0], z[0]]


def registrate_allen2UserDataSpace(file_mat, allen_vol, user_vol,
                                   smooth=False):
    """
    Align a 3D allen volume on User volume.
    Using ANTsPyX registration.

    Parameters
    ----------
    file_mat: string
        Path to transform matrix
    allen_vol: ndarray
        Allen volume to registrate.
    user_vol: (from nib.load())
        User reference volume.
    smooth: boolean
        bSpline interpolation.

    Return
    ------
    ndarray: Warped volume.
    """
    # Creating and reshaping ANTsPyx images for registration
    # Moving : Allen volume
    # Fixed : AVGT volume
    fixed = ants.from_numpy(user_vol.get_fdata().astype(np.float32))
    moving = ants.from_numpy(allen_vol.astype(np.float32))

    # Selecting interpolator
    interp = 'nearestNeighbor'
    if smooth:
        interp = 'bSpline'

    return ants.apply_transforms(fixed=fixed, moving=moving,
                                 transformlist=file_mat,
                                 interpolator=interp).numpy()


def compute_transform_matrix(moving_vol, fixed_vol):
    """
    Compute an Affine transformation matrix
    to align Allen average template on User template.
    Using ANTsPyX registration.

    Parameters
    ----------
    moving_vol: volume
        Allen volume (from nrrd.read()).
    fixed_vol: volume
        Fixed volume (from nib.load()).

    Return
    ------
    string: Path of the transform matrix.
    """
    moving = ants.from_numpy(moving_vol.astype(np.float32))
    fixed = ants.from_numpy(fixed_vol.get_fdata().astype(np.float32))

    mytx = ants.registration(fixed=fixed,
                             moving=moving,
                             type_of_transform='Affine')

    return mytx['fwdtransforms'][0]


def convert_point_to_vox(point, res):
    """
    """
    return [point[0]//res, point[1]//res, point[2]//res]


def get_user_coords(allen_coords, res, file_mat, user_vol, allen_bbox,
                    to_vox=False):
    """
    refactor ? pour tps d'exec
    """
    if to_vox:
        # Converting injection coordinates position to voxels
        allen_pir_vox = convert_point_to_vox(allen_coords, res)
    else:
        # Assuming that the point is already in voxel
        allen_pir_vox = allen_coords
    allen_pir_vox = list(map(int, allen_pir_vox))

    # Reorienting the point in UserDataSpace
    reoriented_coords = pretransform_point_PIR_UserDataSpace(
        allen_pir_vox, allen_bbox, user_vol)
    # Applying invert ANTsPyX transformation on this point
    tx = ants.read_transform(file_mat)
    user_coords = tx.invert().apply_to_point(reoriented_coords)

    if to_vox:
        return list(map(int, user_coords))
    else:
        return user_coords


def get_uzer_coords(allen_coords, bbox_allen, tx, ornt_pir2user, ornt_user2pir):
    """
    """
    user_coords = [0, 0, 0]
    user_coords[int(ornt_pir2user[0][0])] = allen_coords[0] * ornt_user2pir[int(ornt_pir2user[0][0])][1]
    user_coords[int(ornt_pir2user[1][0])] = allen_coords[1] * ornt_user2pir[int(ornt_pir2user[1][0])][1]
    user_coords[int(ornt_pir2user[2][0])] = allen_coords[2] * ornt_user2pir[int(ornt_pir2user[2][0])][1]

    for i in range(len(user_coords)):
        if user_coords[i] < 0:
            user_coords[i] += bbox_allen[int(ornt_pir2user[:,0].tolist().index(i))]

    return tx.invert().apply_to_point(user_coords)

def convert_point_to_um(point, res):
    """
    """
    return [point[0]*res, point[1]*res, point[2]*res]


def get_allen_coords(user_coords, res, file_mat, user_vol,
                     allen_bbox):
    """
    """
    # Reading transform matrix
    tx = ants.read_transform(file_mat)

    # Getting allen vox coords in User Data Space
    allen_vox_user = tx.apply_to_point(user_coords)
    allen_vox_user = list(map(int, allen_vox_user))

    # Reorient the point in Allen Space voxel
    allen_pir_vox = pretransform_point_UserDataSpace_PIR(
        allen_vox_user, allen_bbox, user_vol)

    return convert_point_to_um(allen_pir_vox, res)


def load_matrix_in_any_format(filepath):
    _, ext = os.path.splitext(filepath)
    if ext == '.txt':
        data = np.loadtxt(filepath)
    elif ext == '.npy':
        data = np.load(filepath)
    elif ext == '.mat':
        # .mat are actually dictionnary. This function support .mat from
        # antsRegistration that encode a 4x4 transformation matrix.
        transfo_dict = loadmat(filepath)
        lps2ras = np.diag([-1, -1, 1])

        rot = transfo_dict['AffineTransform_float_3_3'][0:9].reshape((3, 3))
        trans = transfo_dict['AffineTransform_float_3_3'][9:12]
        offset = transfo_dict['fixed']
        r_trans = (np.dot(rot, offset) - offset - trans).T * [1, 1, -1]

        data = np.eye(4)
        data[0:3, 3] = r_trans
        data[:3, :3] = np.dot(np.dot(lps2ras, rot), lps2ras)
    else:
        raise ValueError('Extension {} is not supported'.format(ext))

    return data


def registrate_allen_streamlines(streamlines,
                                 file_mat, user_vol, res):
    """
    Align allen streamlines on the AVGT.

    Parameters
    ----------
    streamlines: array of arrays
        Streamlines array.
    $$$$$$$$$$$$$$$$
    $              $
    $   REMPLIR !  $
    $              $
    $$$$$$$$$$$$$$$$
    Returns
    -------
    array of arrays:
        Registered streamlines
    """
    tx = ants.read_transform(file_mat)
    ornt_pir2user = get_ornt_PIR_UserDataSpace(user_vol)
    ornt_user2pir = get_ornt_UserDataSpace_PIR(user_vol)
    bbox_allen = select_allen_bbox(res)

    # Loop : Transforming streamlines
    new_streamlines = []
    for sl in tqdm(streamlines):
        new_streamline = []
        for point in sl:
            user_vox = get_uzer_coords(list(point), bbox_allen, tx,
                                       ornt_pir2user, ornt_user2pir)
            new_streamline.append(user_vox)
        new_streamlines.append(new_streamline)

    return new_streamlines

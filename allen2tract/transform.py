import numpy as np
from tqdm import tqdm
import nibabel as nib
import matplotlib
matplotlib.use('TkAgg')
import ants


def select_allen_bbox(res):
    """
    Select Allen voxel bounding box
    corresponding to the resolution.

    Parameters
    ----------
    res: int
        Resolution in Allen [25, 50, 100]

    Returns
    -------
    tuple: Allen Bounding Box
    """
    return (13200//res, 8000//res, 11400//res)


def convert_point_to_vox(point, res):
    """
    Convert a Allen point in um to voxels.

    Parameters
    ----------
    point: list, tuple
        Coordinate in um
    res: int
        Resolution in the Allen [25, 50, 100]
    """
    return [point[0]//res, point[1]//res, point[2]//res]


def convert_point_to_um(point, res):
    """
    Convert a Allen point in voxels to um.

    Parameters
    ----------
    point: list, tuple
        Coordinate in um
    res: int
        Resolution in the Allen [25, 50, 100]
    """
    return [point[0]*res, point[1]*res, point[2]*res]


def get_ornt_PIR_UserDataSpace(user_vol):
    """
    Get the orientation transformation
    from Allen to User DataSpace.
    Using nibabel.orientations.

    Parameters
    ----------
    user_vol: ndarray
        User volume data array

    Return
    ------
    ornt: 3x2 matrix
        nibabel ornt.
    """
    ornt_pir = nib.orientations.axcodes2ornt(('P', 'I', 'R'))

    user_axcodes = nib.aff2axcodes(user_vol.affine)
    ornt_user = nib.orientations.axcodes2ornt(user_axcodes)

    ornt_pir2user = nib.orientations.ornt_transform(ornt_pir, ornt_user)

    return ornt_pir2user


def get_ornt_UserDataSpace_PIR(user_vol):
    """
    Get the orientation transformation
    from UserDataSpace to Allen.
    Using nibabel.orientations.

    Parameters
    ----------
    user_vol: ndarray
        User volume data array

    Return
    ------
    ornt: 3x2 matrix
        nibabel ornt.
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
        get_ornt_PIR_UserDataSpace(user_vol))

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
        get_ornt_UserDataSpace_PIR(user_vol))

    return vol_reorient


def pretransform_point_PIR_UserDataSpace(point,
                                         allen_bbox, user_vol):
    """
    Applying nibabel ornt codes to retrieve allen_coords
    in UserDataSpace orientation (ex: PIR->RAS)

    Process: Create a fake Allen volume, place the point,
    reorient the volume, get the max of the array

    Parameters
    ----------
    point: tuple, list of ints
        Coordinate in the Allen
    allen_bbox: tuple
        Allen bounding box
    user_vol: ndarray
        User volume data array

    Returns
    -------
    list: Coordinates in UserDataSpace orientation
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
    Applying nibabel ornt codes to retrieve Allen coords
    in UserDataSpace orientation in Allen orientation (ex: RAS->PIR)

    Process: Create a fake Allen volume, reorient the volume,
    place the point, revert the orientation of the volume,
    get the max of the array

    Parameters
    ----------
    point: tuple, list of ints
        Coordinate in the Allen oriented in UserDataSpace
    allen_bbox: tuple
        Allen bounding box
    user_vol: ndarray
        User volume data array

    Returns
    -------
    list: Coordinates in PIR orientation
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
    file_mat: str
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
    moving = ants.from_numpy(moving_vol.astype(
        np.float32)).resample_image(fixed_vol.shape, 1, 0)
    fixed = ants.from_numpy(fixed_vol.get_fdata().astype(
        np.float32)).resample_image(fixed_vol.shape, 1, 0)

    mytx = ants.registration(fixed=fixed,
                             moving=moving,
                             type_of_transform='Affine')

    return mytx['fwdtransforms'][0]


def get_user_coords(allen_coords, res, file_mat, user_vol):
    """
    Retrieve the corresponding coordinate in UserDataSpace of
    a specific location in the Allen.

    Parameters
    ----------
    allen_coords: list, tuple
        Allen coordinate in um
    res: int
        Resolution in the Allen [25, 50, 100]
    file_mat: str
        Full path to transformation matrix
    user_vol: ndarray
        User volume data array

    Returns
    -------
    user_coords: list of ints
        Coordinates in UserDataSpace in voxels
    """
    # Selecting Allen bounding box
    allen_bbox = select_allen_bbox(res)

    # Converting injection coordinates position to voxels
    allen_pir_vox = convert_point_to_vox(allen_coords, res)
    allen_pir_vox = list(map(int, allen_pir_vox))

    # Reorienting the point in UserDataSpace
    reoriented_coords = pretransform_point_PIR_UserDataSpace(
        allen_pir_vox, allen_bbox, user_vol)

    # Applying invert ANTsPyX transformation on this point
    tx = ants.read_transform(file_mat)
    user_coords = tx.invert().apply_to_point(reoriented_coords)

    return list(map(int, user_coords))


def get_allen_coords(user_coords, res, file_mat, user_vol):
    """
    Retrieve the corresponding coordinate in the Allen of
    a specific location in the UserDataSpace

    Parameters
    ----------
    user_coords: list, tuple
        User coordinate in voxels
    res: int
        Resolution in the Allen [25, 50, 100]
    file_mat: str
        Full path to transformation matrix
    user_vol: ndarray
        User volume data array

    Returns
    -------
    user_coords: list of ints
        Coordinates in the Allen in um
    """
    # Selecting Allen bounding box
    allen_bbox = select_allen_bbox(res)

    # Reading transform matrix
    tx = ants.read_transform(file_mat)

    # Getting allen vox coords in User Data Space
    allen_vox_user = tx.apply_to_point(user_coords)
    allen_vox_user = list(map(int, allen_vox_user))

    # Reorient the point in Allen Space voxel
    allen_pir_vox = pretransform_point_UserDataSpace_PIR(
        allen_vox_user, allen_bbox, user_vol)

    return convert_point_to_um(allen_pir_vox, res)


def get_user_coords_sl(allen_coords, bbox_allen,
                       tx, ornt_pir2user, ornt_user2pir):
    """
    Overrided version of `get_user_coords`.
    Purposes: Retrieving user_coords with the maximum precision in
    order to right streamlines values.

    Take more parameters to optimise the exectution time.

    Parameters
    ----------
    allen_coords: list, tuple
        Allen coords in um
    bbox_allen: list, tuple
        Allen bounding box
    tx: ANTsPyX matrix
        Transformation matrix
    ornt_pir2user: 3x2 matrix
        nibabel orientation matrix from allen to user
    ornt_user2pir: 3x2 matrix
        nibabel orientation matrix from user to allen

    Returns
    -------
    user_coords: list of floats
        User coords with high precision
    """

    # Using nibabel ornt to reorient the allen_coords in UserDataSpace
    # without creating a fake volume
    # Using first column of ornt to change indices of the point
    # and second column to change the origin (sign and offset)
    user_coords = [0, 0, 0]
    user_coords[int(ornt_pir2user[0][0])] = allen_coords[0] * ornt_user2pir[
        int(ornt_pir2user[0][0])][1]
    user_coords[int(ornt_pir2user[1][0])] = allen_coords[1] * ornt_user2pir[
        int(ornt_pir2user[1][0])][1]
    user_coords[int(ornt_pir2user[2][0])] = allen_coords[2] * ornt_user2pir[
        int(ornt_pir2user[2][0])][1]

    # Adding the offset on the composant that is negative (sign changed)
    for i in range(len(user_coords)):
        if user_coords[i] < 0:
            user_coords[i] += (bbox_allen[
                int(ornt_pir2user[:, 0].tolist().index(i))] - 1)

    # Applying tranformation matrix
    return tx.invert().apply_to_point(user_coords)


def registrate_allen_streamlines(streamlines,
                                 file_mat, user_vol, res):
    """
    Align allen streamlines on the AVGT.

    Parameters
    ----------
    streamlines: array of arrays
        Streamlines array.
    file_mat: str
        Full path to transformation matrix
    user_vol: ndarray
        User volume data array
    res: int
        Resolution in the Allen [25, 50, 100]
        corresponding to the matrix.

    Returns
    -------
    array of arrays:
        Registered streamlines
    """
    # Loading matrix, orientations and bounding box
    tx = ants.read_transform(file_mat)
    ornt_pir2user = get_ornt_PIR_UserDataSpace(user_vol)
    ornt_user2pir = get_ornt_UserDataSpace_PIR(user_vol)
    bbox_allen = select_allen_bbox(res)

    # Loop : Transforming streamlines
    new_streamlines = []
    for sl in tqdm(streamlines):
        new_streamline = []
        for point in sl:
            user_vox = get_user_coords_sl(list(point), bbox_allen, tx,
                                          ornt_pir2user, ornt_user2pir)
            new_streamline.append(user_vox)
        new_streamlines.append(new_streamline)

    return new_streamlines

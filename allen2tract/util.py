import os
from pathlib import Path
import numpy as np
import nibabel as nib
from allen2tract.control import get_cached_dir


def load_user_template(template_file):
    """
    Load User reference template.

    Parameters
    ----------
    template_file: string
        Path to template.
    """
    return nib.load(template_file)


def save_nifti(vol, affine, path):
    """
    Create a Nifti image and
    save it.

    Parameters
    ----------
    vol: ndarray
        Image data.
    affine: 4x4 array
        Image affine.
    path: string
        Path to the output file.
    """
    img = nib.Nifti1Image(vol, affine)
    nib.save(img, path)


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

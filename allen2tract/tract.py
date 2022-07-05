from curses.ascii import SP
import numpy as np
import nibabel as nib
from dipy.io.streamline import load_tractogram, save_tractogram
from dipy.tracking.utils import near_roi
from dipy.io.stateful_tractogram import StatefulTractogram, Space

from allen2tract.util import load_avgt


def get_tract(fname, reference):
    """
    Load a tractogram

    Parameters
    ----------
    fname: string
        Path to trk file.
    reference:
        .nii.gz file reference of the trk.
    """
    return load_tractogram(fname, reference)


def save_tract(fname, streamlines,
               reference, space):
    """
    Save tractrogram file

    Parameters
    ----------
    fname: string
        Path to output file.
    streamlines: array of arrays
        Streamlines to save.
    reference:
        .nii.gz file reference of the trk.
    space:
        StatefulTractogram space.
    """
    sft = StatefulTractogram(
        streamlines=streamlines,
        reference=str(reference),
        space=space
    )
    save_tractogram(
        filename=fname,
        sft=sft
    )


def filter_tract_near_roi(mask, in_tract, out_tract, reference):
    """
    Save a bundle of streamlines passing
    through the binary mask

    Parameters
    ----------
    mask: ndarray
        Binary mask.
    int_tract: string
        Path to the input trk
    out_tract: string
        Path to the output trk
    reference:
        .nii.gz file reference of the trk.
    """
    # Getting avgt wildtype tractogram
    tract = get_tract(in_tract, reference)

    # Loading reference
    ref = nib.load(reference)

    # Filtering streamlines
    # Keeping only the ones that pass through the roi
    through_roi = near_roi(
        streamlines=tract.streamlines,
        affine=ref.affine,
        region_of_interest=mask
    )

    # Writting streamlines array sequence
    streamlines_through_roi = []
    for i in range(len(tract.streamlines)):
        if through_roi[i]:
            streamlines_through_roi.append(
                tract.streamlines[i])

    # Saving the tractogram
    save_tract(
        fname=out_tract,
        streamlines=streamlines_through_roi,
        reference=str(reference),
        space=Space.RASMM
    )

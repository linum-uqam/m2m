import numpy as np
from dipy.io.streamline import load_tractogram, save_tractogram
from dipy.tracking.utils import near_roi

from utils.util import load_avgt


def get_allen_tract():
    """
    """
    fname = "./data/avgt/avgt_wildtype_tractogram.trk"
    return load_tractogram(fname)


def get_streamlines():
    """
    """
    return get_allen_tract()[0]


def get_header():
    """
    """
    return get_allen_tract()[1]


def filter_tract_near_roi(mask, fname):
    """
    """
    streamlines = get_streamlines()

    nearby_roi = near_roi(
        streamlines=streamlines,
        affine=load_avgt().affine,
        region_of_interest=mask
    )

    streamlines_near_roi = []
    for i in range(len(streamlines)):
        if nearby_roi[i]:
            streamlines_near_roi.append(streamlines[i])
    
    save_tractogram(
        fname=fname,
        streamlines=streamlines_near_roi,
        affine=np.eye(4),
        header=get_header()
    )





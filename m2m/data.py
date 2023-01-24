import gdown
from pathlib import Path

from m2m.control import get_cached_dir

GDRIVE_BASE_URL = "https://drive.google.com/uc?id={}"

data_ids = {
    "allen_tractogram_wildtype_50um.trk": "17WP0F1POmxWToKLV0Dl9aD5MsMMyQYlt",
    "allen_template_ras_50um.nii.gz": "1hX_oW8TLH6aPMvdk7-fuikeuJhKIASa2",
}


def download_to_cache(data_id: str, force_download: bool = False) -> str:
    """
    Download data to cache

    Parameters
    ----------
    data_id
        Data to download. The available are the keys of data.data_ids dictionary
    force_download
        Force the download of the file if it is already in the cache

    Returns
    -------
    Full path to the downloaded file
    """
    assert data_id in data_ids.keys(), f"Available data: {data_ids.keys()}"
    url = GDRIVE_BASE_URL.format(data_ids[data_id])
    local_filename = Path(get_cached_dir("data")) / data_id

    if not local_filename.is_file() or force_download:
        local_filename.parent.mkdir(exist_ok=True, parents=True)
        gdown.download(url, str(local_filename))
    else:
        print("Already in cache")

    return str(local_filename)

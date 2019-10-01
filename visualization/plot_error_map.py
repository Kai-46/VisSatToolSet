import numpy as np
from .save_image_only import save_image_only


def plot_error_map(error_map, out_file, maskout=None, force_range=None):
    error_map = error_map.copy()
    if force_range is not None:
        min_val, max_val = force_range
        error_map = np.clip(error_map, min_val, max_val)
        # make sure the color map spans exactly [min_val, max_val]
        error_map[0, 0] = min_val   
        error_map[0, 1] = max_val
    else:
        min_val = np.nanmin(error_map)
        max_val = np.nanmax(error_map)

    # save image and mask
    save_image_only(error_map, out_file, maskout=maskout, cmap='bwr', save_cbar=True, plot=True)

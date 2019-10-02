import numpy as np
import numpy_groupies as npg


# points: each row is (xx, yy, zz)
# xoff: ul_e
# yoff: ul_n
def proj_to_grid(points, xoff, yoff, xresolution, yresolution, xsize, ysize):
    row = np.floor((yoff - points[:, 1]) / xresolution).astype(dtype=np.int)
    col = np.floor((points[:, 0] - xoff) / yresolution).astype(dtype=np.int)
    points_group_idx = row * xsize + col
    points_val = points[:, 2]

    # remove points that lie out of the dsm boundary
    mask = ((row >= 0) * (col >= 0) * (row < ysize) * (col < xsize)) > 0
    points_group_idx = points_group_idx[mask]
    points_val = points_val[mask]

    # create a place holder for all pixels in the dsm
    group_idx = np.arange(xsize * ysize).astype(dtype=np.int)
    group_val = np.empty(xsize * ysize)
    group_val.fill(np.nan)

    # concatenate place holders with the real valuies, then aggregate
    group_idx = np.concatenate((group_idx, points_group_idx))
    group_val = np.concatenate((group_val, points_val))

    dsm = npg.aggregate(group_idx, group_val, func='nanmax', fill_value=np.nan)
    dsm = dsm.reshape((ysize, xsize))

    return dsm

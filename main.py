import os
import json
import numpy as np

from visualization.plot_height_map import plot_height_map
from lib.dsm_util import write_dsm_tif
from lib.proj_to_grid import proj_to_grid
import cv2

from lib.ply_np_converter import ply2np, np2ply
from lib.latlon_utm_converter import latlon_to_eastnorh
from lib.latlonalt_enu_converter import latlonalt_to_enu, enu_to_latlonalt

from evaluate import evaluate

# points is in the cooridnate system (UTM east, UTM north, altitude)
def produce_dsm_from_points(bbx, points, tif_to_write, jpg_to_write=None):
    # write dsm to tif
    ul_e = bbx['ul_easting']
    ul_n = bbx['ul_northing']

    e_resolution = 0.5  # 0.5 meters per pixel
    n_resolution = 0.5 
    e_size = int(bbx['width'] / e_resolution) + 1
    n_size = int(bbx['height'] / n_resolution) + 1
    dsm = proj_to_grid(points, ul_e, ul_n, e_resolution, n_resolution, e_size, n_size)
    # median filter
    dsm = cv2.medianBlur(dsm.astype(np.float32), 3)
    write_dsm_tif(dsm, tif_to_write, 
                  (ul_e, ul_n, e_resolution, n_resolution), 
                  (bbx['zone_number'], bbx['hemisphere']), nodata_val=-9999)

    # create a preview file
    if jpg_to_write is not None:
        dsm = np.clip(dsm, bbx['alt_min'], bbx['alt_max'])
        plot_height_map(dsm, jpg_to_write, save_cbar=True)

    return (ul_e, ul_n, e_size, n_size, e_resolution, n_resolution)


def main(site_data_dir, in_ply, out_dir, eval=False, max_processes=4):
    if not os.path.exists(out_dir):
        os.mkdir(out_dir)

    # load aoi.json from the site_data_dir
    with open(os.path.join(site_data_dir, 'aoi.json')) as fp:
        bbx = json.load(fp)
    
    lat0 = (bbx['lat_min'] + bbx['lat_max']) / 2.0
    lon0 = (bbx['lon_min'] + bbx['lon_max']) / 2.0
    alt0 = bbx['alt_min']

    # load input ply file
    points, color, comments = ply2np(in_ply)

    # convert to UTM coordinate system
    lat, lon, alt = enu_to_latlonalt(points[:, 0:1], points[:, 1:2], points[:, 2:3], lat0, lon0, alt0)
    east, north = latlon_to_eastnorh(lat, lon)
    points = np.hstack((east, north, alt))

    # write to ply file
    ply_to_write = os.path.join(out_dir, 'point_cloud.ply')
    print('Writing to {}...'.format(ply_to_write))
    comment_1 = 'projection: UTM {}{}'.format(bbx['zone_number'], bbx['hemisphere'])
    np2ply(points, ply_to_write, 
          color=color, comments=[comment_1,], use_double=True)


    # produce dsm and write to tif file
    tif_to_write = os.path.join(out_dir, 'dsm.tif')
    jpg_to_write = os.path.join(out_dir, 'dsm.jpg')
    print('Writing to {} and {}...'.format(tif_to_write, jpg_to_write))
    produce_dsm_from_points(bbx, points, tif_to_write, jpg_to_write)

    if eval:
        tif_gt = os.path.join(site_data_dir, 'ground_truth.tif')
        print('Evaluating {} with ground-truth {}...'.format(tif_to_write, tif_gt))
        evaluate(tif_to_write, tif_gt, out_dir, max_processes)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='VisSat Toolset')
    parser.add_argument('--data_dir', type=str,
                    help='data directory for the site')
    parser.add_argument('--ply', type=str,
                    help='recontructed point cloud in ply format')
    parser.add_argument('--out_dir', type=str,
                    help='output directory')
    parser.add_argument('--eval', action='store_true',
                    help='if turned on, the program will also output metric numbers')
    parser.add_argument('--max_processes', type=int, default=4,
                    help='maximum number of processes to be launched')

    args = parser.parse_args()
    main(args.data_dir, args.ply, args.out_dir, args.eval, args.max_processes)

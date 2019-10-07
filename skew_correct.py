import multiprocessing
import cv2
import numpy as np
import json
import os
import imageio
import shutil


# img_src is numpy array, affine matrix is 2*3 matrix
# image index is col, row
# keep all pixels in the source image
# return img_dst, off_set
def warp_affine(img_src, affine_matrix, no_blank_margin=True):
    height, width = img_src.shape[:2]

    # compute bounding box
    bbx = np.dot(affine_matrix, np.array([[0, width, width, 0],
                                          [0, 0, height, height],
                                          [1, 1, 1, 1]]))

    if no_blank_margin:
        col = np.sort(bbx[0, :])
        row = np.sort(bbx[1, :])

        # leave some small margin
        col_min = int(col[1]) + 3
        row_min = int(row[1]) + 3
        w = int(col[2]) - col_min - 3
        h = int(row[2]) - row_min - 3
    else:
        col_min = np.min(bbx[0, :])
        col_max = np.max(bbx[0, :])
        row_min = np.min(bbx[1, :])
        row_max = np.max(bbx[1, :])

        w = int(np.round(col_max - col_min + 1))
        h = int(np.round(row_max - row_min + 1))

    # add offset to the affine_matrix
    affine_matrix[0, 2] -= col_min
    affine_matrix[1, 2] -= row_min

    off_set = (-col_min, -row_min)

    # warp image
    img_dst = cv2.warpAffine(img_src, affine_matrix, (w, h))

    assert (h == img_dst.shape[0] and w == img_dst.shape[1])

    return img_dst, off_set, affine_matrix


def skew_correct_worker(perspective_img_dir, img_name, params, pinhole_img_dir):
    fx = params[2]
    fy = params[3]
    cx = params[4]
    cy = params[5]
    s = params[6]
    qvec = params[7:11]
    tvec = params[11:14]

    # compute homography and update s, cx
    norm_skew = s / fy
    cx = cx - s * cy / fy
    s = 0.

    # warp image
    affine_matrix = np.array([[1., -norm_skew, 0.],
                              [0., 1., 0.]])
    img_src = imageio.imread(os.path.join(perspective_img_dir, img_name))
    img_dst, off_set, affine_matrix = warp_affine(img_src, affine_matrix)
    imageio.imwrite(os.path.join(pinhole_img_dir, img_name), img_dst)

    new_h, new_w = img_dst.shape[:2]
    # add off_set to camera parameters
    cx += off_set[0]
    cy += off_set[1]

    return norm_skew, affine_matrix, [new_w, new_h, fx, fy, cx, cy,
            qvec[0], qvec[1], qvec[2], qvec[3],
            tvec[0], tvec[1], tvec[2]]


def skew_correct(data_dir):
    # input
    perspective_img_dir = os.path.join(data_dir, 'images')
    perspective_file = os.path.join(data_dir, 'perspective_cameras.json')
    with open(perspective_file) as fp:
        perspective_dict = json.load(fp)

    # output
    out_dir = os.path.join(data_dir, 'skew_correct')
    pinhole_img_dir = os.path.join(out_dir, 'images')
    if os.path.exists(pinhole_img_dir):
        shutil.rmtree(pinhole_img_dir)
    os.makedirs(pinhole_img_dir)
    pinhole_file = os.path.join(out_dir, 'pinhole_cameras.json')
    warping_file = os.path.join(out_dir, 'affine_warpings.json')

    pinhole_dict = {}
    affine_warping_dict = {}
    info_txt = 'img_name, skew (s/fy)\n'


    perspective_images = sorted(os.listdir(perspective_img_dir))
    pool_size = min(multiprocessing.cpu_count(), len(perspective_images))
    pool = multiprocessing.Pool(pool_size)

    results = []
    arguments = []
    for img_name in perspective_images:
        # w, h, fx, fy, cx, cy, s, qvec, t
        params = perspective_dict[img_name]
        w = params[0]
        h = params[1]
        arguments.append((img_name, w, h))
        results.append(pool.apply_async(skew_correct_worker, (perspective_img_dir, img_name, params, pinhole_img_dir)))

    for i, r in enumerate(results):
        img_name, w, h = arguments[i]
        norm_skew, affine_matrix, pinhole = r.get()
        affine_warping_dict[img_name] = affine_matrix
        info_txt += '{}, {}\n'.format(img_name, norm_skew)
        pinhole_dict[img_name] = pinhole

        print('removed normalized skew: {} in image: {}, original size: {}, {}, new image size: {}, {}'.format(
               norm_skew, img_name, w, h, pinhole[0], pinhole[1]))

    pool.close()
    pool.join()

    # dump the results to disk
    with open(pinhole_file, 'w') as fp:
        json.dump(pinhole_dict, fp, indent=2)

    with open(warping_file, 'w') as fp:
        for img_name in affine_warping_dict.keys():
            matrix = affine_warping_dict[img_name]
            affine_warping_dict[img_name] = list(matrix.reshape((6,)))
        json.dump(affine_warping_dict, fp, indent=2)

    with open(os.path.join(out_dir, 'skews.csv'), 'w') as fp:
        fp.write(info_txt)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Remove Skew from Images')
    parser.add_argument('--data_dir', type=str,
                    help='data directory for the site')

    args = parser.parse_args()   
    skew_correct(args.data_dir)

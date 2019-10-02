from .plyfile import PlyData, PlyElement
import numpy as np


# only support writing vertex and color attributes
def np2ply(vertex, out_ply, color=None, comments=None, text=False, use_double=False):
    if use_double:
        vertex = vertex.astype(dtype=np.float64)
        dtype_list = [('x', 'f8'), ('y', 'f8'), ('z', 'f8')]
    else:
        vertex = vertex.astype(dtype=np.float32)
        dtype_list = [('x', 'f4'), ('y', 'f4'), ('z', 'f4')] 

    if color is None:
        data = [(vertex[i, 0], vertex[i, 1], vertex[i, 2]) for i in range(vertex.shape[0])]
    else:
        data = [(vertex[i, 0], vertex[i, 1], vertex[i, 2], color[i, 0], color[i, 1], color[i, 2]) for i in range(vertex.shape[0])]
        dtype_list = dtype_list + [('red', 'uint8'), ('green', 'uint8'), ('blue', 'uint8')]

    vertex = np.array(data, dtype=dtype_list)
    el = PlyElement.describe(vertex, 'vertex')
    if text:
        text_fmt = ['%.4f', '%.4f', '%.4f']
        if color is not None:
            text_fmt = text_fmt + ['%i', '%i', '%i']

        if comments is None:
            PlyData([el], text=True, text_fmt=text_fmt).write(out_ply)
        else:
            PlyData([el], text=True, text_fmt=text_fmt, comments=comments).write(out_ply)
    else:
        if comments is None:
            PlyData([el], byte_order='<').write(out_ply)
        else:
            PlyData([el], byte_order='<', comments=comments).write(out_ply)


# not support surface normal
def ply2np(in_ply):
    ply = PlyData.read(in_ply)
    comments = ply.comments
    if len(comments) == 0:
        comments = None
    
    vertex = ply['vertex'].data
    names = vertex.dtype.names

    if 'x' in names:
        xyz = np.hstack((vertex['x'].reshape((-1, 1)),
                         vertex['y'].reshape((-1, 1)),
                         vertex['z'].reshape((-1, 1))))

    if 'red' in names:
        rgb = np.hstack((vertex['red'].reshape((-1, 1)),
                         vertex['green'].reshape((-1, 1)),
                         vertex['blue'].reshape((-1, 1))))
    else:
        rgb = None

    return xyz, rgb, comments

import numpy as np
from osgeo import gdal, gdal_array, osr
import os


def parse_proj_str(proj_str):
    idx1 = proj_str.find('UTM zone')
    idx2 = proj_str.find('",')

    sub_str = proj_str[idx1:idx2]
    hemisphere = sub_str[-1]
    zone_number = int(sub_str[-3:-1])

    return zone_number, hemisphere


def read_dsm_tif(file):
    assert (os.path.exists(file))

    ds = gdal.Open(file)
    geo = ds.GetGeoTransform()
    proj = ds.GetProjection()
    meta = ds.GetMetadata()
    width = ds.RasterXSize
    height = ds.RasterYSize

    assert (ds.RasterCount == 1)     # dsm is only one band
    band = ds.GetRasterBand(1)       # band index is one-based

    data_type = gdal_array.GDALTypeCodeToNumericTypeCode(band.DataType)
    assert (isinstance(data_type(), np.float32))
    image = np.zeros((ds.RasterYSize, ds.RasterXSize), dtype=np.float32)

    image[:, :] = band.ReadAsArray()
    nodata = band.GetNoDataValue()

    # to ease later processing, replace nodata regions with nan
    if nodata is not None:
        mask = np.isclose(image, nodata)
        image[mask] = np.nan

    zone_number, hemisphere = parse_proj_str(proj)
    # return a meta dict
    meta_dict = {
        'geo': geo,
        'proj': proj,
        'meta': meta,
        'img_width': width,
        'img_height': height,
        'nodata': nodata,
        'zone_number': zone_number,
        'hemisphere': hemisphere,
        'ul_easting': geo[0],
        'ul_northing': geo[3],
        'east_resolution': geo[1],
        'north_resolution': abs(geo[5])
    }

    # add other info for convenience
    # lr_easting are left-margin of the last column
    # lr_northing are top-margin of the last row
    meta_dict['lr_easting'] = meta_dict['ul_easting'] + (meta_dict['img_width']-1) * meta_dict['east_resolution']
    meta_dict['lr_northing'] = meta_dict['ul_northing'] - (meta_dict['img_height']-1) * meta_dict['north_resolution']
    meta_dict['area_width'] = meta_dict['lr_easting'] - meta_dict['ul_easting']
    meta_dict['area_height'] = meta_dict['ul_northing'] - meta_dict['lr_northing']
    meta_dict['alt_min'] = float(np.nanmin(image))  # for json serialization
    meta_dict['alt_max'] = float(np.nanmax(image))

    del ds
    return image, meta_dict


def get_driver(file):
    f_ext = os.path.splitext(file)[1]
    for i in range(gdal.GetDriverCount()):
        driver = gdal.GetDriver(i)
        if driver.GetMetadataItem(gdal.DCAP_RASTER):
            d_ext_str = driver.GetMetadataItem(gdal.DMD_EXTENSIONS)
            if d_ext_str is not None:
                for d_ext in d_ext_str.split(' '):
                    if f_ext == '.' + d_ext:
                        return driver
    return None


# out_file: .tif file to write
# geo: (ul_e, ul_n, e_resolution, n_resolution)
# utm_zone: ('N' or 'S')
def write_dsm_tif(image, out_file, geo, utm_zone, nodata_val=None):
    assert (len(image.shape) == 2)      # image should only be 2D

    ul_e, ul_n, e_resolution, n_resolution = geo
    zone_number, hemisphere = utm_zone

    # replace nan with no_data
    if nodata_val is not None:
        image = image.copy()    # avoid modify source data
        image[np.isnan(image)] = nodata_val
    else:
        nodata_val = np.nan

    driver = get_driver(out_file)
    out = driver.Create(out_file, image.shape[1], image.shape[0], 1,
                        gdal_array.NumericTypeCodeToGDALTypeCode(np.float32))
    band = out.GetRasterBand(1)     # one-based index
    band.WriteArray(image.astype(np.float32), 0, 0)
    band.SetNoDataValue(nodata_val)
    band.FlushCache()

    # syntax for geotransform
    # geotransform[0] = top left x
    # geotransform[1] = w-e pixel resolution
    # geotransform[2] = 0
    # geotransform[3] = top left y
    # geotransform[4] = 0
    # geotransform[5] = n-s pixel resolution (negative value)
    out.SetGeoTransform((ul_e, e_resolution, 0, ul_n, 0, -n_resolution))

    srs = osr.SpatialReference();
    srs.SetProjCS('WGS84 / UTM zone {}{}'.format(zone_number, hemisphere));
    srs.SetWellKnownGeogCS('WGS84');
    srs.SetUTM(zone_number, hemisphere=='N');
    out.SetProjection(srs.ExportToWkt())
    out.SetMetadata({'AREA_OR_POINT': 'Area'})

    del out

import utm
import numpy as np
import pyproj


# all the points should lie on the same hemisphere and UTM zone
def latlon_to_eastnorh(lat, lon):
    # assume all the points are either on north or south hemisphere
    assert(np.all(lat >= 0) or np.all(lat < 0))

    if lat[0, 0] >= 0: # north hemisphere
        south = False
    else:
        south = True

    _, _, zone_number, _ = utm.from_latlon(lat[0, 0], lon[0, 0])

    proj = pyproj.Proj(proj='utm', ellps='WGS84', zone=zone_number, south=south)
    east, north = proj(lon, lat)
    return east, north

def eastnorth_to_latlon(east, north, zone_number, hemisphere):
    if hemisphere == 'N':
        south = False
    else:
        south = True

    proj = pyproj.Proj(proj='utm', ellps='WGS84', zone=zone_number, south=south)
    lon, lat = proj(east, north, inverse=True)
    return lat, lon

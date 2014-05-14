"""
Interface Geoset objects with files in DS9 region format.

This module provides functionality for interfacing the Geoset class with
DS9 region files. See the Geoset class for details about the geoset
structure.

.. note:: Geoset instances cannot be fully represented in DS9 format. See
   the write function for details.

Functions
---------
read(filename)
    Create a Geoset instance from a DS9 region file.
write(geoset, filename, coordsys=None, fmt='.15f')
    Write a Geoset instance to a DS9 region file.

"""
from collections import OrderedDict

import numpy as np
from shapely import geometry

from . import _geoset


def read(filename):
    """
    Create a Geoset instance from a DS9 region file.

    .. note:: This will break if the region file was not written using the
       write function in this module!

    Parameters
    ----------
    filename : str
        Path to the DS9 region file to be loaded.

    Returns
    -------
    out : Geoset
        A Geoset instance build using the polygons stored in the DS9 region
        file.

    """
    def parse_ds9_attrs(attrstr, global_attrs=False):
        attrstr = attrstr + ' junk'
        if not global_attrs:
            attrstr = 'junk ' + attrstr

        j = [0] + [i for i in range(len(attrstr)) if attrstr[i] == '='] + [-1]

        keys, vals = [], []
        for j1, j2 in zip(j[:-1], j[1:]):
            val, key = attrstr[j1+1:j2].rsplit(' ', 1)
            if ((val[0], val[-1]) == ('"', '"') or
                (val[0], val[-1]) == ('{', '}')):
                val = val[1:-1]
            keys.append(key)
            vals.append(val)
        return zip(keys[:-1], vals[1:])

    with open(filename, 'r') as file:
        lines = file.readlines()

    geoset = _geoset.Geoset(None)
    i0, j0, k0 = None, None, None
    for line in lines:
        line = line.split('\n')[0]
        # Skip comments and blank lines:
        if line.startswith('#') or not line:
            continue

        # Parse global attributes:
        elif line.startswith('global'):
            attrs = parse_ds9_attrs(line, global_attrs=True)
            attrs = OrderedDict(attrs)
            geoset.attrs = attrs

        # Parse coordinate system:
        elif line in ['physical', 'fk5']:
            if geoset.attrs is None:
                geoset.attrs = OrderedDict()
            geoset.attrs['coordsys'] = line

        # Build geoset:
        elif line.startswith('polygon'):
            coords, delim, attrs = line.partition('(')[-1].partition(')')
            coords, attrs = coords.replace(',', ' '), attrs.split('#')[-1]

            # Make polygon
            xy = [float(i) for i in coords.split()]
            x, y = xy[0::2], xy[1::2]
            poly = geometry.Polygon(zip(x, y))

            # Test if polygon is a hole:
            is_hole = False
            if 'background' in attrs:
                is_hole = True
                attrs = attrs.split('background')[-1]

            # Get item/geo/poly structure indices:
            idx_list = parse_ds9_attrs(attrs)
            for idx in idx_list:
                tag, n = idx[1].split()
                n = int(n)
                if tag == 'item':
                    i = n
                elif tag == 'geo':
                    j = n
                elif tag == 'poly':
                    k = n

            if i != i0:
                geo = _geoset.Geo(poly)
                item = _geoset.Item(geo)
                geoset.items.append(item)
            elif j != j0:
                geo = _geoset.Geo(poly)
                item.geos.append(geo)
            elif k != k0:
                geo.geo = geo.geo.union(poly)
            elif is_hole:
                geo.geo = geo.geo.difference(poly)
            i0, j0, k0 = i, j, k

    return geoset


def write(geoset, filename, coordsys=None, fmt='.15f'):
    """
    Write a Geoset instance to a DS9 region file.

    The structure of the input geoset is preserved using DS9 tags with
    item, geo, and poly numbers (poly number is useful for grouping
    together members of a MultiPolygon within a Geo instance and keeping
    holes associated with a polygon). Polygon holes are identified by the
    background attribute keyword. DS9 format is somewhat limited, so there
    are probably cases where a DS9 region file written using this function
    does not perfectly represent the original Polygon/MultiPolygon objects.
    Attributes within the geoset tree and FITS headers are not written!

    Parameters
    ----------
    geoset : Geoset
        The input Geoset instance.
    filename : str
        Destination path of the output DS9 region file.
    coordsys : {None|'physical'|'fk5'}, optional
        DS9 keyword describing the coordinate system of the listed regions.
        If None, coordsys is set to physical. Default value is None.
    fmt : str, optional
        A string specifying how coordinates should be printed. Default
        value is '.15f'.

    """
    if coordsys is None:
        coordsys = 'physical'
    fmt = '{{0:{0:s}}}'.format(fmt)

    lines = [coordsys + '\n']
    for i, item in enumerate(geoset.items):
        itag = ' tag={{item {0:d}}}'.format(i)

        for j, geo in enumerate(item.geos):
            gtag = ' tag={{geo {0:d}}}'.format(j)
            poly = geo.geo
            if poly.type == 'Polygon':
                poly = [poly]

            for k, subpoly in enumerate(poly):
                ptag = ' tag={{poly {0:d}}}'.format(k)
                xy = np.array(subpoly.exterior.coords)
                xy = ','.join(fmt.format(i) for i in np.ravel(xy))
                line = 'polygon({0:s}) #{1:s}{2:s}{3:s}\n'
                line = line.format(xy, itag, gtag, ptag)
                lines.append(line)

                for hole in subpoly.interiors:
                    xy = np.array(hole.coords)
                    xy = ','.join(fmt.format(i) for i in np.ravel(xy))
                    line = 'polygon({0:s}) # background{1:s}{2:s}{3:s}\n'
                    line = line.format(xy, itag, gtag, ptag)
                    lines.append(line)

    with open(filename, 'w') as f:
        for line in lines:
            f.write(line)

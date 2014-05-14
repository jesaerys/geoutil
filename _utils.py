"""
General-purpose geometry utilities.

Functions
---------
validate_poly(poly, poly_buffer=0)
    Test if a a polygon is valid and attempt to fix it if not.
poly_pix2world(poly_list, hdr_list)
    Convert polygon vertices from pixel coordinates to world coordinates.
poly_world2pix(poly_list, hdr_list)
    Convert polygon vertices from world coordinates to pixel coordinates.
poly_translate(poly_list, dx_list, dy_list)
    Translate polygon coordinates by dx and dy.
clean_poly(poly)
    Remove extraneous geometries from a polygon.
safe_difference(poly1, poly2)
    Wrapper for poly1.difference(poly2) with some extra functionality to
    handle strange cases where it fails.
plot_poly(poly, ax=None, f='k-')
    Convenience function for plotting polygons.
consolidate_polys(poly_list, hole_list=None)
    Turn a list of polygons into a single, multi-polygon object.

"""
from astropy.io import fits
from astropy import wcs
import numpy as np
from shapely import geometry, geos


# Some FITS headers contain the following keys that cause issues when
# creating astropy.wcs.WCS instances!
_PROBLEMATIC_KEYS = ['CPDIS1', 'CPDIS2']


def validate_poly(poly, poly_buffer=0):
    """Test if a a polygon is valid and attempt to fix it if not.

    The buffer method of shapely.geometry objects is used to attempt to fix
    any problems causing a polygon to be invalid, such as pinch points or
    self-crossings.

    Parameters
    ----------
    poly : shapely.geometry.Polygon or shapely.geometry.MultiPolygon
        The polygon to be validated.
    poly_buffer : int or float
        The amount by which poly should be buffered if it is invalid. The
        default value of 0 will join polygons that overlap in a
        MultiPolygon, and split a Polygon into two where it pinches in on
        itself. Note that for an ACS image, setting poly_buffer = 1e-10 deg
        corresponds to changing each vertex by little less than 1e-5 pixels.


    Returns
    -------
    out : shapely.geometry.Polygon or shapely.geometry.MultiPolygon
        A validated polygon; it will not necessarily have the same type as
        the input polygon, i.e. Polygons can turn into MultiPolygons, etc.

    """
    if not poly.is_valid:
        poly = poly.buffer(poly_buffer)
    return poly


def poly_pix2world(poly_list, hdr_list):
    """Convert polygon vertices from pixel coordinates to world coordinates.

    Vertices are converted from pixel coordinates to world coordinates
    according to the WCS information stored in the provided FITS image
    header(s) using astropy.wcs.

    Parameters
    ----------
    poly_list : list
        List of zero or more shapely.geometry.Polygon or
        shapely.geometry.MultiPolygon instances.
    hdr_list : astropy.io.fits.Header or list or None
        Either a single astropy.io.fits.Header instance or a list of zero
        or more. If only one header is given, it is used for all of the
        coordinate conversions. If a list is given, then there must be one
        header for each polygon in poly_list. If None, then no conversion
        is performed.

    Returns
    -------
    out : list
        Same as poly_list, but with all coordinates converted to the world
        system according to the provided header(s).

    """
    def convert(poly, hwcs):
        xy = np.array(poly.exterior.coords)
        lonlat = hwcs.wcs_pix2world(xy, 1)
        new_poly = geometry.Polygon(lonlat.tolist())
        for hole in poly.interiors:
            xy = np.array(hole.coords)
            lonlat = hwcs.wcs_pix2world(xy, 1)
            new_hole = geometry.Polygon(lonlat.tolist())
            new_poly = new_poly.difference(new_hole)
        return new_poly

    # Make sure that hdr_list is iterable:
    if not isinstance(hdr_list, list):
        hdr_list = [hdr_list] * len(poly_list)

    new_poly_list = []
    for poly, hdr in zip(poly_list, hdr_list):

        # Remove keys that can cause issues with astropy.wcs:
        proxy_hdr = fits.Header()
        for key, val in hdr.items():
            if key in _PROBLEMATIC_KEYS:
                continue
            proxy_hdr[key] = val
        hwcs = wcs.WCS(proxy_hdr)

        if poly.type == 'MultiPolygon':
            new_poly = [convert(subpoly, hwcs) for subpoly in poly]
            new_poly = geometry.MultiPolygon(new_poly)
        else:
            new_poly = convert(poly, hwcs)
        new_poly_list.append(new_poly)
    return new_poly_list


def poly_world2pix(poly_list, hdr_list):
    """Convert polygon vertices from world coordinates to pixel coordinates.

    Vertices are converted from world coordinates to pixel coordinates
    according to the WCS information stored in the provided FITS image
    header(s) using astropy.wcs.

    Parameters
    ----------
    poly_list : list
        List of zero or more shapely.geometry.Polygon or
        shapely.geometry.MultiPolygon instances.
    hdr_list : astropy.io.fits.Header or list or None
        Either a single astropy.io.fits.Header instance or a list of zero
        or more. If only one header is given, it is used for all of the
        coordinate conversions. If a list is given, then there must be one
        header for each polygon in poly_list. If None, then no conversion
        is performed.

    Returns
    -------
    out : list
        Same as poly_list, but with all coordinates converted to the pixel
        system according to the provided header(s).

    """
    def convert(poly, hwcs):
        lonlat = np.array(poly.exterior.coords)
        xy = hwcs.wcs_world2pix(lonlat, 1)
        new_poly = geometry.Polygon(xy.tolist())
        for hole in poly.interiors:
            lonlat = np.array(hole.coords)
            xy = hwcs.wcs_world2pix(lonlat, 1)
            new_hole = geometry.Polygon(xy.tolist())
            new_poly = new_poly.difference(new_hole)
        return new_poly

    # Make sure that hdr_list is iterable:
    if not isinstance(hdr_list, list):
        hdr_list = [hdr_list] * len(poly_list)

    new_poly_list = []
    for poly, hdr in zip(poly_list, hdr_list):

        # Remove keys that can cause issues with astropy.wcs:
        proxy_hdr = fits.Header()
        for key, val in hdr.items():
            if key in _PROBLEMATIC_KEYS:
                continue
            proxy_hdr[key] = val
        hwcs = wcs.WCS(proxy_hdr)

        if poly.type == 'MultiPolygon':
            new_poly = [convert(subpoly, hwcs) for subpoly in poly]
            new_poly = geometry.MultiPolygon(new_poly)
        else:
            new_poly = convert(poly, hwcs)
        new_poly_list.append(new_poly)
    return new_poly_list


def poly_translate(poly_list, dx_list, dy_list):
    """Translate polygon coordinates by dx and dy.

    Parameters
    ----------
    poly_list : list
        List of zero or more shapely.geometry.Polygon or
        shapely.geometry.MultiPolygon instances.
    dx_list, dy_list : int or float or list or None
        The shift to be applied in the x or y direction, or a list of zero
        or more shifts. If only one shift is given, it is used for all
        polygons. If a list is given, then there must be one shift for each
        polygon in poly_list. None is treated as equivalent to 0.

    Returns
    -------
    out : list
        Same as poly_list, but with all coordinates translated by dx and dy.

    """
    def convert(poly, dx, dy):
        xy = np.array(poly.exterior.coords)
        xy[:,0], xy[:,1] = xy[:,0] + dx, xy[:,1] + dy
        new_poly = geometry.Polygon(xy.tolist())
        for hole in poly.interiors:
            xy = np.array(hole.coords)
            xy[:,0], xy[:,1] = xy[:,0] + dx, xy[:,1] + dy
            new_hole = geometry.Polygon(xy.tolist())
            new_poly = new_poly.difference(new_hole)
        return new_poly

    # Make sure that dx and dy are iterable:
    if not isinstance(dx_list, list):
        dx_list = [dx_list] * len(poly_list)
    if not isinstance(dy_list, list):
        dy_list = [dy_list] * len(poly_list)

    new_poly_list = []
    for poly, dx, dy in zip(poly_list, dx_list, dy_list):
        if poly.type == 'MultiPolygon':
            new_poly = [convert(subpoly, dx, dy) for subpoly in poly]
            new_poly = geometry.MultiPolygon(new_poly)
        else:
            new_poly = convert(poly, dx, dy)
        new_poly_list.append(new_poly)
    return new_poly_list


# Miscellaneous functions
# -----------------------


def clean_poly(poly):
    """Remove extraneous geometries from a polygon.

    Performing a series of set-theoretic operations on a polygon can result
    in some extraneous objects, e.g., an empty polygon embedded in a
    MultiPolygon. This function looks for such objects and removes them.

    """
    if poly.type == 'Polygon':
        poly = [poly]
    poly_list = []
    for p in poly:
        if (p.type != 'Polygon') or p.is_empty or (p.area == 0):
            continue
        poly_list.append(p)
    if len(poly_list) > 1:
        return geometry.MultiPolygon(poly_list)
    elif len(poly_list) == 1:
        return poly_list[0]
    else:
        return geometry.Polygon()


def safe_difference(poly1, poly2):
    """Wrapper for poly1.difference(poly2) with some extra functionality to
    handle strange cases where it fails.

    """
    try:
        poly = poly1.difference(poly2)
    except geos.TopologicalError:
        # Sometimes the subtraction of multipolygons fails for unknown reasons,
        # but works if each subpolygon is subtracted individually
        if poly2.type == 'Polygon':
            poly2 = [poly2]
        poly = poly1.union(geometry.Polygon())  # Make a copy of poly1
        for p in poly2:
            poly = poly.difference(p)
    return clean_poly(poly)


def plot_poly(poly, ax=None, f='k-'):
    """Convenience function for plotting polygons.

    Requires matplotlib.

    """
    from matplotlib import pyplot as plt

    if poly.type == 'Polygon':
        poly = [poly]
    for p in poly:
        x, y = np.array(p.exterior.coords).T
        if ax:
            ax.plot(x, y, f)
        else:
            plt.plot(x, y, f)
        for hole in p.interiors:
            x, y = np.array(hole.coords).T
            if ax:
                ax.plot(x, y, f)
            else:
                plt.plot(x, y, f)

    return None


def consolidate_polys(poly_list, hole_list=None):
    """Turn a list of polygons into a single, multi-polygon object.

    After forming the main polygon from poly_list, polygons in hole_list
    are subtracted from it to create holes. If a hole does not actually lie
    inside of the main polygon, it is added instead of subtracted.

    Parameters
    ----------
    poly_list : list
        List of zero or more shapely.geometry.Polygon or
        shapely.geometry.MultiPolygon instances to consolidate.
    hole_list : list, optional
        List of zero or more polygons defining holes. Default is None (no
        holes).

    Returns
    -------
    out : shapely.geometry.MultiPolygon, shapely.geometry.Polygon, or None
        A MultiPolygon or Polygon representing the superposition of all
        polygons and holes in poly_list and hole_list, or None if poly_list
        and hole_list are both empty.

    """
    if not poly_list:
        poly = geometry.Polygon()
    elif len(poly_list) == 1:
        poly = poly_list[0]
    else:
        poly = geometry.MultiPolygon(poly_list)

    if hole_list is not None:
        for hole in hole_list:
            if hole.within(poly):
                poly = poly.difference(hole)
            else:
                poly = poly.union(hole)

    if poly.is_empty:
        poly = None
    return poly

"""

=================
`geoutil._geoset`
=================

Container classes for organizing collections of `shapely.geometry` objects.

This module defines a custom data structure called a *geoset* that enables
basic grouping and attribution of objects from `shapely.geometry`. The
geoset structure is implemented using nested classes: `Geo` instances are
stored in `Item` instances, and `Item` instances are stored in a `Geoset`
instance. See the `Geoset` class for a full description of the geoset
model.

Classes
-------

======== ==========================================
`Geo`    Container for a single geometry object.
`Item`   Container for a group of `Geo` instances.
`Geoset` Container for a group of `Item` instances.
======== ==========================================

"""
from collections import OrderedDict

from astropy import wcs
from shapely import geometry

from . import _utils


class Geo(object):

    """Container for a single geometry object.

    Store a geometry class instance from `shapely.geometry` and a set of
    attributes. This class represents the smallest unit in the geoset
    specification (see the `Geoset` class for an overview).

    Parameters
    ----------
    geo : class from `shapely.geometry` or None
        Initializes the `geo` instance variable.
    attrs : optional
        Initializes the `attrs` instance variable. Default value is None.

    Attributes
    ----------
    geo : class from `shapely.geometry` or None
        Any class instance from `shapely.geometry`, e.g., `Polygon`. May also
        be None.
    attrs : dict-like or None
        Attributes as key-value pairs (typically an `OrderedDict`). None if
        no attributes.

    Methods
    -------
    pix2world
        Return a copy with coordinates converted to the WCS world system.
    world2pix
        Return a copy with coordinates converted to the pixel system.
    translate
        Return a copy with coordinates translated by dx and dy.
    copy
        Return a deep copy.

    """

    def __init__(self, geo, attrs=None):
        self.geo = geo
        self.attrs = attrs

    def __str__(self, i=None, n=None, indent='    ', level=0):
        """
        Parameters
        ----------
        i : int
            geo number.
        n : int
            Number of geos encountered before the parent item.
        indent : str
            Set the indent for geo lines.
        level : int
            Set the indent level for geos.

        """
        geostr = 'None' if self.geo is None else self.geo.type

        if self.attrs is None:
            attrstr = ''
        else:
            attrstr = ', {0:d} attr(s)'.format(len(self.attrs))

        if i is not None and n is not None:
            istr = ' {0:d},{1:d}: '.format(i, i+n)
        elif i is not None:
            istr = ' {0:d}: '.format(i)
        else:
            istr = ': '

        return level*indent + 'Geo' + istr + geostr + attrstr

    def pix2world(self, hdr):
        """Return a copy with coordinates converted to the WCS world
        system.

        Any attributes describing the coordinate system of the item must be
        updated manually!

        Parameters
        ----------
        hdr : `astropy.io.fits.Header`
            Transform coordinates according to the WCS information in the
            FITS header.

        Returns
        -------
        out : `Geo`
            Copy of the original with coordinates converted to the WCS
            world system.

        """
        if self.geo is None:
            geo = None
        else:
            geo = _utils.poly_pix2world([self.geo], hdr)[0]
        if self.attrs is None:
            attrs = None
        else:
            attrs = OrderedDict((key, val) for key, val in self.attrs.items())
        return Geo(geo, attrs=attrs)

    def world2pix(self, hdr):
        """Return a copy with coordinates converted to the pixel system.

        Any attributes describing the coordinate system of the item must be
        updated manually!

        Parameters
        ----------
        hdr : `astropy.io.fits.Header`
            Transform coordinates according to the WCS information in the
            FITS header.

        Returns
        -------
        out : `Geo`
            Copy of the original with coordinates converted to the pixel
            system.

        """
        if self.geo is None:
            geo = None
        else:
            geo = _utils.poly_world2pix([self.geo], hdr)[0]
        if self.attrs is None:
            attrs = None
        else:
            attrs = OrderedDict((key, val) for key, val in self.attrs.items())
        return Geo(geo, attrs=attrs)

    def translate(self, dx, dy):
        """Return a copy with coordinates translated by `dx` and `dy`.

        Parameters
        ----------
        dx, dy : int or float
            Coordinate shifts in the x and y directions.

        Returns
        -------
        out : `Geo`
            Copy of the original with coordinates translated by `dx` and
            `dy`.

        """
        if self.geo is None:
            geo = None
        else:
            geo = _utils.poly_translate([self.geo], dx, dy)[0]
        if self.attrs is None:
            attrs = None
        else:
            attrs = OrderedDict((key, val) for key, val in self.attrs.items())
        return Geo(geo, attrs=attrs)

    def copy(self):
        """Return a deep copy.

        Returns
        -------
        out : `Geo`
            Deep copy of the original.

        Notes
        -----
        The geometry object is copied by computing its union with a null
        geometry. As a result, the coordinates of this copy may be
        reordered from the original and string representations would not be
        equal. The `attrs` instance variable is copied as an `OrderedDict`
        (unless it is None).

        """
        if self.geo is None:
            geo = None
        else:
            geo = self.geo.union(geometry.Point())
        if self.attrs is None:
            attrs = None
        else:
            attrs = OrderedDict((key, val) for key, val in self.attrs.items())
        return Geo(geo, attrs=attrs)


class Item(object):

    """Container for a group of `Geo` instances.

    Store any number of `Geo` class instances and a set of attributes. This
    class represents the intermediate unit in the geoset specification (see
    the `Geoset` class for an overview).

    Parameters
    ----------
    geos : list, tuple, `Geo`, or None
        Initialize the `geos` instance variable using either a list or
        tuple of zero or more `Geo` instances, a single `Geo` instance
        (will automatically be turned into a list of length 1), or None.
    attrs : optional
        Initialize the `attrs` instance variable. Default value is None.

    Attributes
    ----------
    geos : list
        List of zero or more `Geo` instances.
    attrs : dict-like or None
        Attributes as key-value pairs (typically an `OrderedDict`). None if
        no attributes.

    Methods
    -------
    pix2world
        Return a copy with coordinates converted to the WCS world system.
    world2pix
        Return a copy with coordinates converted to the pixel system.
    translate
        Return a copy with coordinates translated by dx and dy.
    copy
        Return a deep copy.

    """

    def __init__(self, geos, attrs=None):
        if not geos:
            geos = []
        elif not getattr(geos, '__iter__', False):
            geos = [geos]
        self.geos = geos
        self.attrs = attrs

    def __str__(self, i=None, n=None, indent='    ', level=0):
        """
        Parameters
        ----------
        i : int
            Item number.
        n : int
            Number of geos encountered before this item.
        indent : str
            Set the indent for item lines.
        level : int
            Set the indent level for items.

        """
        if not self.geos:
            geosstr = 'None'
        else:
            geosstr = '{0:d} geo(s)'.format(len(self.geos))

        if self.attrs is None:
            attrstr = ''
        else:
            attrstr = ', {0:d} attr(s)'.format(len(self.attrs))

        istr = ': ' if i is None else ' {0:d}: '.format(i)

        lines = [level*indent + 'Item' + istr + geosstr + attrstr]
        for j, geo in enumerate(self.geos):
            lines.append(geo.__str__(i=j+1, n=n, level=level+1))
        return '\n'.join(lines)

    def pix2world(self, hdr):
        """Return a copy with coordinates converted to the WCS world
        system.

        Any attributes describing the coordinate system of the item must be
        updated manually!

        Parameters
        ----------
        hdr : `astropy.io.fits.Header`
            Transform coordinates according to the WCS information in the
            FITS header.

        Returns
        -------
        out : `Item`
            Copy of the original with coordinates converted to the WCS
            world system.

        """
        geos = [geo.pix2world(hdr) for geo in self.geos]
        if self.attrs is None:
            attrs = None
        else:
            attrs = OrderedDict((key, val) for key, val in self.attrs.items())
        return Item(geos, attrs=attrs)

    def world2pix(self, hdr):
        """Return a copy with coordinates converted to the pixel system.

        Any attributes describing the coordinate system of the item must be
        updated manually!

        Parameters
        ----------
        hdr : `astropy.io.fits.Header`
            Transform coordinates according to the WCS information in the
            FITS header.

        Returns
        -------
        out : `Item`
            Copy of the original with coordinates converted to the pixel
            system.

        """
        geos = [geo.world2pix(hdr) for geo in self.geos]
        if self.attrs is None:
            attrs = None
        else:
            attrs = OrderedDict((key, val) for key, val in self.attrs.items())
        return Item(geos, attrs=attrs)

    def translate(self, dx, dy):
        """Return a copy with coordinates translated by `dx` and `dy`.

        Parameters
        ----------
        dx, dy : int or float
            Coordinate shifts in the x and y directions.

        Returns
        -------
        out : `Item`
            Copy of the original with coordinates translated by `dx` and
            `dy`.

        """
        geos = [geo.translate(dx, dy) for geo in self.geos]
        if self.attrs is None:
            attrs = None
        else:
            attrs = OrderedDict((key, val) for key, val in self.attrs.items())
        return Item(geos, attrs=attrs)

    def copy(self):
        """Return a deep copy.

        Returns
        -------
        out : `Item`
            Deep copy of the original.

        Notes
        -----
        Each geometry object is copied by computing its union with a null
        geometry. As a result, the coordinates of a copy may be reordered
        from the original and string representations would not be equal.
        Each `attrs` instance variable is copied as an `OrderedDicts`
        (unless it is None).

        """
        geos = [geo.copy() for geo in self.geos]
        if self.attrs is None:
            attrs = None
        else:
            attrs = OrderedDict((key, val) for key, val in self.attrs.items())
        return Item(geos, attrs=attrs)


class Geoset(object):

    """Container for a group of `Item` instances.

    This class defines a custom data structure called a geoset that enables
    basic grouping and attribution of objects from `shapely.geometry` (e.g.
    `Polygons`).

    Parameters
    ----------
    items : list, tuple, `Item`, or None
        Initialize the `items` instance variable using either a list or
        tuple of zero or more `Item` instances, a single `Item` instance,
        or None.
    attrs : optional
        Initialize the `attrs` instance variable. Default value is None.
    hdr : optional
        Initialize the `hdr` instance variable. Default value is None.

    Attributes
    ----------
    items : list
        List of zero or more `Item` instances.
    attrs : dict-like or None
        Attributes as key-value pairs (typically an `OrderedDict`). None if
        no attributes.
    hdr : `astropy.io.fits.header.Header` or None
        FITS header that relates to the stored geometries, e.g. WCS
        information for transforming between pixel and sky coordinates.
        None if no header.

    Methods
    -------
    geos
        Return a complete listing of `Geo` instances in the tree.
    pix2world
        Return a copy with coordinates converted to the WCS world system.
    world2pix
        Return a copy with coordinates converted to the pixel system.
    translate
        Return a copy with coordinates translated by dx and dy.
    copy
        Return a deep copy.

    Notes
    -----
    The geoset structure is a simple tree-like hierarchy of nested classes,
    and is implemented as follows:

    =========== ======== ====== ======
    level       1        2      3
    =========== ======== ====== ======
    class       `Geoset` `Item` `Geo`
    container   .items   .geos  .geo
    attributes  .attrs   .attrs .attrs
    FITS header .hdr
    =========== ======== ====== ======

    A single geometry object is contained with its specific attributes in a
    `Geo` instance. Multiple (possibly related) `Geo` instances are grouped
    together in an `Item` instance, along with a set of attributes specific
    to the group. The `Geoset` class contains a set of `Item` instances.
    The geoset as a whole may carry a set attributes, as well as a FITS
    header (an `astropy.io.fits.Header` instance; particularly useful if
    the geometries are all specified in pixel coordinates). All attribute
    sets are dict-like, typically `OrderedDict` instances. See the `Item`
    and `Geo` classes for further details.

    There is some flexibility in how geometry objects are assigned to an
    item. Any number of `Geo` instances are allowed within an `Item`, while
    the `shapely.geometry` subpackage supports various "multi" geometry
    objects and collections, such as `MultiPolygon`. It is therefore
    possible for an item to have several `Geo` instances, each with a
    different geometry type, including collections, `MultiPolygons`, etc.

    A typical use is storing polygons of regions identified in an image.
    The FITS image header and any "global" attributes of the region set
    could be stored in a `Geoset`, along with a list of `Item` instances,
    where an "item" in this case could mean an individual region. Each
    `Item` might contain some attributes describing the specific region
    (name, etc.), and then a list of `Geo` instances, each of which
    contains a polygon object (and even more attributes, if needed). The
    number of `Geo` instances assigned to each item/region depends on the
    complexity of the region; simple regions described by a single polygon
    would only require one `Geo` instance.

    Examples
    --------
    To build a geoset from scratch given a single geometry object (e.g. a
    `shapely.geometry.Polygon` instance, ``poly``),

    >>> geo = Geo(poly)
    >>> item = Item(geo)
    >>> geoset = Geoset(item)
    >>> print geoset
    Geoset: 1 item(s), 1 geo(s)
        Item 1: 1 geo(s)
            Geo 1,1: Polygon

    To add on to an existing geoset (e.g. a second polygon, ``poly2``),

    >>> item = geoset.items[0].geos.append(Geo(poly2))
    >>> print geoset
    Geoset: 1 item(s), 2 geo(s)
        Item 1: 2 geo(s)
            Geo 1,1: Polygon
            Geo 2,2: Polygon

    """

    def __init__(self, items=None, attrs=None, hdr=None):
        if items is None:
            items = []
        elif not getattr(items, '__iter__', False):
            items = [items]
        self.items = items
        self.attrs = attrs
        self.hdr = hdr
        self._geos = None

    def __str__(self):
        if not self.items:
            itemsstr = ': None'
        else:
            itemsstr = ': {0:d} item(s)'.format(len(self.items))
            ngeos = sum([len(item.geos) for item in self.items])
            geosstr = ', {0:d} geo(s)'.format(ngeos)

        if self.attrs is None:
            attrstr = ''
        else:
            attrstr = ', {0:d} attr(s)'.format(len(self.attrs))

        hdrstr = '' if self.hdr is None else ', FITS header'

        lines = ['Geoset' + itemsstr + geosstr + attrstr + hdrstr]
        n = 0
        for j, item in enumerate(self.items):
            lines.append(item.__str__(i=j+1, n=n, level=1))
            n += len(item.geos)
        return '\n'.join(lines)

    def pix2world(self, hdr=None):
        """Return a copy with coordinates converted to the WCS world
        system.

        Any attributes describing the coordinate system of the geoset must
        be updated manually!

        Parameters
        ----------
        hdr : `astropy.io.fits.Header` or None, optional
            Transform coordinates according to the WCS information in the
            FITS header. If None, the header stored in the geoset is used.
            Default value is None.

        Returns
        -------
        out : `Geoset`
            Copy of the original with coordinates converted to the WCS
            world system.

        """
        if hdr is None:
            hdr = self.hdr
        items = [item.pix2world(hdr) for item in self.items]
        if self.attrs is None:
            attrs = None
        else:
            attrs = OrderedDict((key, val) for key, val in self.attrs.items())
        if self.hdr is None:
            hdr = None
        else:
            hdr = self.hdr.copy()
        return Geoset(items, attrs=attrs, hdr=hdr)

    def world2pix(self, hdr=None):
        """Return a copy with coordinates converted to the pixel system.

        Any attributes describing the coordinate system of the geoset must
        be updated manually!

        Parameters
        ----------
        hdr : `astropy.io.fits.Header` or None, optional
            Transform coordinates according to the WCS information in the
            FITS header. If None, the header stored in the geoset is used.
            Default value is None.

        Returns
        -------
        out : `Geoset`
            Copy of the original with coordinates converted to the pixel
            system.

        """
        if hdr is None:
            hdr = self.hdr
        items = [item.world2pix(hdr) for item in self.items]
        if self.attrs is None:
            attrs = None
        else:
            attrs = OrderedDict((key, val) for key, val in self.attrs.items())
        if self.hdr is None:
            hdr = None
        else:
            hdr = self.hdr.copy()
        return Geoset(items, attrs=attrs, hdr=hdr)

    def translate(self, dx, dy):
        """Return a copy with coordinates translated by dx and dy.

        Parameters
        ----------
        dx, dy : int or float
            Coordinate shifts in the x and y directions.

        Returns
        -------
        out : `Geoset`
            Copy of the original with coordinates translated by `dx` and
            `dy`.

        """
        items = [item.translate(dx, dy) for item in self.items]
        if self.attrs is None:
            attrs = None
        else:
            attrs = OrderedDict((key, val) for key, val in self.attrs.items())
        if self.hdr is None:
            hdr = None
        else:
            hdr = self.hdr.copy()
        return Geoset(items, attrs=attrs, hdr=hdr)

    def copy(self):
        """Return a deep copy.

        Returns
        -------
        out : `Geoset`
            Deep copy of the original.

        Notes
        -----
        Each geometry object in the tree is copied by computing its union
        with a null geometry. As a result, the coordinates of a copy may be
        reordered from the original and string representations would not be
        equal. Each `attrs` instance variable in the tree is copied as an
        `OrderedDict` (unless it is None).

        """
        items = [item.copy() for item in self.items]
        if self.attrs is None:
            attrs = None
        else:
            attrs = OrderedDict((key, val) for key, val in self.attrs.items())
        if self.hdr is None:
            hdr = None
        else:
            hdr = self.hdr.copy()
        return Geoset(items, attrs=attrs, hdr=hdr)

    @property
    def geos(self):
        """Return a complete listing of `Geo` instances in the tree.

        This is a read-only attribute; setting and deleting members in this
        list are not supported.

        Returns
        -------
        out : list
            A list of all `Geo` instances stored in the tree.

        """
        self._geos = []
        for item in self.items:
            for geo in item.geos:
                self._geos.append(geo)
        return self._geos

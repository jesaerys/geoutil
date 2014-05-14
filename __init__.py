"""
=======
geoutil
=======
Utilities for working with objects from the geometry subpackage of shapely.

This package defines a custom data structure called a geoset that enables
basic grouping and attribution of objects from the geometry subpackage of
shapely. The geoset structure is implemented using nested classes: Geo
instances are stored in Item instances, and Item instances are stored in a
Geoset instance. See the Geoset class for a full description of the geoset
model.

This package also contains the geosetxml module for interfacing with the
Geoset class. It defines the geoset XML format, an XML representation of
the geoset data structure (see geosetxml.toxml).

There are also some functions for processing shapely.geometry.Polygon
instances.


Modules
-------
geosetxml
    Interface Geoset objects with files in geoset XML format.
ds9regfile
    Interface Geoset objects with files in DS9 region format.
polylistxml
    Interface Geoset objects with files in polylist XML format. (POLYLIST
    XML is the precursor of the GEOSET XML format and is deprecated. It is
    retained for backwards compatibility with older projects.)


Classes
-------
Geo
    Container for a single geometry object.
Item
    Container for a group of Geo instances.
Geoset
    Container for a group of Item instances.


Functions
---------
validate_poly(poly, poly_buffer=0)
    Test if a polygon is valid and attempt to fix it if not.
poly_pix2world(poly_list, hdr_list)
    Convert polygon vertices from pixel coordinates to world coordinates.
poly_world2pix(poly_list, hdr_list)
    Convert polygon vertices from world coordinates to pixel coordinates.
poly_translate(poly_list, dx_list, dy_list)
    Translate polygon coordinates by dx and dy.


Dependencies
------------
- `astropy <www.astropy.org>`_
- `numpy <www.numpy.org>`_
- `shapely <https://github.com/Toblerity/Shapely>`_


Notes
-----
I/O interfacing with Geoset instances may be expanded to additional file
formats using modules similar to geosetxml. A new interface module should
be imported by the geoutil package using an ``import newinterface``
statement. This helps keep similar functions for different interfaces
nicely organized in separate namespaces, i.e. geosetxml.write and
newinterface.write.

"""
from ._geoset import Geo, Geoset, Item
from ._utils import (poly_pix2world, poly_world2pix, poly_translate,
                     validate_poly)
from . import geosetxml
from . import ds9regfile
from . import polylistxml

"""

=========
`geoutil`
=========

Utilities for working with objects from the geometry subpackage of `shapely
<https://github.com/Toblerity/Shapely>`_.

This package defines a custom data structure called a *geoset* that enables
basic grouping and attribution of objects from `shapely.geometry`. The
geoset structure is implemented using nested classes: |Geo| instances are
stored in |Item| instances, and |Item| instances are stored in a |Geoset|
instance. See the |Geoset| class for a full description of the geoset
model.

This package also contains the `geosetxml` module for interfacing with the
|Geoset| class. It defines the *geoset XML format*, an XML representation
of the geoset data structure (see `geosetxml.toxml`).

There are also some functions for processing `shapely.geometry.Polygon`
instances.

`geoutil` depends on the following packages:

- `astropy <http://www.astropy.org>`_
- `numpy <http://www.numpy.org>`_
- `shapely <https://github.com/Toblerity/Shapely>`_


Modules
-------

I/O interfacing with |Geoset| instances is handled by modules imported in
`geoutil`, where each module reads and writes in a specific file format.
New interface modules can be written (modeled after `geoutil.geosetxml`) to
support additional file formats. Having a dedicated interface module for
each file format keep similar functions for different interfaces nicely
organized in separate namespaces, e.g., `geosetxml.write` is distinct from
`newinterfacemodule.write`.

============= =============================================================
`geosetxml`   Interface |Geoset| instances with files in geoset XML format.
`ds9regfile`  Interface |Geoset| instances with files in DS9 region format.
`polylistxml` Interface |Geoset| instances with files in polylist XML format.
              (polylist XML is the precursor of the geoset XML format and
              is deprecated. It is retained for backwards compatibility
              with older projects.)
============= =============================================================


Classes
-------

======== ==========================================
|Geo|    Container for a single geometry object.
|Item|   Container for a group of |Geo| instances.
|Geoset| Container for a group of |Item| instances.
======== ==========================================


Functions
---------

================ ========================================================
|validate_poly|  Test if a polygon is valid and attempt to fix it if not.
|poly_pix2world| Convert polygon vertices from pixel coordinates to world
                 coordinates.
|poly_world2pix| Convert polygon vertices from world coordinates to pixel
                 coordinates.
|poly_translate| Translate polygon coordinates by dx and dy.
================ ========================================================



============
Module Index
============

- `geoutil._geoset`
- `geoutil.geosetxml`
- `geoutil.ds9regfile`
- `geoutil.polylistxml`
- `geoutil._utils`


.. references

.. |Geo| replace:: `~geoutil._geoset.Geo`
.. |Item| replace:: `~geoutil._geoset.Item`
.. |Geoset| replace:: `~geoutil._geoset.Geoset`

.. |validate_poly| replace:: `~geoutil._utils.validate_poly`
.. |poly_pix2world| replace:: `~geoutil._utils.poly_pix2world`
.. |poly_world2pix| replace:: `~geoutil._utils.poly_world2pix`
.. |poly_translate| replace:: `~geoutil._utils.poly_translate`

"""
from ._geoset import Geo, Geoset, Item
from ._utils import (poly_pix2world, poly_world2pix, poly_translate,
                     validate_poly)
from . import geosetxml
from . import ds9regfile
from . import polylistxml

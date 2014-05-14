geoutil
=======

Utilities for working with objects from the geometry subpackage of `shapely
<https://github.com/Toblerity/Shapely>`_.

This package defines a custom data structure called a geoset that enables
basic grouping and attribution of objects from the geometry subpackage of
shapely. The geoset structure is implemented using nested classes: ``Geo``
instances are stored in ``Item`` instances, and ``Item`` instances are
stored in a ``Geoset`` instance. See the ``Geoset`` class for a full
description of the geoset model.

This package also contains the geosetxml module for interfacing with the
``Geoset`` class. It defines the geoset XML format, an XML representation
of the geoset data structure (see ``geosetxml.toxml``).

There are also some functions for processing ``shapely.geometry.Polygon``
instances.

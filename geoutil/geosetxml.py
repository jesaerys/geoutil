"""

===================
`geoutil.geosetxml`
===================

Interface |Geoset| instances with files in geoset XML format.

This module defines the geoset XML format, an XML representation of the
geoset data structure, and provides functionality for interfacing with the
|Geoset| class. See the |Geoset| class for details about
the geoset structure, and the `toxml` function for the geoset XML format
definition.

Functions
---------

=========== ===============================================================
`fromxml`   Return a |Geoset| instance from a geoset XML tree.
`toxml`     Return a geoset XML tree from a |Geoset| instance.
`read`      Return a |Geoset| instance from a geoset XML file.
`write`     Write a |Geoset| instance to a geoset XML file.
`formatter` A custom XML "pretty print" formatter for geoset XML files.
=========== ===============================================================


.. references

.. |Geoset| replace:: `~geoutil._geoset.Geoset`

"""
from collections import OrderedDict
import json

from astropy.io import fits
try:
    from lxml import etree
except ImportError:
    from xml.etree import ElementTree as etree
from shapely import wkt

from . import _geoset


def fromxml(geoset_xml):
    """Convert a geoset XML tree to a |Geoset| instance.

    See `toxml` for details about the geoset XML format.

    Parameters
    ----------
    geoset_xml : `Element` from `xml.etree.ElementTree` or `lxml.etree`
        The root element of an XML tree in geoset XML format.

    Returns
    -------
    out : |Geoset|
        A |Geoset| instance built using the items, geometries, attributes,
        and FITS header information stored in `geoset_xml`.

    Notes
    -----
    Text contained in subelements of the XML tree is processed using the
    following functions:

    ============ ============= ===================
    XML element  text format   parsing function
    ============ ============= ===================
    ``<WKT>``    WKT           `wkt.loads`
    ``<ATTR>``   JSON array    `json.loads`
    ``<HEADER>`` single string `Header.fromstring`
    ============ ============= ===================

    Note that strings returned by `json` are always unicode strings.

    """
    attrs = geoset_xml[0].text
    if attrs is not None:
        attrs = OrderedDict(json.loads(attrs))
    hdr = geoset_xml[1].text
    if hdr is not None:
        hdr = fits.Header.fromstring(hdr)
    geoset = _geoset.Geoset(None, attrs=attrs, hdr=hdr)

    if len(geoset_xml) > 2:
        for item_xml in geoset_xml[2:]:
            attrs = item_xml[0].text
            if attrs is not None:
                attrs = OrderedDict(json.loads(attrs))
            item = _geoset.Item(None, attrs=attrs)

            if len(item_xml) > 1:
                for geo_xml in item_xml[1:]:
                    attrs = geo_xml[0].text
                    if attrs is not None:
                        attrs = OrderedDict(json.loads(attrs))
                    geo = geo_xml[1].text
                    if geo is not None:
                        geo = wkt.loads(geo)

                    item.geos.append(_geoset.Geo(geo, attrs=attrs))

            geoset.items.append(item)

    return geoset


def read(filename):
    """Create a |Geoset| instance from a geoset XML file.

    Uses `fromxml` to parse the XML tree after the file is loaded. See
    `fromxml` for details.

    Parameters
    ----------
    filename : str
        Path to the geoset XML file to be loaded.

    Returns
    -------
    out : |Geoset|
        A |Geoset| instance build using the items, geometries, attributes,
        and FITS header information stored in the geoset XML file.

    """
    geoset_xml = etree.parse(filename).getroot()
    return fromxml(geoset_xml)


def toxml(geoset):
    """Convert a |Geoset| instance to a geoset XML tree.

    The geoset structure (see the |Geoset| class) can be represented in
    geoset XML format, defined as follows::

      <GEOSET>
        <ATTR>...</ATTR>
        <HEADER>...</HEADER>
        <ITEM>
          <ATTR>...</ATTR>
          <GEO><ATTR>...</ATTR><WKT>...</WKT></GEO>
          ...
        </ITEM>
        ...
      </GEOSET>

    ========== ============================================================
    ``GEOSET`` Subelements: ``ATTR``, ``HEADER``, zero or more ``ITEM``
               elements.
    ``ITEM``   Subelements: ``ATTR``, zero or more ``GEO`` elements.
    ``GEO``    Subelements: ``ATTR``, ``WKT``.
    ``ATTR``   Text (optional): attributes specified as an array of
               key-value pairs in JSON format, ``[[key1, val1], ...]``.
    ``HEADER`` Text (optional): FITS header represented as a single string,
               i.e., 80-character sections (one section per header keyword)
               joined without line breaks.
    ``WKT``    Text (optional): WKT (well-known text) representation of a
               `shapely.geometry` geometry class instance.
    ========== ============================================================

    Parameters
    ----------
    geoset : |Geoset|
        A |Geoset| instance from which to build an XML tree.

    Returns
    -------
    out : `Element` from `xml.etree.ElementTree` or `lxml.etree``
        A geoset XML tree build using the items, geometries, attributes,
        and FITS header stored in the provided |Geoset| instance.

    Notes
    -----
    Objects stored in a |Geoset| are serialized into text using the
    following functions:

    ======================== ================= ==============
    object                   serializer        text format
    ======================== ================= ==============
    `shapely.geometry` obj   `wkt.dumps`       WKT
    attribute list [1]_      `json.dumps`      JSON array
    `astropy.io.fits.Header` `Header.tostring` single string
    ======================== ================= ==============

    .. [1] a list of key-value pairs, such as that returned by
       ``dict.items()``.

    """
    geoset_xml = etree.Element('GEOSET')

    attr_xml = etree.SubElement(geoset_xml, 'ATTR')
    if geoset.attrs is not None:
        attr_xml.text = json.dumps(geoset.attrs.items())

    header_xml = etree.SubElement(geoset_xml, 'HEADER')
    if geoset.hdr is not None:
        header_xml.text = geoset.hdr.tostring()

    for item in geoset.items:
        item_xml = etree.SubElement(geoset_xml, 'ITEM')

        attr_xml = etree.SubElement(item_xml, 'ATTR')
        if item.attrs is not None:
            attr_xml.text = json.dumps(item.attrs.items())

        for geo in item.geos:
            geo_xml = etree.SubElement(item_xml, 'GEO')

            attr_xml = etree.SubElement(geo_xml, 'ATTR')
            if geo.attrs is not None:
                attr_xml.text = json.dumps(geo.attrs.items())

            wkt_xml = etree.SubElement(geo_xml, 'WKT')
            if geo.geo is not None:
                wkt_xml.text = wkt.dumps(geo.geo)
    return geoset_xml


def formatter(geoset_xml):
    """A custom XML "pretty print" formatter for geoset XML files.

    Formatting is done by adding appropriate spaces and newlines to the
    text and tails of subelements in the XML tree. There is no return
    value; the input XML tree is modified in place.

    Parameters
    ----------
    geoset_xml : `Element` from `xml.etree.ElementTree` or `lxml.etree`
        The geoset XML tree to be formatted.

    """
    indent = '  '
    geoset_xml.text = '\n' + indent
    geoset_xml[0].tail = '\n' + indent
    geoset_xml[1].tail = '\n' + indent

    if len(geoset_xml) > 2:
        for item_xml in geoset_xml[2:]:
            item_xml.text = '\n' + 2*indent
            item_xml[0].tail = '\n' + 2*indent

            if len(item_xml) > 1:
                for geo_xml in item_xml[1:]:
                    geo_xml.tail = '\n' + 2*indent

            item_xml[-1].tail = '\n' + indent
            item_xml.tail = '\n' + indent

    geoset_xml[-1].tail = '\n'
    geoset_xml.tail = '\n'


def write(geoset, filename):
    """Write a |Geoset| instance to a geoset XML file.

    Uses `toxml` to form an XML tree which is then written to file. See
    `toxml` for details.

    Parameters
    ----------
    geoset : |Geoset|
        The input |Geoset| instance.
    filename : str
        Destination path of the output geoset XML file.

    """
    geoset_xml = toxml(geoset)
    formatter(geoset_xml)
    tree = etree.ElementTree(geoset_xml)
    tree.write(filename, encoding='UTF-8', xml_declaration=True)

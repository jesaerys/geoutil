"""
Interface Geoset objects with files in polylist XML format.

This module defines the polylist XML format, an XML representation of the
geoset data structure, and provides functionality for interfacing with the
Geoset class. See the Geoset class for details about the geoset structure,
and the toxml function for the polylist XML format definition.

.. note:: POLYLIST XML is the precursor of the GEOSET XML format and is
   deprecated. It is retained for backwards compatibility with older
   projects.

Functions
---------
fromxml(polylist_xml)
    Return a Geoset instance from a polylist XML tree.
toxml(geoset)
    Return a polylist XML tree from a Geoset instance.
read(filename)
    Return a Geoset instance from a polylist XML file.
write(geoset, filename)
    Write a Geoset instance to a polylist XML file.
formatter(geoset_xml)
    A custom XML "pretty print" formatter for polylist XML files.

"""
from collections import OrderedDict

from astropy.io import fits
try:
    from lxml import etree
except ImportError:
    from xml.etree import ElementTree as etree
from shapely import wkt

from . import _geoset


def add_XML_attrs(attr_list, element, eformat='%.16e', fformat='%.16f'):
    """
    Add attributes to an XML element from a list of key-value pairs.

    "Attributes" in this context means XML attributes, i.e. metadata stored
    with the tag inside an XML element. Attributes are stored as text, so
    each value is converted to a string based on the data type. No return
    value; attributes are added directly to the given element.

    Parameters
    ----------
    attr_dict : OrderedDict
        OrderedDict of attributes.
    element : Element from xml.etree.ElementTree or lxml.etree
        XML element to which attributes are added.
    eformat, fformat : str
        Format strings controlling how scientific and decimal floats are
        printed.

    Notes
    -----
    xml and lxml do not return attributes in any guaranteed order, so the
    ordering of the input attributes list may not be preserved.

    """
    for attr, val in attr_list.items():
        if attr == '':
            continue
        elif type(val) is type(1):
            val = '%d' % val
        elif (type(val) is type(1.0)) and ('e' in str(val)):
            val = eformat % val
        elif type(val) is type(1.0):
            val = fformat % val
        else:
            val = '%s' % val
        element.attrib[attr] = val


def get_XML_attrs(element):
    """
    Return an attribute dictionary from an XML element.

    "Attributes" in this context means XML attributes, i.e. metadata stored
    with the tag inside an XML element. Attributes are stored as text, so
    each value is converted from a string based on a best guess as to the
    indented data type.

    Parameters
    ----------
    element : Element from xml.etree.ElementTree or lxml.etree
        XML element containing attributes.

    Returns
    -------
    out : OrderedDict
        An OrderedDict of the attributes stored in element.

    Notes
    -----
    xml and lxml do not return attributes in any guaranteed order!

    """
    attr_list = []
    for attr, val in element.attrib.items():
        try:
            val = int(val)
        except ValueError:
            try:
                val = float(val)
            except ValueError:
                if val == 'True':
                    val = True
                elif val == 'False':
                    val = False
        attr_list.append((attr, val))
    attr_list = None if not attr_list else OrderedDict(attr_list)
    return attr_list


def fromxml(polylist_xml):
    """
    Convert a polylist XML tree to a Geoset instance.

    See toxml for details about the polylist XML format.

    Parameters
    ----------
    polylist_xml : Element from xml.etree.ElementTree or lxml.etree
        The root element of an XML tree in polylist XML format.

    Returns
    -------
    out : Geoset
        A Geoset instance build using the items, geometries,
        attributes, and FITS header information stored in polylist_xml.

    Notes
    -----
    Text contained in POLY subelements of the XML tree is processed using the
    wkt.loads function to form shapely.geometry objects.

    """
    attrs = get_XML_attrs(polylist_xml)
    hdr = get_XML_attrs(polylist_xml[0])
    if hdr is not None:
        hdr = fits.Header(hdr.items())
    geoset = _geoset.Geoset(None, attrs=attrs, hdr=hdr)

    if len(polylist_xml) > 1:
        for item_xml in polylist_xml[1:]:
            attrs = get_XML_attrs(item_xml)
            item = _geoset.Item(None, attrs=attrs)

            if len(item_xml) > 0:
                for poly_xml in item_xml:
                    attrs = get_XML_attrs(poly_xml)
                    poly = poly_xml.text
                    if poly is not None:
                        poly = wkt.loads(poly)

                    item.geos.append(_geoset.Geo(poly, attrs=attrs))

            geoset.items.append(item)

    return geoset


def read(filename):
    """
    Create a Geoset instance from a polylist XML file.

    Uses the fromxml function to parse the XML tree after the file is
    loaded. See fromxml for details.

    Parameters
    ----------
    filename : str
        Path to the polylist XML file to be loaded.

    Returns
    -------
    out : Geoset
        A Geoset instance build using the items, geometries,
        attributes, and FITS header information stored in the polylist XML
        file.

    """
    polylist_xml = etree.parse(filename).getroot()
    return fromxml(polylist_xml)


def toxml(geoset):
    """
    Convert a Geoset instance to a polylist XML tree.

    The geoset structure (see the Geoset class) can be represented in XML
    as follows; this defines the polylist XML format::

      <POLYLIST ...>
        <HEADER .../>
        <ITEM ...>
          <POLY ...>...</POLY>
          ...
        </ITEM>
        ...
      </POLYLIST>

    POLYLIST
        Subelements: HEADER and zero or more ITEM elements.
        XML attributes (optional)
    ITEM
        Subelements: zero or more POLY elements.
        XML attributes (optional)
    POLY
        Text (optional): WKT (well-known text) representation of a
        shapely.geometry geometry class instance.
        XML attributes (optional)
    HEADER
        XML attributes (optional)

    Parameters
    ----------
    geoset : Geoset
        A Geoset instance from which to build an XML tree.

    Returns
    -------
    out : Element from xml.etree.ElementTree or lxml.etree
        A polylist XML tree build using the items, geometries, attributes,
        and FITS header stored in the provided Geoset instance.

    Notes
    -----
    shapely.geometry objects are serialized to WKT strings using the
    wkt.dumps function.

    """
    geoset_xml = etree.Element('POLYLIST')
    if geoset.attrs is not None:
        add_XML_attrs(geoset.attrs, geoset_xml)

    header_xml = etree.SubElement(geoset_xml, 'HEADER')
    if geoset.hdr is not None:
        add_XML_attrs(geoset.hdr, header_xml)

    for item in geoset.items:
        item_xml = etree.SubElement(geoset_xml, 'ITEM')

        if item.attrs is not None:
            add_XML_attrs(item.attrs, item_xml)

        for geo in item.geos:
            geo_xml = etree.SubElement(item_xml, 'POLY')

            if geo.attrs is not None:
                add_XML_attrs(geo.attrs, geo_xml)

            if geo.geo is not None:
                geo_xml.text = wkt.dumps(geo.geo)
    return geoset_xml


def pretty_format(elem, level=0, indent='  '):
    """
    "Pretty print" formatter for XML files.

    Recursively edits newlines and spaces in text and tails of subelements
    in the XML tree. There is no return value; the provided XML tree is
    operated on "in place".

    Parameters
    ----------
    elem : ElementTree or Element from xml.etree.ElementTree or lxml.etree
        All subelements of this XML element are formatted.

    """
    if hasattr(elem, 'getroot'):
        elem = elem.getroot()
    i = '\n' + level * '  '
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + '  '
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            pretty_format(elem, level=level+1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i


def write(geoset, filename):
    """
    Write a Geoset instance to a polylist XML file.

    Uses the toxml function to form an XML tree which is then written to
    file. See toxml for details.

    Parameters
    ----------
    geoset : Geoset
        The input Geoset instance.
    filename : str
        Destination path of the output polylist XML file.

    """
    polylist_xml = toxml(geoset)
    pretty_format(polylist_xml)
    tree = etree.ElementTree(polylist_xml)
    tree.write(filename, encoding='UTF-8', xml_declaration=True)

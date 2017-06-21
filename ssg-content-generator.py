#!/usr/bin/python

import datetime
import os
import os.path
import errno
import platform
import re
import sys
import yaml
import string
import argparse
from xml.dom import minidom
from copy import deepcopy


try:
    from xml.etree import cElementTree as ET
except ImportError:
    import cElementTree as ET

try:
    set
except NameError:
    # for python2
    from sets import Set as set

try:
    from configparser import SafeConfigParser
except ImportError:
    # for python2
    from ConfigParser import SafeConfigParser


xccdf_ns = {'xsi': "http://www.w3.org/2001/XMLSchema-instance",
             'xhtml': "http://www.w3.org/1999/xhtml",
             'dc': "http://purl.org/dc/elements/1.1/",
             'id': "product-name",
             'schemaLocation': "http://checklists.nist.gov/xccdf/1.1 xccdf-1.1.4.xsd",
             'style': "SCAP_1.1",
             'resolved': "false",
             'lang': "en-US",
             }


def common_xccdf_content(content, xml_tree):
    description = yaml_key_value(content, 'description')
    name = yaml_key_value(content, 'title')

    if name:
        title = ET.SubElement(xml_tree, 'title')
        title.text = name
    if description:
        desc = ET.SubElement(xml_tree, 'description')
        desc.text = description
        #for test in desc.iter():
        #    print test.text

    return xml_tree


def yaml_key_value(content, key):
    try:
        return content[key]
    except:
        pass


def yaml_to_xml_mapping(content, xmltree):
    group = yaml_key_value(content, 'group_id')
    rule = yaml_key_value(content, 'rule_id')
    ocil = yaml_key_value(content, 'ocil')
    rationale = yaml_key_value(content, 'rationale')
    oval_id = yaml_key_value(content, 'oval')
    identifiers = yaml_key_value(content, 'identifiers')
    references = yaml_key_value(content, 'references')
    warning = yaml_key_value(content, 'warning')
    primary_group = yaml_key_value(content, 'primary_group')
    variable = yaml_key_value(content, 'var_id')
    option = yaml_key_value(content, 'options')
    option_val = yaml_key_value(content, 'option_val')
    
    if group:
        grouping = ET.Element('Group', id=group)
        grouping = common_xccdf_content(content, grouping)
    if variable:
        grouping = ET.Element('Value', id=variable)
        grouping = common_xccdf_content(content, grouping)
        grouping.set('type', content['type'])
        grouping.set('operator', content['operator'])
        grouping.set('interactive', str(content['interactive']))
        if option:
            for options in option:
                for key, val  in content['options'][options].iteritems():
                     opt = ET.SubElement(grouping, 'value', selector=key)
                     opt.text = val

    if rule:
        grouping = ET.Element('Rule', id=rule)
        grouping = common_xccdf_content(content, grouping)
    if ocil:
        ocil_elem = ET.SubElement(grouping, 'ocil')
        ocil_elem.set('clause', ocil['clause'])
        ocil_elem.text = ocil['description']
    if rationale:
        rationale_elem = ET.SubElement(grouping, 'rationale')
        rationale_elem.text = rationale
    if oval_id:
        oval = ET.SubElement(grouping, 'oval')
        oval.set('id', oval_id)
        if variable:
            oval.set('value', variable['id'])
    if identifiers:
        idents = ET.SubElement(grouping, 'ident')
        for ide in identifiers:
            if identifiers[ide] is not None:
                idents.set(ide, identifiers[ide])
    if references:
        refs = ET.SubElement(grouping, 'ref')
        for ref in references:
            if references[ref] is not None:
                refs.set(ref, references[ref])
    if warning:
        warn = ET.SubElement(grouping, 'warning', category="general")
        warn.text = warning
    if primary_group:
        for pgroup in xmltree.iter('Group'):
            if pgroup.attrib['id'] == primary_group:
                pgroup.append(grouping)
    else:
        xmltree.append(grouping)

    #xmlstr = minidom.parseString(ET.tostring(xmltree)).toprettyxml(indent="   ")
    #with open("test.xml", "w") as f:
    #    f.write(xmlstr)
    xmlfile = ET.tostring(xmltree, encoding='utf8', method='xml')
    write_file("shorthand.xml", xmlfile)


def read_yamls_in_dirs(file_type, tree):
    for filename in sorted(os.listdir('.')):
        if filename.endswith(".%s" % file_type):
            with open(os.path.join('.', filename), 'r') as content_file:
                content = yaml.safe_load(content_file)
                if content['documentation_complete'] is not False:
                    yaml_to_xml_mapping(content, tree)


def write_file(filename, content):
    with open(filename, "w") as f:
        f.write(content)


def main():
    parser = argparse.ArgumentParser()
    sub_parser = parser.add_subparsers(help="Content Types")
    xccdf_parser = sub_parser.add_parser("xccdf",
            help="Generate XCCDF content")
    xccdf_parser.add_argument('--shorthand', action="store_true",
            help="Merges content together to create a XML file")

    args, unknown = parser.parse_known_args()
    if unknown:
        sys.stderr.write(
            "Unknown arguments " + ",".join(unknown) + ".\n"
        )
        sys.exit(1)

    if len(sys.argv) < 3:
        print parser.print_help()

    if args.shorthand:
        body = ""
        for prefix, uri in xccdf_ns.items():
             ET.register_namespace(prefix, uri)
        tree = ET.Element('Benchmark')
        xmlfile = read_yamls_in_dirs('group', tree)
        xmlfile = read_yamls_in_dirs('var', tree)
        xmlfile = read_yamls_in_dirs('rule', tree)


if __name__ == "__main__":
    main()

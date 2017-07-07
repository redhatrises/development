#!/usr/bin/python

import os
import os.path
import re
import sys
import argparse
import datetime

from xml.dom import minidom
import yaml


try:
    from xml.etree import cElementTree as ET
except ImportError:
    import cElementTree as ET

try:
    set
except NameError:
    # for python2
    from sets import Set as set


xccdf_ns = {"xsi": "http://www.w3.org/2001/XMLSchema-instance",
            "xhtml": "http://www.w3.org/1999/xhtml",
            "dc": "http://purl.org/dc/elements/1.1/"}

script_extensions = (".yml", ".sh", ".anaconda", ".pp", ".rb", "chef", "py")
ssg_file_ingest_order = ["benchmark", "profile", "group", "var", "rule",
                         "anaconda", "sh", "yml", "pp", "chef", "rb", "py"]

datestamp = datetime.datetime.utcnow().strftime("%Y-%m-%d")


def fix_xml_elements(xmlfile):
    fix_elements = {"&lt;pre&gt;": "<pre>",
                    '&lt;/pre&gt;': '</pre>',
                    '&lt;tt&gt;': '<tt>',
                    '&lt;/tt&gt;': '</tt>',
                    '&lt;li&gt;': '<li>',
                    '&lt;/li&gt;': '</li>',
                    '&lt;ul&gt;': '<ul>',
                    '&lt;/ul&gt;': '</ul>',
                    '&lt;br&gt;': '<br>',
                    '&lt;br&gt;': '</br>',
                    "&lt;i&gt;": "<i>",
                    "&lt;/i&gt;": "</i>"}

    for key, value in fix_elements.iteritems():
        xmlfile = re.sub(key, value, xmlfile)

    return xmlfile


def yaml_key_value(content, key):
    try:
        return content[key]
    except:
        pass


def script_to_xml_mapping(content, filename, xmltree):
    if filename.endswith(".yml"):
        system = "urn:xccdf:fix:script:ansible"
    elif filename.endswith(".sh"):
        system = "urn:xccdf:fix:script:sh"
    elif filename.endswith(".anaconda"):
        system = "urn:redhat:anaconda:pre"
    elif filename.endswith(".pp"):
        system = "urn:xccdf:fix:script:puppet"
    elif filename.endswith(".chef"):
        system = "urn:xccdf:fix:script:chef"
    elif filename.endswith(".rb"):
        system = "urn:xccdf:fix:script:ruby"
    elif filename.endswith(".py"):
        system = "urn:xccdf:fix:script:python"

    filename = filename.split(".")[0]
    for rule in xmltree.iter("Rule"):
        if rule.attrib["id"] == filename:
            script = ET.SubElement(rule, "fix", system=system)
            script.text = content

    return xmltree


def common_xccdf_content(content, xml_tree, title_override=None, desc_override=None):
    description = yaml_key_value(content, "description")
    name = yaml_key_value(content, "title")

    if name:
        title = ET.SubElement(xml_tree, "title")
        title.text = name
        if title_override is not None:
            title.set("override", str(title_override).lower())
    if description:
        desc = ET.SubElement(xml_tree, "description")
        desc.text = description
        if desc_override is not None:
            title.set("override", str(desc_override).lower())

    return xml_tree


def yaml_to_xml_mapping(content, xmltree):
    benchmark = yaml_key_value(content, "status")
    profile = yaml_key_value(content, "profile_id")
    extends = yaml_key_value(content, "extends")
    title_override = yaml_key_value(content, "title_override")
    desc_override = yaml_key_value(content, "desc_override")
    group = yaml_key_value(content, "group_id")
    rule = yaml_key_value(content, "rule_id")
    ocil = yaml_key_value(content, "ocil")
    rationale = yaml_key_value(content, "rationale")
    oval_id = yaml_key_value(content, "oval")
    identifiers = yaml_key_value(content, "identifiers")
    references = yaml_key_value(content, "references")
    warning = yaml_key_value(content, "warning")
    primary_group = yaml_key_value(content, "primary_group")
    variable = yaml_key_value(content, "var_id")
    option = yaml_key_value(content, "options")
    option_val = yaml_key_value(content, "option_val")

    if benchmark:
        for bench in xmltree.iter("Benchmark"):
            status = ET.SubElement(bench, "status", date=datestamp)
            status.text = benchmark
            grouping = common_xccdf_content(content, bench)
            notice = ET.SubElement(bench, "notice", id=content["notice"]["id"])
            notice.text = content["notice"]["description"]
            fmatter = ET.SubElement(bench, "front-matter")
            fmatter = content["front-matter"]
            rmatter = ET.SubElement(bench, "rear-matter")
            rmatter.text = content["rear-matter"]
            version = ET.SubElement(bench, "version")
            version.text = str(content["version"])

    if profile:
        grouping = ET.Element("Profile", id=profile)
        if extends:
            grouping.set("extends", extends)
        if title_override:
            grouping = common_xccdf_content(content, grouping, title_override)
        elif desc_override:
            grouping = common_xccdf_content(content, grouping, desc_override)
        else:
            grouping = common_xccdf_content(content, grouping)

        for refined_values in yaml_key_value(content, "rule_configuration"):
            refined = ET.SubElement(grouping, "refined-value", idref=refined_values["item"])
            refined.set("selector", refined_values["selector"])

        for rules in content["rule_selection"]:
            rule = ET.SubElement(grouping, "select", idref=rules["rule"])
            try:
                rule.set("selected", str(rules["selected"]).lower())
            except KeyError:
                rule.set("selected", "true")

    if group:
        grouping = ET.Element("Group", id=group)
        grouping = common_xccdf_content(content, grouping)
    if variable:
        grouping = ET.Element("Value", id=variable)
        grouping = common_xccdf_content(content, grouping)
        grouping.set("type", content["type"])
        grouping.set("operator", content["operator"])
        grouping.set("interactive", str(content["interactive"]))
        if option:
            for options in option:
                for key, val  in content["options"][options].iteritems():
                    opt = ET.SubElement(grouping, "value", selector=key)
                    opt.text = val

    if rule:
        grouping = ET.Element("Rule", id=rule)
        grouping = common_xccdf_content(content, grouping)
    if ocil:
        ocil_elem = ET.SubElement(grouping, "ocil")
        ocil_elem.set("clause", ocil["clause"])
        ocil_elem.text = ocil["description"]
    if rationale:
        rationale_elem = ET.SubElement(grouping, "rationale")
        rationale_elem.text = rationale
    if oval_id:
        oval = ET.SubElement(grouping, "oval")
        oval.set("id", oval_id)
        if variable:
            oval.set("value", variable["id"])
    if identifiers:
        idents = ET.SubElement(grouping, "ident")
        for ide in identifiers:
            if identifiers[ide] is not None:
                idents.set(ide, identifiers[ide])
    if references:
        refs = ET.SubElement(grouping, "ref")
        for ref in references:
            if references[ref] is not None:
                refs.set(ref, references[ref])
    if warning:
        warn = ET.SubElement(grouping, "warning", category="general")
        warn.text = warning
    if primary_group:
        for pgroup in xmltree.iter("Group"):
            if pgroup.attrib["id"] == primary_group:
                pgroup.append(grouping)
    elif not benchmark:
        xmltree.append(grouping)

    #xmlstr = minidom.parseString(ET.tostring(xmltree)).toprettyxml(indent="   ")
    #with open("test.xml", "w") as f:
    #    f.write(xmlstr)
    #xmlfile = ET.tostring(xmltree, encoding="utf8", method="xml")
    #write_file("shorthand.xml", xmlfile)

    return xmltree


def files_or_map(group_map, files):
    filenames = ""

    if group_map["map"] == "":
        return sorted(files)

    for key, values in group_map.iteritems():
        for value in values:
            if value in files:
                filenames = group_map["map"]
            else:
                filenames = sorted(files)

    return filenames


def read_content_in_dirs(filetype, tree, directory, group_map={"map": ""}):
    for dirs in directory:
        for root, dirs, files in sorted(os.walk(dirs)):
            for filename in files_or_map(group_map, files):
                with open(os.path.join(root, filename), "r") as content_file:
                    if filename.endswith(".%s" % filetype):
                        if not filename.endswith(script_extensions):
                            content = yaml.safe_load(content_file)
                            if content["documentation_complete"] is not False:
                                tree = yaml_to_xml_mapping(content, tree)
                        else:
                            content = content_file.read()
                            tree = script_to_xml_mapping(content, filename, tree)

    xtree = ET.tostring(tree)
    write_file("shorthand.xml", xtree)

    return tree


def read_group_map(directory):
    for dirs in directory:
        for root, dirs, files in sorted(os.walk(dirs)):
            for filename in sorted(files):
                if filename.endswith(".map"):
                    with open(os.path.join(root, filename), "r") as content_file:
                        group_map = yaml.safe_load(content_file)
    return group_map


def write_file(filename, content):
    with open(filename, "w") as outputfile:
        outputfile.write(content)


def main():
    xccdf_xmlns = "http://checklists.nist.gov/xccdf/1.1"
    parser = argparse.ArgumentParser()
    sub_parser = parser.add_subparsers(help="Content Types")
    xccdf_parser = sub_parser.add_parser("xccdf", help="Generate XCCDF content")
    xccdf_parser.add_argument("--shorthand", action="store_true",
                              help="Merges content together to create a XML file")
    xccdf_parser.add_argument("--product", action="store",
                              default="product_name", required=False,
                              help="Name of the product [Default: %(default)s]")
    xccdf_parser.add_argument("--scap_version", action="store",
                              default="SCAP_1.1", required=False,
                              help="SCAP version [Default: %(default)s]")
    xccdf_parser.add_argument("--xccdf_xmlns", action="store",
                              default=xccdf_xmlns, required=False,
                              help="SCAP version [Default: %(default)s]")
    xccdf_parser.add_argument("--schema", action="store",
                              default=xccdf_xmlns + " xccdf-1.1.4.xsd",
                              required=False,
                              help="Schema namespace and XML schema [Default: %(default)s]")
    xccdf_parser.add_argument("--resolved", action="store",
                              default="false", required=False,
                              help=" [Default: %(default)s]")
    xccdf_parser.add_argument("--lang", action="store",
                              default="en_US", required=False,
                              help="Language of XML file [Default: %(default)s]")
    xccdf_parser.add_argument("directory", metavar="DIRECTORY", nargs="+",
                              help="Location of content to combine into the final document")

    args, unknown = parser.parse_known_args()
    if unknown:
        sys.stderr.write(
            "Unknown arguments " + ",".join(unknown) + ".\n"
        )
        sys.exit(1)

    if len(sys.argv) < 3:
        parser.error(parser.print_help())

    directory = args.directory

    if args.shorthand:
        tree = ET.Element("Benchmark")
        tree.set("id", args.product)
        tree.set("xsi:schemaLocation", args.schema)
        tree.set("style", args.scap_version.upper())
        tree.set("resolved", args.resolved.lower())
        tree.set("xml:lang", args.lang)
        xmlfile = read_content_in_dirs("benchmark", tree, directory)

        group_map = read_group_map(directory)

        for prefix, uri in xccdf_ns.items():
            tree.set("xmlns:" + prefix, uri)

        for order in ssg_file_ingest_order:
            xmlfile = read_content_in_dirs(order, tree, directory, group_map)

        xmlfile = ET.tostring(xmlfile)
        xmlfile = fix_xml_elements(xmlfile)
        write_file("shorthand.xml", xmlfile)


if __name__ == "__main__":
    main()

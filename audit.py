# audit.py
import xml.etree.cElementTree as ET
import re

""" Finding unique tags and frequency of the tags """
def count_tags(filename):
        tags = {}
        for event, elem in ET.iterparse(filename, events=("start",)):
            if elem.tag not in tags:
                tags[elem.tag] = 1
            else:
                tags[elem.tag] += 1
        return tags
    

""" Finding unique keys of tag element and frequency of the keys """
def count_tag_keys(filename):
    tag_keys = {}
    for event, elem in ET.iterparse(filename, events=("start",)):
        if elem.tag == "tag":
             for tag in elem.iter('tag'):
                k = tag.get('k')
                if k not in tag_keys:
                    tag_keys[k] = 1
                else:
                    tag_keys[k] += 1
    return tag_keys


""" Finding problematic keys """
# Compile a regular expression pattern into a regular expression object
without_colons = re.compile(r'^([a-z]|_)*$', re.IGNORECASE)
without_colons_num = re.compile(r'^([a-z]|_)*\d$', re.IGNORECASE)
with_colons = re.compile(r'^([a-z]|_)+:([a-z]|_)+', re.IGNORECASE)
problemchars = re.compile(r'[=\+/&<>;\'\"\?%#$@\,\. \t\r\n]')

# Finding the number of problematic keys
def count_key_types(filename):
    count_keys = {"without_colons": 0, "with_colons": 0, "problemchars": 0, "other": 0}
    for event, elem in ET.iterparse(filename, events=("start",)):
        if elem.tag == "tag":
             for tag in elem.iter('tag'):
                k = tag.get('k')
                if without_colons.search(elem.attrib['k']) or without_colons_num.search(elem.attrib['k']):  
                    count_keys['without_colons'] = count_keys['without_colons'] + 1
                elif with_colons.search(elem.attrib['k']):
                    count_keys['with_colons'] = count_keys['with_colons'] + 1
                elif problemchars.search(elem.attrib['k']):
                    count_keys['problemchars'] = count_keys['problemchars'] + 1
                else:
                    count_keys['other'] = count_keys['other'] + 1
    
    return count_keys

# Finding problematic keys
def key_type(filename):
    keys = {"without_colons": set(), "with_colons": set(), "problemchars": set(), "other": set()}
    for event, elem in ET.iterparse(filename, events = ('start',)):
        if elem.tag == "tag":
            for tag in elem.iter('tag'):
                if without_colons.search(elem.attrib['k']) or without_colons_num.search(elem.attrib['k']):
                    keys['without_colons'].add(tag.attrib['k'])
                elif with_colons.search(elem.attrib['k']):
                    keys['with_colons'].add(tag.attrib['k'])
                elif problemchars.search(elem.attrib['k']):
                    keys['problemchars'].add(tag.attrib['k'])
                else:
                    keys['other'].add(tag.attrib['k'])
    return keys


""" Finding unique street types """
# Compile a regular expression pattern into a regular expression object
street_type_re = re.compile(r'\b\S+\.?$', re.IGNORECASE) # matches the very last word in a street name

# Finding unique street types
def get_street_types(filename):
    street_names = set() # a set is an unordered collection with no duplicate elements
    street_types = set()
    for event, elem in ET.iterparse(filename, events=("start",)):
        if elem.tag in ['node','way']:
            for tag in elem.iter("tag"): # elem.iter returns iteration all tags nested within the elem
                if tag.attrib['k'] == "addr:street":
                    v = tag.get('v')
                    if v != "":
                        street_names.add(v)
    for street_name in street_names:
        m = street_type_re.search(street_name) # search the pattern in the street_name 
        if m: 
            street_type = m.group() # returns subgroups of the match, 
                                    # no argument sets to zero, meaning the whole match is returned
            if street_type not in street_types:
                street_types.add(street_type)
    return street_types


""" Finding unique users """
def get_user(filename):
    users = set() # a set is an unordered collection with no duplicate elements
    for event, elem in ET.iterparse(filename, events=("start",)):
        if elem.tag in ['node','way','relation']:
            u = elem.attrib['uid'] # or alternatively you can use u = elem.get('uid')
            if u != "":
                users.add(u)

    return users

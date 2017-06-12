#process_osm.py
import xml.etree.cElementTree as ET
import re
from collections import defaultdict
import cerberus
import map_schema # is local py file
import csv
import codecs


""" Iterparsing to get each top level elment in the xml """
def get_element(filename):
    context = ET.iterparse(filename, events = ('start', )) # get an iterable
    evnt, root = context.next() # access the next interation, 
                                # in this case 'osm' element, which is root
                                # then moves on to the following iteration without executing for-loop below
    for event, elem in context:
        if elem.tag in ['node', 'way']:
            yield elem 
            root.clear()


""" Updating abbreviation into full name of street names """            
# The dictionary of to_fullname needs to be updated depending on the output of get_street_types
to_fullname = {"St": "Street",
            "St.": "Street",
            "Ave": "Avenue",
            "Rd.": "Road",
            "Rd":  "Road",
            "Blvd": "Boulevard",
            "Blvd.": "Boulevard",
            "Bl": "Boulevard",
            "DRIVE": "Drive",
            "Dr": "Drive",
            "Ct": "Court",
            "Ct.": "Court",
            "Pl": "Place",
            "Sq": "Square",
            "La": "Lane",
            "Ln": "Lane",
            "Tr": "Trail",
            "Pkwy": "Parkway",
            "Pkwy.": "Parkway",
            "Cmns": "Commons"
           }

# Helper procedure: change string into titleCase except for UpperCase
def string_case(s): 
    if s.isupper():
        return s
    else:
        return s.title()

# Updating abbreviation into full name of street names    
def update_name(name):
    name = name.split(' ')
    for i in range(len(name)):
        if name[i] in to_fullname:
            name[i] = to_fullname[name[i]]
            name[i] = string_case(name[i])
        else:
            name[i] = string_case(name[i])
    updated_name = ' '.join(name)
    return updated_name
            

""" Cleaning and Shaping xml elements to a dictionary 

rules
1. If the element top level tag is "node":
The dictionary returned should have the format {"node": .., "node_tags": ...}

1-1. The "node" field should hold a dictionary of the following top level node attributes:
- id
- user
- uid
- version
- lat
- lon
- timestamp
- changeset
All other attributes can be ignored

1-2. The "node_tags" field should hold a list of dictionaries, one per secondary tag. 
Secondary tags are child tags of node which have the tag name/type: "tag". 

Each dictionary should have the following

fields from the secondary tag attributes:
- id: the top level node id attribute value
- key: the full tag "k" attribute value if no colon is present or the characters after the colon if one is.
- value: the tag "v" attribute value
- type: either the characters before the colon in the tag "k" value or "regular" if a colon is not present.

- if the tag "k" value contains problematic characters, the tag should be ignored
- if the tag "k" value contains a ":" the characters before the ":" should be set as the tag type
  and characters after the ":" should be set as the tag key
- if there are additional ":" in the "k" value they and they should be ignored and kept as part of
  the tag key. 
- If a node has no secondary tags then the "node_tags" field should just contain an empty list.


2. If the element top level tag is "way":
The dictionary should have the format {"way": ..., "way_tags": ..., "way_nodes": ...}

2-1. The "way" field should hold a dictionary of the following top level way attributes:
- id
- user
- uid
- version
- timestamp
- changeset
All other attributes can be ignored

2-2. The "way_tags" field should again hold a list of dictionaries, 
following the exact same rules as for "node_tags".

2-3. The dictionary should have a field "way_nodes". "way_nodes" should hold a list of
dictionaries, one for each nd child tag.  

Each dictionary should have the fields:
- id: the top level element (way) id
- node_id: the ref attribute value of the nd tag
- position: the index starting at 0 of the nd tag i.e. what order the nd tag appears within the way element

"""


# Compile a regular expression pattern into a regular expression object
WITH_COLONS = re.compile(r'^([a-z]|_)+:([a-z]|_)+', re.IGNORECASE)
PROBLEMCHARS = re.compile(r'[=\+/&<>;\'\"\?%#$@\,\. \t\r\n]')

# definding sub-keys for each key
NODE_FIELDS = ['id', 'lat', 'lon', 'user', 'uid', 'version', 'changeset', 'timestamp']
NODE_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_FIELDS = ['id', 'user', 'uid', 'version', 'changeset', 'timestamp']
WAY_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_NODES_FIELDS = ['id', 'node_id', 'position']

# Cleaning and Shaping xml elements to a dictionary
def shape_element(element, default_tag_type='regular'):

    node_attribs = {}
    way_attribs = {}
    way_nodes = []
    tags = [] # handle secondary tags the same way for both node and way elements 

    if element.tag == 'node':
        for field in NODE_FIELDS:
            node_attribs[field] = element.attrib[field] # alternatively, element.get(attrib)
       
        for tag in element.iter('tag'):
            node_tag = {}
            node_tag['id'] = element.attrib['id']
            
            if PROBLEMCHARS.match(tag.attrib['k']):
                pass # tag 'k' value containing problematic characters should be ignored
            elif WITH_COLONS.match(tag.attrib['k']):
                node_tag['type'] = tag.attrib['k'].split(':',1)[0] # split by the first colon 
                                                                   # and ignore the second colon
                                                                   # type is char before the first colon
                node_tag['key'] = tag.attrib['k'].split(':',1)[1]
            else:
                node_tag['type'] = 'regular' # type is 'regular' if no colon tag 'k' value
                node_tag['key'] = tag.attrib['k']
            
            if tag.attrib['k'] == 'addr:street':
                node_tag['value'] = update_name(tag.attrib['v']) # update street type
            else:
                node_tag['value'] = tag.attrib['v']
            tags.append(node_tag)
        
        return {'node': node_attribs, 'node_tags': tags}
        
    elif element.tag == 'way':
        for field in WAY_FIELDS:
            way_attribs[field] = element.attrib[field]
        
        position = 0
        for nd in element.iter('nd'):
            way_nd = {}
            way_nd['id'] = element.attrib['id']
            way_nd['node_id'] = nd.attrib['ref']
            way_nd['position'] = position # indicates order of way nodes
            position += 1
            way_nodes.append(way_nd)
        
        for tag in element.iter('tag'):
            way_tag = {}
            way_tag['id'] = element.attrib['id']
            if PROBLEMCHARS.match(tag.attrib['k']):
                pass
            elif WITH_COLONS.match(tag.attrib['k']):
                way_tag['type'] = tag.attrib['k'].split(':',1)[0] 
                way_tag['key'] = tag.attrib['k'].split(':',1)[1]
            else:
                way_tag['type'] = 'regular'
                way_tag['key'] = tag.attrib['k']    
            way_tag['value'] = tag.attrib['v']
            tags.append(way_tag)
               
        return {'way': way_attribs, 'way_nodes': way_nodes, 'way_tags': tags}


""" Validating a shaped dictionary """         
validator = cerberus.Validator()
MAP_SCHEMA = map_schema.schema 

def validate_element(shaped_dict):
    if validator.validate(shaped_dict, MAP_SCHEMA) is not True:
        field, errors = next(validator.errors.iteritems())
        message_string = "\nElement of type '{0}' has the following errors:\n{1}"
        error_strings = (
            "{0}: {1}".format(k, v if isinstance(v, str) else ", ".join(v))
            for k, v in errors.iteritems()
        )
        raise cerberus.ValidationError(
            message_string.format(field, "\n".join(error_strings))
        )


""" Extending csv.DictWriter to handle Unicode input """
class UnicodeDictWriter(csv.DictWriter, object):

    def writerow(self, row):
        super(UnicodeDictWriter, self).writerow({
            k: (v.encode('utf-8') if isinstance(v, unicode) else v) for k, v in row.iteritems()
        })

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)


# ================================================== #
#               Main Function                        #
# ================================================== #
""" Writing each key into a separate csv file """

NODES_PATH = "bburg_nodes.csv"
NODE_TAGS_PATH = "bburg_nodes_tags.csv"
WAYS_PATH = "bburg_ways.csv"
WAY_NODES_PATH = "bburg_ways_nodes.csv"
WAY_TAGS_PATH = "bburg_ways_tags.csv"

def process_map(filename):
    
    with codecs.open(NODES_PATH, 'w') as nodes_file, \
         codecs.open(NODE_TAGS_PATH, 'w') as nodes_tags_file, \
         codecs.open(WAYS_PATH, 'w') as ways_file, \
         codecs.open(WAY_NODES_PATH, 'w') as way_nodes_file, \
         codecs.open(WAY_TAGS_PATH, 'w') as way_tags_file:

        nodes_writer = UnicodeDictWriter(nodes_file, NODE_FIELDS)
        node_tags_writer = UnicodeDictWriter(nodes_tags_file, NODE_TAGS_FIELDS)
        ways_writer = UnicodeDictWriter(ways_file, WAY_FIELDS)
        way_nodes_writer = UnicodeDictWriter(way_nodes_file, WAY_NODES_FIELDS)
        way_tags_writer = UnicodeDictWriter(way_tags_file, WAY_TAGS_FIELDS)

        nodes_writer.writeheader()
        node_tags_writer.writeheader()
        ways_writer.writeheader()
        way_nodes_writer.writeheader()
        way_tags_writer.writeheader()
            
        for elem in get_element(filename):
            shaped_dict = shape_element(elem)
                
            if shaped_dict:
                validate_element(shaped_dict)

                if elem.tag == 'node':
                    nodes_writer.writerow(shaped_dict['node'])
                    node_tags_writer.writerows(shaped_dict['node_tags'])
                elif elem.tag == 'way':
                    ways_writer.writerow(shaped_dict['way'])
                    way_nodes_writer.writerows(shaped_dict['way_nodes'])
                    way_tags_writer.writerows(shaped_dict['way_tags'])


if __name__ == '__main__':
    filename = 'bburg_map.xml'
    process_map(filename)



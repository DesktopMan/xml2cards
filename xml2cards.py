#!/usr/bin/python3
import sys
from xml.etree import ElementTree
import json
import pyphen


def get_type_info(item_type):
    info = {
        '$': {'name': 'Treasure', 'icon': 'locked-chest', 'color': 'darkgoldenrod'},
        'P': {'name': 'Potion', 'icon': 'drink-me', 'color': 'maroon'},
        'G': {'name': 'Gear', 'icon': 'gear-hammer', 'color': 'maroon'},
        'LA': {'name': 'Light Armor', 'icon': 'leather-vest', 'color': 'dimgray'},
        'MA': {'name': 'Medium Armor', 'icon': 'breastplate', 'color': 'dimgray'},
        'HA': {'name': 'Heavy Armor', 'icon': 'mail-shirt', 'color': 'dimgray'},
        'S': {'name': 'Shield', 'icon': 'round-shield', 'color': 'dimgray'},
        'M': {'name': 'Melee Weapon', 'icon': 'crossed-swords', 'color': 'dimgray'},
        'R': {'name': 'Ranged Weapon', 'icon': 'pocket-bow', 'color': 'dimgray'},
        'A': {'name': 'Ammunition', 'icon': 'target-arrows', 'color': 'dimgray'},
        'ST': {'name': 'Staff', 'icon': 'wizard-staff', 'color': 'indigo'},
        'RD': {'name': 'Rod', 'icon': 'orb-wand', 'color': 'indigo'},
        'RG': {'name': 'Ring', 'icon': 'ring', 'color': 'darkgreen'},
        'W': {'name': 'Wondrous Item', 'icon': 'swap-bag', 'color': 'darkgreen'},
        'WD': {'name': 'Wand', 'icon': 'crystal-wand', 'color': 'indigo'},
        'SC': {'name': 'Spell Scroll', 'icon': 'tied-scroll', 'color': 'indigo'},
    }

    if item_type in info:
        return info[item_type]

    return {'name': 'Unknown type', 'icon': 'cross-mark', 'color': 'black'}


def get_item_properties():
    return {
        'name': 'name',
        'type': 'type',
        'weight': 'weight',
        'ac': 'ac',
        'stealth': 'stealth',
        'dmg1': 'dmg',
        'dmg2': 'dmg',
        'dmgType': 'type',
        'property': 'prop',
        'range': 'range',
        'text': 'text',
        'modifier': 'mod',
        'roll': 'roll',
        'value': 'value'
    }


class Item:
    def __init__(self):
        for p in get_item_properties():
            setattr(self, p[0], "")


def load_items(filename):
    items = []

    for e in ElementTree.parse(filename).getroot():
        if e.tag != 'item':
            continue

        item = Item()
        for prop_name in get_item_properties():
            # Convert tags to newlines
            for t in e.findall(prop_name):
                if not t.text:
                    t.text = ""

            setattr(item, prop_name, '\n'.join([t.text for t in e.findall(prop_name)]))

        items.append(item)

    return items


def convert_item(item, dic):
    result = {}
    type_info = get_type_info(item.type)

    # Basic info
    if item.type == '$':
        result['title'] = item.name[item.name.find(' - ') + 3:]
        item.value = item.name[0:item.name.find(' - ')]
    else:
        result['title'] = item.name

    result['color'] = type_info['color']
    result['icon'] = type_info['icon']
    result['icon_back'] = type_info['icon']

    # Properties
    result['contents'] = []
    result['contents'].append('subtitle | %s' % type_info['name'])

    result['contents'].append('rule')

    properties_added = 0

    for prop_name, prop_display in get_item_properties().items():
        prop_value = getattr(item, prop_name)

        if prop_name == 'name' or prop_name == 'type' or prop_name == 'text' or prop_value == '' or prop_value == 0:
            continue

        for v in prop_value.split('\n'):
            result['contents'].append('property | %s | %s' % (prop_display, v))
            properties_added += 1

    if properties_added > 0:
        result['contents'].append('rule')

    # Text
    for line in item.text.split('\n'):
        line = line.strip()

        if line == '':
            continue
        elif line.startswith("Source:"):
            result['contents'].append('fill')
            result['contents'].append('rule')

            line = line.replace('Source: ', '')

            result['contents'].append('center | %s' % line)
        else:
            result['contents'].append('justify | %s\n' % ' '.join([dic.inserted(w, '\u00ad') for w in line.split(' ')]))

    # Tags
    result['tags'] = [type_info['name'].lower()]

    return result


def convert_items(items, name_filter):
    dic = pyphen.Pyphen(lang='en_US')
    result = []

    for item in items:
        count = name_filter.count(item.name)

        if count == 0:
            continue

        item = convert_item(item, dic)
        item['count'] = count
        result.append(item)

    found = []
    for item in result:
        found.append(item['title'])

    missing = []
    for item in name_filter:
        if item not in found and item != '' and not item.startswith('#'):
            missing.append(item)

    return result, missing


def main():
    if len(sys.argv) != 4:
        print('Usage: xml2cards.py <items.xml>', '<items.txt>', '<output.json>')
        exit(0)

    xml_file = sys.argv[1]
    filter_file = sys.argv[2]
    json_file = sys.argv[3]

    name_filter = []
    with open(filter_file, 'r') as f:
        name_filter.extend(f.read().splitlines())

    items = load_items(xml_file)
    converted, missing = convert_items(items, name_filter)

    if len(missing) > 0:
        print('Missing items:\n%s' % '\n'.join(missing))

    print('Done.')

    with open(json_file, 'w') as f:
        f.write(json.dumps(converted, indent=2))

if __name__ == '__main__':
    main()

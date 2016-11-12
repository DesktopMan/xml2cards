#!/usr/bin/python3
import os
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
        'name': 'Name',
        'type': 'Type',
        'weight': 'Weight',
        'ac': 'Armor Class',
        'stealth': 'Stealth',
        'dmg1': 'Damage',
        'dmg2': 'Damage',
        'dmgType': 'Type',
        'property': 'Property',
        'range': 'Range',
        'text': 'Text',
        'modifier': 'Modifier',
        'roll': 'Roll',
        'value': 'Value',
        'rarity': 'Rarity'
    }


class Item:
    def __init__(self):
        for p in get_item_properties():
            setattr(self, p[0], "")


def load_items(filename):
    items = {}

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

        # Remove value from the name of valuables
        if item.type == '$':
            item.name = item.name[item.name.find(' - ') + 3:]

        items[item.name.lower()] = item

    return items


def convert_item(item, dic):
    result = {}

    type_info = get_type_info(item.type)

    result['title'] = item.name
    result['color'] = type_info['color']
    result['icon'] = type_info['icon']
    result['icon_back'] = type_info['icon']

    # Properties
    result['contents'] = []
    if item.rarity == '':
        result['contents'].append('subtitle | %s' % type_info['name'])
    else:
        result['contents'].append('subtitle | %s (%s)' % (type_info['name'], item.rarity))

    result['contents'].append('rule')

    properties_added = 0

    for prop_name, prop_display in get_item_properties().items():
        prop_value = getattr(item, prop_name)

        # Skip properties already displayed elsewhere
        if prop_name in ['name', 'type', 'text', 'rarity'] or prop_value in ['', '0', 0]:
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
        elif line.startswith("Rarity:"):
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


def convert_items(items, items_wanted):
    dic = pyphen.Pyphen(lang='en_US')
    result = []
    missing = []

    for wanted in items_wanted:
        if not wanted or wanted.startswith('#'):  # Empty line or commented out
            continue

        count = wanted.split()
        if count[0].isdigit():
            wanted = ' '.join(count[1:])
            count = int(count[0])
        else:
            count = 1

        # Item was not found
        if not wanted.lower() in items:
            missing.append(wanted)
            continue

        item = convert_item(items[wanted.lower()], dic)
        item['count'] = count
        result.append(item)

    return result, missing


def main():
    print('--------------------------')
    print('XML to RPG cards converter')
    print('--------------------------\n')

    if len(sys.argv) != 4:
        print('Usage: xml2cards.py <items.xml>', '<filter.txt>', '<output.json>\n')
        exit(0)

    xml_file = sys.argv[1]
    filter_file = sys.argv[2]
    json_file = sys.argv[3]

    if not os.path.isfile(xml_file):
        print('Error: \'%s\' is not a file.\n' % xml_file)
        exit(1)

    if not os.path.isfile(filter_file):
        print('Error: \'%s\' is not a file.\n' % filter_file)
        exit(1)

    name_filter = []
    with open(filter_file, 'r') as f:
        name_filter.extend(f.read().splitlines())

    items = load_items(xml_file)
    converted, missing = convert_items(items, name_filter)

    if len(missing) > 0:
        print('Missing items:\n%s' % '\n'.join(missing))

    with open(json_file, 'w') as f:
        f.write(json.dumps(converted, indent=2))

    print('Done. Wrote %d items to \'%s\' JSON file.' % (len(converted), json_file))

if __name__ == '__main__':
    main()

#!/usr/bin/python3
import sys
from xml.etree import ElementTree as et
import json
import pyphen


def get_type_info(itemType):
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

    if itemType in info:
        return info[itemType]

    return {'name': 'Unknown type', 'icon': 'cross-mark', 'color': 'black'}


class Item:
    properties = [
        'name',
        'type',
        # 'weight',
        'ac',
        'stealth'
        'dmg1',
        'dmg2',
        'dmgType',
        'property',
        'range',
        'text',
        'modifier',
        'roll',
        'value'
    ]

    def __init__(self):
        for p in self.properties:
            setattr(self, p, "")


def load_items(filename, filter = []):
    items = []

    for e in et.parse(filename).getroot():
        if e.tag == 'item':
            item = Item()
            for p in Item.properties:

                # Convert tags to newlines
                for t in e.findall(p):
                    if not t.text:
                        t.text = ""

                setattr(item, p, '\n'.join([t.text for t in e.findall(p)]))

            if len(filter) == 0 or item.name in filter:
                items.append(item)

    return items


def convert_item(item, dic):
    result = {}
    info = get_type_info(item.type)

    # Basic info
    if item.type == '$':
        result['title'] = item.name[item.name.find(' - ') + 3:]
        item.value = item.name[0:item.name.find(' - ')]
    else:
        result['title'] = item.name

    result['color'] = info['color']
    result['icon'] = info['icon']
    result['icon_back'] = info['icon']
    result['count'] = 1

    # Properties
    result['contents'] = []
    result['contents'].append('subtitle | %s' % info['name'])

    result['contents'].append('rule')

    properties_added = 0

    for prop in item.properties:
        value = getattr(item, prop)

        if prop == 'name' or prop == 'type' or prop == 'text' or value == '' or value == '0':
            continue

        for v in value.split('\n'):
            result['contents'].append('property | %s | %s' % (prop, v))
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
    result['tags'] = [info['name'].lower()]

    return result


def convert_items(items):
    dic = pyphen.Pyphen(lang='en_US')
    result = []

    for item in items:
        result.append(convert_item(item, dic))

    return result

if __name__ == '__main__':
    items = load_items('items.xml', sys.argv[1:])
    converted = convert_items(items)

    print(json.dumps(converted, indent=2))

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

    for e in et.parse(filename).getroot():
        if e.tag != 'item':
            continue

        item = Item()
        for propName in get_item_properties():
            # Convert tags to newlines
            for t in e.findall(propName):
                if not t.text:
                    t.text = ""

            setattr(item, propName, '\n'.join([t.text for t in e.findall(propName)]))

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

    for propName, propDisplay in get_item_properties().items():
        propValue = getattr(item, propName)

        if propName == 'name' or propName == 'type' or propName == 'text' or propValue == '' or propValue == 0:
            continue

        for v in propValue.split('\n'):
            result['contents'].append('property | %s | %s' % (propDisplay, v))
            properties_added += 1

    if properties_added > 0:
        result['contents'].append('rule')

    # Text
    previous_justify = False

    for line in item.text.split('\n'):
        line = line.strip()

        if line == '':
            continue
        elif line.startswith("Source:"):
            result['contents'].append('fill')
            result['contents'].append('rule')

            line = line.replace('Source: ', '')

            result['contents'].append('center | %s' % line)

            previous_justify = False
        else:
            if not previous_justify:
                result['contents'].append('\n')
            result['contents'].append('justify | %s\n' % ' '.join([dic.inserted(w, '\u00ad') for w in line.split(' ')]))
            previous_justify = True

    # Tags
    result['tags'] = [type_info['name'].lower()]

    return result


def convert_items(items, filter):
    dic = pyphen.Pyphen(lang='en_US')
    result = []

    for item in items:
        count = filter.count(item.name)

        if count == 0:
            continue

        item = convert_item(item, dic)
        item['count'] = count
        result.append(item)

    return result

if __name__ == '__main__':
    filename = sys.argv[1]

    filter = sys.argv[2:]
    filter.extend(sys.stdin.read().splitlines())

    items = load_items('items.xml')
    converted = convert_items(items, filter)

    with open(filename, 'w') as f:
        f.write(json.dumps(converted, indent=2))

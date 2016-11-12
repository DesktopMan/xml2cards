#!/usr/bin/python3
import os
import sys
import collections
from xml.etree import ElementTree
import argparse
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
        'property': 'Properties',
        'range': 'Range',
        'text': 'Text',
        'modifier': 'Modifier',
        'roll': 'Roll',
        'value': 'Value',
        'rarity': 'Rarity'
    }


def get_icon_override(name):
    overrides = {
        'Belt of': 'belt',
        'Book of': 'book-cover',
        'Boots of': 'boots',
        'Bracers of': 'bracer',
        'Cloak of': 'cloak',
        'Gloves of': 'hand',
        'Helm of': 'crested-helmet',
        'Horn of': 'hunting-horn',
        'Tome of': 'book-cover'
    }

    for key, value in overrides.items():
        if name.startswith(key):
            return value

    return None


class Item:
    def __init__(self):
        for p in get_item_properties():
            setattr(self, p[0], "")


def load_items(filename):
    items = collections.OrderedDict()

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

        # Add bonus damage to damage roll
        for m in item.modifier.split('\n'):
            if m.startswith('melee damage') or m.startswith('ranged damage') or m.startswith('weapon damage'):
                damage = m[m.find('+'):]
                if item.dmg1:
                    item.dmg1 += ' %s' % damage

                if item.dmg2:
                    item.dmg2 += ' %s' % damage

                item.modifier = item.modifier.replace(m, '')

        # Add damage type to damage roll
        if item.dmgType:
            if item.dmg1:
                item.dmg1 += ' %s' % item.dmgType

            if item.dmg2:
                item.dmg2 += ' %s' % item.dmgType

        item.dmgType = ''

    return items


def convert_item(item, dic, exclude_properties):
    result = {}

    type_info = get_type_info(item.type)

    result['title'] = item.name
    result['color'] = type_info['color']
    icon = get_icon_override(item.name)
    result['icon'] = icon if icon else type_info['icon']

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

        # Skip properties already displayed elsewhere and excluded properties
        ignored_properties = ['name', 'type', 'text', 'rarity', 'dmgType']
        if exclude_properties:
            ignored_properties.extend(exclude_properties)
        if prop_name in ignored_properties or prop_value in ['', '0', 0]:
            continue

        for v in prop_value.split('\n'):
            if v:
                result['contents'].append('property | %s | %s' % (prop_display, v))
                properties_added += 1

    if properties_added > 0:
        result['contents'].append('rule')

    # Text
    for line in item.text.split('\n'):
        line = line.strip()

        properties = [
            'Ammunition:', 'Finesse:', 'Heavy:', 'Light:', 'Loading:', 'Range:', 'Rarity:', 'Special:', 'Thrown:',
            'Two-Handed:', 'Versatile:'
        ]

        if line == '':
            continue
        elif line.split()[0] in properties:
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


def convert_items(items, items_wanted, exclude_properties):
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

        item = convert_item(items[wanted.lower()], dic, exclude_properties)
        item['count'] = count
        result.append(item)

    return result, missing


def convert(args, items):
    if not os.path.isfile(args.filter_file):
        print('Error: \'%s\' is not a file.\n' % args.filter_file)
        exit(1)

    name_filter = []
    with open(args.filter_file, 'r') as f:
        name_filter.extend(f.read().splitlines())

    converted, missing = convert_items(items, name_filter, args.exclude)

    if len(missing) > 0:
        print('Missing items:\n%s' % '\n'.join(missing))

    with open(args.output_file, 'w') as f:
        f.write(json.dumps(converted, indent=2))

    print('Done. Wrote %d items to \'%s\' JSON file.\n' % (len(converted), args.output_file))


def search(args, items):
    print('Searching for \'%s\'...\n' % args.filter)
    for key, item in items.items():
        if args.filter.lower() in key:
            print(''.center(len(item.name), '-'))
            print(item.name)
            print(''.center(len(item.name), '-'))
            print()
            print(item.text)
            print()


def main():
    print('==========================')
    print('XML to RPG cards converter')
    print('==========================\n')

    # Set up the CLI arguments and parse them
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(help='Choose sub-command')

    parser_convert = subparsers.add_parser('convert', help='Convert XML to JSON')
    parser_convert.add_argument('xml_file', help='XML item input file')
    parser_convert.add_argument('filter_file', help='Item text filter file')
    parser_convert.add_argument('output_file', help='JSON item output file')
    exclude_choices = [p for p in get_item_properties()]
    [exclude_choices.remove(p) for p in ['name', 'type', 'text', 'rarity', 'dmgType']]
    parser_convert.add_argument('--exclude', choices=exclude_choices, nargs='*', help='Exclude properties')
    parser_convert.set_defaults(func=convert)

    parser_search = subparsers.add_parser('search', help='Search for items')
    parser_search.add_argument('xml_file', help='XML input file')
    parser_search.add_argument('filter', help='Item name filter')
    parser_search.set_defaults(func=search)

    args = parser.parse_args()

    if len(sys.argv) == 1:
        parser.print_help()
        exit(0)

    if not os.path.isfile(args.xml_file):
        print('Error: \'%s\' is not a file.\n' % args.xml_file)
        exit(1)

    items = load_items(args.xml_file)
    args.func(args, items)

if __name__ == '__main__':
    main()

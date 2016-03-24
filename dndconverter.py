from xml.etree import ElementTree as et

class Item:
    properties = [
        'name',
        'type',
        'weight',
        'ac',
        'stealth'
        'dmg1',
        'dmg2',
        'dmgType',
        'property',
        'range',
        'text',
        'modifier',
        'roll'
    ]

    def __init__(self):
        for p in self.properties:
            setattr(self, p, "")


def load_items(filename):
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

            items.append(item)

    for i in items:
        for p in Item.properties:
            print('%s: %s' % (p, getattr(i, p)))

        print('')

    return items


def get_menu_choice(choices):

    print('0: Back')

    for i, c in enumerate(choices, start=1):
        print("%i: %s" % (i, c))

    choice = -1

    while choice < 0:
        choice = int(input('Pick a choice'))
        if choice < 0 or choice > len(choices):
            print('Invalid choice. Try again.')
            choice = -1

    return choice

if __name__ == '__main__':

    items = load_items('items.xml')
    choice = get_menu_choice(['Search by name', 'Search by description', 'Exit'])

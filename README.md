# About

xml2cards converts item descriptions in the [DnD App Files](https://github.com/ceryliae/DnDAppFiles) format to the JSON
format required by [RPG cards](https://desktopman.github.io/rpg-cards/generator/generate.html). Note that I've made some
changes to RPG cards to support text justify and center.

The script automatically maps item types to card colors and icons and adds all the properties for you. 

# Requirements

The Python module *pyphen* is used for hyphenation.

# Usage

## Convert

1. Type in the items your group has in a text file (one per line)

2. Run the script:
   ```
   ./xml2cards.py convert items.xml filter.txt output.json
   ```

3. Load the JSON file in RPG cards and edit as you see fit

### Excluding properties

If you want to exclude one or more properties you can do that with the --exclude option:

```
./xml2cards.py convert items.xml filter.txt output.json --exclude weight
```

* ac
* dmg1
* dmg2
* modifier
* property
* range
* roll
* stealth
* value
* weight

## Search

You can also search for items. This matches text anywhere in the name and displays the item description:

```
./xml2cards.py search items.xml potion
```

# Example filter.txt

You can add multiples of an item by writing the count first. Lines starting with # will be ignored.

```
# Valuables
3 Malachite

# Items
Bag of Holding
Ring of Regeneration
# Herbalism Kit
5 Potion of Healing

# Weapons
Warhammer +1
```
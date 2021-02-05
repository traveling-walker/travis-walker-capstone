import xml.etree.ElementTree as ET
import csv
from os import path


def parse_xml():
    tree = ET.parse(path.join('.', 'data', 'artists.xml'))

    root = tree.getroot()

    artists = []

    for child in root.findall('./artist'):
        artist_id = int(child.find('id').text)

        member_list = []
        members = child.find('members')
        if members is not None:
            for member_id in members.findall('id'):
                member_list.append(int(member_id.text))

        group_list = []
        groups = child.find('groups')
        if groups is not None:
            for group_id in groups.findall('name'):
                group_list.append(int(group_id.get('id')))

        artists.append({
            'artist_id': artist_id,
            'member_list': member_list,
            'group_list': group_list
        })

    fields = ['artist_id', 'member_list', 'group_list']

    with open(path.join('.', 'data', 'artists.csv'), 'w+', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fields)
        writer.writeheader()
        writer.writerows(artists)

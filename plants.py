import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np


class PlantFinder:

    def __init__(self):
        self._categories = []
        self._spec_desc = []
        self._data = pd.DataFrame()
        self._all_colours = set()
        self.collect_info()
        self.find_colours()

    def collect_info(self):
        number_pages = 29
        plant_refs = []

        for cur_number in range(1, number_pages):
            url = f'http://www.pro-landshaft.ru/plants/catalog/{cur_number}/'
            soup = BeautifulSoup(requests.get(url).content, 'html.parser')
            for tag in soup.find_all('li', soup.body.strong.parent.parent.parent.ul)[3:][:-14]:
                plant_refs.append(tag.a['href'])

        url = f'http://www.pro-landshaft.ru/plants/catalog/1/'
        soup = BeautifulSoup(requests.get(url).content, 'html.parser')
        cat = soup.find_all('ul', soup.body.strong.parent.parent.parent)[1]
        self._categories = [tag.text.strip() for tag in soup.find_all('li', cat)[-14:]]

        photos = []
        common_desc = []
        plant_cat = []
        pages_refs = []

        for ref in plant_refs:
            url = f'http://www.pro-landshaft.ru{ref}'
            soup = BeautifulSoup(requests.get(url).content, 'html.parser')

            info = soup.body.find_all('p')
            cur_cat = [tag.text.strip() for tag in info[1].find_all('a')]

            first_type = 0
            cur_photo = ''
            while not info[first_type].text.startswith('Описание'):
                if info[first_type].img and not cur_photo:
                    cur_photo = 'http://www.pro-landshaft.ru{}'.format(info[first_type].img['src'])
                first_type += 1
                if first_type == len(info):
                    first_type = 5
                    break
            common_info = info[first_type].text.strip()[8:]
            first_type += 1
            if not common_info:
                common_info = info[first_type].text.strip()
            if info[first_type].img and not cur_photo:
                cur_photo = 'http://www.pro-landshaft.ru{}'.format(info[first_type].img['src'].replace(' ', '%20'))
                first_type += 1
            if not common_info:
                common_info = info[first_type].text.strip()

            for cur_type in range(first_type, len(info)):
                if info[first_type].img and not cur_photo:
                    cur_photo = 'http://www.pro-landshaft.ru{}'.format(info[first_type].img['src'].replace(' ', '%20'))
                if info[cur_type].strong:
                    if info[cur_type].font or not info[cur_type].text.strip():
                        break
                    plant_cat.append([int(cat in cur_cat) for cat in self._categories])
                    photos.append(cur_photo)
                    common_desc.append(common_info)
                    pages_refs.append(url)
                    self._spec_desc.append(info[cur_type].text.strip())

        names = [' '.join(string.split()[:2]).strip(',').strip(' –') for string in self._spec_desc]

        df1 = pd.DataFrame(
            {
                'Название': names,
                'Общее описание': common_desc,
                'Описание вида': self._spec_desc,
                'Фото': photos,
                'Ссылка на страницу': pages_refs
            }
        )
        df2 = pd.DataFrame(np.array(plant_cat), columns=self._categories)

        self._data = pd.concat([df1, df2], axis=1)

    def find_colours(self):
        url = 'https://colorscheme.ru/color-names.html'
        soup = BeautifulSoup(requests.get(url).content, 'html.parser')

        colours = set()
        for tag in soup.find_all('td'):
            if tag.text.strip():
                word = tag.text.strip().split()[-1]
                if 'а' < word[0] < 'я' or 'А' < word[0] < 'Я':
                    colours.add(word)

        colours = list(colours)
        for i in range(len(colours)):
            colours[i] = colours[i].lower()
            if '-' in colours[i]:
                colours[i] = colours[i][colours[i].rfind('-') + 1:]
            if colours[i].endswith('ый') or colours[i].endswith('ий'):
                self._all_colours.add(colours[i][:-2])

        colours_exist = [''] * len(self._spec_desc)
        for i in range(len(self._spec_desc)):
            string = self._spec_desc[i]
            for colour in self._all_colours:
                if colour in string:
                    colours_exist[i] += colour + ' '
        self._data = pd.concat([self._data, pd.DataFrame({'Цвета': colours_exist})], axis=1)

    @staticmethod
    def match_query(row, cur_types, cur_colour):
        for cur_type in cur_types:
            if not row[cur_type]:
                return False
        return cur_colour[:-2] in row['Цвета']

    def __call__(self, plant_types, plant_colour, plant_name):
        if plant_name:
            indexes = self._data.apply(lambda row: plant_name in row['Название'].lower(), axis=1)
        else:
            indexes = self._data.apply(lambda row: self.match_query(row, plant_types, plant_colour), axis=1)

        if indexes.empty:
            return None
        result = self._data[indexes].sample(1)
        return {
            "res_plant_name": result["Название"].values[0],
            "general_desc": result["Общее описание"].values[0],
            "spec_desc": result["Описание вида"].values[0],
            "photo_ref": result["Фото"].values[0],
            "page_ref": result["Ссылка на страницу"].values[0]
        }

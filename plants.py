import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np


class PlantFinder:

    def __init__(self):
        self._categories = []
        self._spec_desc = []
        self._data = pd.DataFrame()
        self._pests = pd.DataFrame()
        self._all_colours = set()
        self.collect_info()
        self.find_colours()
        self.get_pests()

    def collect_info(self):
        # отправимся на сайт http://www.pro-landshaft.ru/,
        # number_pages - количество первых букв в названиях, оно
        # же количество страниц в каталоге всех растений
        number_pages = 29
        plant_refs = []

        # здесь находим ссылки на страницы с каждым растением
        for cur_number in range(1, number_pages):
            url = f'http://www.pro-landshaft.ru/plants/catalog/{cur_number}/'
            soup = BeautifulSoup(requests.get(url).content, 'html.parser')
            for tag in soup.find_all('li', soup.body.strong.parent.parent.parent.ul)[3:][:-14]:
                plant_refs.append(tag.a['href'])

        # ищем категории - типы растений, по которым потом будет происходить поиск
        url = f'http://www.pro-landshaft.ru/plants/catalog/1/'
        soup = BeautifulSoup(requests.get(url).content, 'html.parser')
        cat = soup.find_all('ul', soup.body.strong.parent.parent.parent)[1]
        self._categories = [tag.text.strip() for tag in soup.find_all('li', cat)[-14:]]

        photos = []
        common_desc = []
        plant_cat = []
        pages_refs = []

        # теперь пройдёмся по всем страницам с растениями
        # о каждом будем знать его фотографию, короткое описание,
        # затем получим описание видов - более конкретное в дополнение
        # к первому, а также получим типы для данного растения
        for ref in plant_refs:
            url = f'http://www.pro-landshaft.ru{ref}'
            soup = BeautifulSoup(requests.get(url).content, 'html.parser')

            info = soup.body.find_all('p')
            cur_cat = [tag.text.strip() for tag in info[1].find_all('a')]

            # дальнейшнее связано со спецификой строения конкретного сайта,
            # информация структурированна не полностью, поэтому приходится
            # расставлять костыли в некоторых местах, преследуя цели, которые
            # были указаны перед большим циклом
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

            # поскольку на каждой странице растения содержится информация
            # о нескольких видах, то будем пополнять списки по ним
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

        # формируем список с названиями - их можно извлечь из
        # описания вида, рассмотрев его начало
        names = [' '.join(string.split()[:2]).strip(',').strip(' –') for string in self._spec_desc]

        # наконец формируем DataFrame, используя для каждого растения
        # отдельные именные колонки(df1), а затем добавляем к ним типы,
        # которые формируем отдельно(df2) и объединяем результаты
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
        # посетим в этот раз сайт https://colorscheme.ru/,
        # здесь мы получим всевозможные цвета, которые могут
        # встретиться в описании растений
        url = 'https://colorscheme.ru/color-names.html'
        soup = BeautifulSoup(requests.get(url).content, 'html.parser')

        # последующие манипуляции нужны для того, чтобы из сложных
        # двойных-тройных названий выделить одно слово, по типу
        # "красный", такие мы будем использовать в дальнейшем
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

        # наконец формируем список с найденными цветами в описании, можно
        # было бы непосредственно искать их каждый раз, но с целью оптимизации
        # константы перенесём их в отдельную колонку исходного DataFrame
        colours_exist = [''] * len(self._spec_desc)
        for i in range(len(self._spec_desc)):
            string = self._spec_desc[i]
            for colour in self._all_colours:
                if colour in string:
                    colours_exist[i] += colour + ' '
        self._data = pd.concat([self._data, pd.DataFrame({'Цвета': colours_exist})], axis=1)

    def get_pests(self):
        # теперь перейдём на сайт http://www.udec.ru/, на котором
        # я нашёл информацию о вредителях, её мы также поместим в
        # DataFrame, а затем будем определять тех, кто может питаться
        # конкретным растением
        photos = []
        links = []
        names = []
        info = []

        for j in range(1, 7):
            url = f'http://www.udec.ru/vrediteli/page/{j}'
            soup = BeautifulSoup(requests.get(url).content, 'html.parser')

            # здесь формируем список с информацией о каждом вредителе, некоторые будут
            # являться статьями без конкретики(без указания вида), их будем пропускать
            result = [child for child in soup.find('h1').parent.children][3].find_all('div')

            for k in range(0, len(result), 2):
                cur_pest = result[k]
                finded_tags = cur_pest.find_all('a')
                if len(finded_tags) < 2 or not self.check_pest(finded_tags[1].text):
                    continue
                if 'belyanka' in finded_tags[0]['href']:
                    continue
                photos.append(finded_tags[0].img['src'])
                links.append(finded_tags[0]['href'])
                names.append(finded_tags[1].text.strip())
                classes = BeautifulSoup(requests.get(links[-1]).content, 'html.parser').find_all('p')
                for i in range(len(classes)):
                    if self.check_obj(classes[i]) and not self.check_obj(classes[i + 1]):
                        all_info = ''
                        counter = i + 1
                        while counter < len(classes) and not \
                                ((not classes[counter].strong and classes[counter].text.strip().startswith('Меры')) or
                                 (classes[counter].strong and classes[counter].strong.text.strip().startswith('Меры'))):
                            all_info += classes[counter].text.strip()
                            counter += 1
                        info.append(all_info)
                        break
        self._pests = pd.DataFrame(
            {
                'Название': names,
                'Информация': info,
                'Фото': photos,
                'Ссылка на страницу': links
            }
        )

    def __call__(self, plant_types, plant_colour, plant_name):
        # наконец формируем метод __call__(), здесь сразу проверим,
        # указано ли название, тогда сразу осуществляем поиск(то есть
        # при указании названия остальное писать не нужно)
        # в противном случае ищем растения с выбранными типами - plant_types и
        # выбранным цветом - plant_colour
        plant_name = plant_name.lower()
        if plant_name:
            indexes = self._data.apply(lambda row: plant_name in row['Название'].lower(), axis=1)
        else:
            indexes = self._data.apply(lambda row: self.match_query(row, plant_types, plant_colour), axis=1)

        # обрабатываем случай, когда ничего не найдено
        if self._data[indexes].empty:
            return None

        result = self._data[indexes].sample(1)

        # формируем информацию о растении, которую будем выводить
        form_data = {
            "res_plant_name": result["Название"].values[0],
            "general_desc": result["Общее описание"].values[0],
            "spec_desc": result["Описание вида"].values[0],
            "photo_ref": result["Фото"].values[0],
            "page_ref": result["Ссылка на страницу"].values[0]
        }

        # далее будем искать вредителей, если ничего не нашлось -
        # передадим этот результат далее, иначе добавим в словарик
        # информацию о найденном вредителе
        name = result['Название'].values[0]
        key_word = name.split()[0][:-1].lower()
        indexes = self._pests.apply(lambda row: key_word in row['Информация'].lower(), axis=1)
        if not self._pests[indexes].empty:
            pest = self._pests[indexes].sample(1)
            form_data['pest_name'] = pest['Название'].values[0]
            form_data['pest_info'] = pest['Информация'].values[0]
            form_data['pest_photo'] = pest['Фото'].values[0]
            form_data['pest_link'] = pest['Ссылка на страницу'].values[0]
        else:
            form_data['pest_name'] = 'nothing'

        return form_data

    @staticmethod
    def check_pest(string):
        for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            if letter in string:
                return True
        return False

    @staticmethod
    def good_start(string):
        for start in ['Семья', 'Семейство', 'Ряд']:
            if string.startswith(start):
                return True
        return False

    def check_obj(self, obj):
        return (not obj.strong and self.good_start(obj.text.strip())) or \
               (obj.strong and self.good_start(obj.strong.text.strip()))

    @staticmethod
    def match_query(row, cur_types, cur_colour):
        for cur_type in cur_types:
            if not row[cur_type]:
                return False
        return cur_colour[:-2] in row['Цвета']


class RandomWeedInfo:

    def __init__(self):
        self._weeds = pd.DataFrame()
        self.get_weeds()

    @staticmethod
    def check_weed(string):
        for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            if letter in string:
                return True
        return False

    def get_weeds(self):
        # снова посетим http://www.udec.ru/, теперь нам нужны сорняки
        # поскольку явного соответствия между ними и растениями нет,
        # будем на каждый запрос присылать случайный сорняк, тем самым
        # добавляя немного познавательной информации в ответ на запрос
        photo = []
        link = []
        info = []
        name = []

        # здесь аналогично другим функциям, получаем информацию со
        # всех страниц, а затем отправляем её в DataFrame, из которого
        # и будем брать случайную строчку
        for k in range(1, 4):
            url = f'http://www.udec.ru/sornyaki/page/{k}'
            soup = BeautifulSoup(requests.get(url).content, 'html.parser')

            result = soup.body.find('h1').parent.div.find_all('div')

            for i in range(1, len(result), 2):
                found_tags = result[i].find_all('a')
                if len(found_tags) < 2 or not self.check_weed(found_tags[1].text):
                    continue
                photo.append(found_tags[0].img['src'])
                link.append(found_tags[0]['href'])
                name.append(found_tags[1].text.strip())
                classes = BeautifulSoup(requests.get(link[-1]).content, 'html.parser').find_all('p')[3:][:-1]
                all_info = ''
                for cur_class in classes:
                    all_info += cur_class.text.strip() + '\n'
                info.append(all_info)

        self._weeds = pd.DataFrame(
            {
                'Название': name,
                'Информация': info,
                'Фото': photo,
                'Ссылка на страницу': link
            }
        )

    def __call__(self):
        return self._weeds.sample(1)

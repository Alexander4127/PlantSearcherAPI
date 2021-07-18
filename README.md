# plant-searcher-app


Веб-приложение создано для поиска растений, которыми можно украсить свой сад.
Оно поддерживает запросы по названию растения, если таковое имеется, иначе поиск осуществляется по 
желаемым типам(можно выбрать любую комбинацию), а также по цвету(обычно речь идёт о цветках или листьях).

Приложение написано с использованием flask, для работы можно запустить main.py, затем, пользуясь 
http://localhost:5000/form, заполнить форму и увидеть результат на http://localhost:5000/data.

Данные взяты с сайта http://www.pro-landshaft.ru/, после чего создан DataFrame, в котором 
осуществляется поиск названий цветов(они взяты с https://colorscheme.ru).

Далее, если растение нашлось, осуществляется поиск по информации о вредителях с сайта http://www.udec.ru/,
тут мы будем искать тех, что потенциально опасны для найденного растения, если такой нашёлся - выводим 
информацию о нём.

Последней выводится информация о сорняках, взятая также с сайта http://www.udec.ru/, тут уже нет явной связи 
с выбранным растением, поэтому с целью расширения кругозора читателя выводим информацию о случайном из них.

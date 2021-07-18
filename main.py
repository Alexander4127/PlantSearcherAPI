from flask import Flask, render_template, request
from plants import PlantFinder, RandomWeedInfo


app = Flask(__name__)
plantFinderByParam = PlantFinder()
generatorWeed = RandomWeedInfo()


# здесь я повторяю пример с лекции
@app.route("/form")
def form():
    return render_template("form.html")


@app.route("/data", methods=["POST", "GET"])
def data():
    if request.method == "GET":
        return (
            f"Сначала проследуйте по пути /form для ввода данных"
        )
    if request.method == "POST":
        # получаем название или типы и цвет растения из запроса и
        # вызываем метод __call__()
        plant_name, plant_types, plant_colour = \
            request.form['plant_name'], request.form.getlist('plant_types'), request.form.get('plant_colour')

        form_data = plantFinderByParam(plant_types, plant_colour, plant_name)
        if form_data is None:
            return f"К сожалению, такое растение не найдено"

        # генерируем случайный сорняк, затем добавляем информацию
        # о нём в словарь
        weed = generatorWeed()
        form_data['weed_name'] = weed['Название'].values[0]
        form_data['weed_info'] = weed['Информация'].values[0]
        form_data['weed_photo'] = weed['Фото'].values[0]
        form_data['weed_link'] = weed['Ссылка на страницу'].values[0]

        return render_template("data.html", form_data=form_data)


if __name__ == "__main__":
    app.run(host="localhost", port=5000, debug=True)

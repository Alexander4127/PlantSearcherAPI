from flask import Flask, render_template, request
from plants import PlantFinder


app = Flask(__name__)
plantFinderByParam = PlantFinder()


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
        plant_name, plant_types, plant_colour = \
            request.form['plant_name'], request.form.getlist('plant_types'), request.form.get('plant_colour')

        form_data = plantFinderByParam(plant_types, plant_colour, plant_name)
        if form_data is None:
            return f"Подходящее растение не найдено"

        return render_template("data.html", form_data=form_data)


if __name__ == "__main__":
    app.run(host="localhost", port=5000, debug=True)

from flask import Flask, render_template, request
from plants import PlantFinder, RandomWeedInfo


app = Flask(__name__)
plantFinderByParam = PlantFinder()
generatorWeed = RandomWeedInfo()


@app.route("/form")
def form():
    return render_template("form.html")


@app.route("/data", methods=["POST", "GET"])
def data():
    if request.method == "GET":
        return (
            f"Please, choose the path /form"
        )
    if request.method == "POST":
        plant_name, plant_types, plant_colour = \
            request.form['plant_name'], request.form.getlist('plant_types'), request.form.get('plant_colour')

        form_data = plantFinderByParam(plant_types, plant_colour, plant_name)
        if form_data is None:
            return f"Plant has not found"

        weed = generatorWeed()
        form_data['weed_name'] = weed['Name'].values[0]
        form_data['weed_info'] = weed['Info'].values[0]
        form_data['weed_photo'] = weed['Photo'].values[0]
        form_data['weed_link'] = weed['Link'].values[0]

        return render_template("data.html", form_data=form_data)


if __name__ == "__main__":
    app.run(host="localhost", port=5000, debug=True)

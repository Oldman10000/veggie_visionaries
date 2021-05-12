import os
from flask import (
    Flask, flash, render_template,
    redirect, request, session, url_for)
from flask_pymongo import PyMongo
from flask_paginate import Pagination, get_page_args
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
import datetime
if os.path.exists("env.py"):
    import env


app = Flask(__name__)

app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.secret_key = os.environ.get("SECRET_KEY")

mongo = PyMongo(app)


# index page
@app.route("/")
@app.route("/index")
def index():
    if session.get("user"):
        user = mongo.db.users.find_one({"username": session["user"]})
    else:
        user = False

    return render_template("index.html", user=user)


# amount of items per page for pagination feature
PER_PAGE = 5


"""
    Pagination copied and adapted from
    https://gist.github.com/mozillazg/69fb40067ae6d80386e10e105e6803c9
"""


def paginated(recipes):
    page, per_page, offset = get_page_args(
        page_parameter='page', per_page_parameter='per_page')
    offset = page * PER_PAGE - PER_PAGE

    return recipes[offset: offset + PER_PAGE]


def pagination_args(recipes):
    page, per_page, offset = get_page_args(
        page_parameter='page', per_page_parameter='per_page')
    total = len(recipes)

    return Pagination(page=page,
                      per_page=PER_PAGE,
                      total=total,
                      css_framework="bootstrap4")


# general recipes page template
def show_recipes(recipes):
    recipes_paginated = paginated(recipes)
    pagination = pagination_args(recipes)

    # cycles through each recipe and updates average rating
    for recipe in recipes:
        recipe_id = recipe["_id"]
        if recipe["rating"]:
            recipe_avg = round(sum(recipe["rating"])/len(recipe["rating"]))
            mongo.db.recipes.update(
                {"_id": ObjectId(recipe_id)},
                {"$set": {"avgrating": recipe_avg}})
        else:
            mongo.db.recipes.update(
                {"_id": ObjectId(recipe_id)},
                {"$set": {"avgrating": "No Reviews Yet!"}})

    return render_template("recipes.html",
                           recipes=recipes_paginated,
                           pagination=pagination)


# shows all recipes
@app.route("/recipes")
def all_recipes():
    recipes = list(mongo.db.recipes.find().sort("_id", -1))
    return show_recipes(recipes)


# shows all recipes
@app.route("/older")
def older():
    recipes = list(mongo.db.recipes.find().sort("_id", 1))
    return show_recipes(recipes)


# allows user to search for recipe
@app.route("/search")
def search():
    query = request.form.get("query")
    recipes = list(mongo.db.recipes.find({"$text": {"$search": query}}))
    return show_recipes(recipes)


# sorts recipes alphabetically
@app.route("/recipes/a-z")
def a_z():
    recipes = list(mongo.db.recipes.find().sort("name"))
    return show_recipes(recipes)


# sorts recipes by rating
@app.route("/recipes/rating")
def rating():
    recipes = list(mongo.db.recipes.find().sort("avgrating", -1))
    return show_recipes(recipes)


# gets easy recipes
@app.route("/recipes/easy")
def easy():
    recipes = list(mongo.db.recipes.find({"difficulty": "easy"}))
    return show_recipes(recipes)


# gets medium recipes
@app.route("/recipes/medium")
def medium():
    recipes = list(mongo.db.recipes.find({"difficulty": "medium"}))
    return show_recipes(recipes)


# gets hard recipes
@app.route("/recipes/hard")
def hard():
    recipes = list(mongo.db.recipes.find({"difficulty": "hard"}))
    return show_recipes(recipes)


# allows user to delete review
@app.route("/delete_review/<review_id>/<recipe_id>")
def delete_review(review_id, recipe_id):
    # removes rating from recipe rating array
    # gets review
    review = mongo.db.reviews.find_one({"_id": ObjectId(review_id)})
    rating = review["rating"]
    # gets recipe
    recipe = mongo.db.recipes.find_one({"_id": ObjectId(recipe_id)})
    ratingArray = recipe["rating"]
    # removes one occurance of the rating from the ratings array
    ratingArray.remove(rating)
    # replaces old array with new array
    mongo.db.recipes.update_one({"_id": ObjectId(recipe_id)},
                                {"$set": {"rating": ratingArray}})

    # removes review from reviews collection
    mongo.db.reviews.remove({"_id": ObjectId(review_id)})

    return redirect(url_for("all_recipes"))


# gets specific recipe as selected by user
@app.route("/recipe/<recipe_id>", methods=["GET", "POST"])
def show_recipe(recipe_id):
    recipe = mongo.db.recipes.find_one({"_id": ObjectId(recipe_id)})
    # review submission
    if request.method == "POST":
        date = datetime.datetime.now()
        review = {
            "recipe": recipe_id,
            "rating": int(request.form.get("rating")),
            "review": request.form.get("review"),
            "created_by": session["user"],
            "date": date.strftime("%x"),
            "time": date.strftime("%X")
        }
        mongo.db.reviews.insert_one(review)

        # updates rating
        rating = int(request.form.get("rating"))
        mongo.db.recipes.update_one(recipe, {"$push": {"rating": rating}})
        return redirect(url_for("all_recipes"))

    reviews = mongo.db.reviews.find({"recipe": recipe_id})
    # gets average rating
    if recipe["rating"]:
        ratings = recipe["rating"]
        avg = round(sum(ratings)/len(ratings))
    else:
        avg = "No Reviews Yet!"

    # checks if this recipe has been favorited by the user
    if session.get("user"):
        user = mongo.db.users.find_one({"username": session["user"]})
        if user["favorite"]:
            for x in user["favorite"]:
                if x == recipe_id:
                    favorited = True
                    break
                else:
                    favorited = False
        else:
            favorited = False
    else:
        favorited = False

    return render_template(
        "recipe.html",
        recipe=recipe,
        reviews=reviews,
        avg=avg,
        favorited=favorited)


# Allows user to favorite a particular recipe
@app.route("/favorite/<recipe_id>")
def favorite(recipe_id):
    user = mongo.db.users.find_one({"username": session["user"]})
    mongo.db.users.update_one(user, {"$push": {"favorite": recipe_id}})
    return redirect(url_for("all_recipes"))


# allows user to remove recipe from favorites
@app.route("/remove_favorite/<recipe_id>")
def remove_favorite(recipe_id):
    user = mongo.db.users.find_one({"username": session["user"]})
    favoriteArray = user["favorite"]
    favoriteArray.remove(recipe_id)
    mongo.db.users.update_one({"username": session["user"]},
                              {"$set": {"favorite": favoriteArray}})
    return redirect(url_for("all_recipes"))


# allows user to add recipe
@app.route("/add_recipe", methods=["GET", "POST"])
def add_recipe():
    if request.method == "POST":
        date = datetime.datetime.now()
        recipe = {
            "name": request.form.get("rname"),
            "difficulty": request.form.get("difficulty"),
            "prep_time": request.form.get("prep_time"),
            "cook_time": request.form.get("cook_time"),
            "serves": request.form.get("serves"),
            "description": request.form.get("description"),
            "ingredients": request.form.getlist("ingredient"),
            "instructions": request.form.getlist("instruction"),
            "image": request.form.get("image_submit"),
            "created_by": session["user"],
            "date": date.strftime("%x"),
            "time": date.strftime("%X"),
            "rating": []
        }
        mongo.db.recipes.insert_one(recipe)
        flash("Recipe Successfully Added")
        return redirect(url_for("all_recipes"))

    return render_template("add_recipe.html")


# allows user to edit recipe
@app.route("/edit_recipe/<recipe_id>", methods=["GET", "POST"])
def edit_recipe(recipe_id):
    if request.method == "POST":
        edited = {
            "name": request.form.get("rname"),
            "difficulty": request.form.get("difficulty"),
            "prep_time": request.form.get("prep_time"),
            "cook_time": request.form.get("cook_time"),
            "serves": request.form.get("serves"),
            "description": request.form.get("description"),
            "ingredients": request.form.getlist("ingredient"),
            "image": request.form.get("image_submit"),
            "instructions": request.form.getlist("instruction"),
            "created_by": session["user"]
        }
        mongo.db.recipes.update({"_id": ObjectId(recipe_id)}, {"$set": edited})
        flash("Recipe Successfully Edited")
        return redirect(url_for("show_recipe", recipe_id=recipe_id))

    recipe = mongo.db.recipes.find_one({"_id": ObjectId(recipe_id)})
    return render_template("edit_recipe.html", recipe=recipe)


# allows user to delete recipe
@app.route("/delete_recipe/<recipe_id>")
def delete_recipe(recipe_id):
    mongo.db.recipes.remove({"_id": ObjectId(recipe_id)})
    flash("Recipe Deleted")
    return redirect(url_for("all_recipes"))


# allows user to register
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # if username exists in db
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username".lower())})

        if existing_user:
            flash("Username already exists")
            return redirect(url_for("register"))

        register = {
            "fname": request.form.get("fname").lower(),
            "lname": request.form.get("lname").lower(),
            "email": request.form.get("email").lower(),
            "username": request.form.get("username").lower(),
            "password": generate_password_hash(request.form.get("password")),
            "favorite": []
        }
        mongo.db.users.insert_one(register)

        # put user into 'session' cookie
        session["user"] = request.form.get("username").lower()
        flash("Registration Successful!")
        return redirect(url_for("loggedin", username=session["user"]))
    return render_template("register.html")


# allows user to login
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # check if username exists
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username".lower())})

        if existing_user:
            # ensure password is correct
            if check_password_hash(
                existing_user["password"], request.form.get("password")):
                    session["user"] = request.form.get("username").lower()
                    return redirect(url_for(
                        "loggedin", username=session["user"]))
            else:
                flash("Incorrect Username and/or Password")
                return redirect(url_for("login"))

        else:
            flash("Incorrect Username and/or Password")
            return redirect(url_for("login"))

    return render_template("login.html")


# redirects logged in user to homepage
@app.route("/index/<username>", methods=["GET", "POST"])
def loggedin(username):
    # grabs session users username
    username = mongo.db.users.find_one(
        {"username": session["user"]})["username"]
    user = mongo.db.users.find_one({"username": session["user"]})

    if session["user"]:
        return render_template("index.html", username=username, user=user)

    return redirect(url_for("login"))


# logs out user
@app.route("/logout")
def logout():
    # remove user from session cookies
    flash("Logged Out")
    session.pop("user")
    return redirect(url_for("login"))


# runs application
if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=True)

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

    allrecipes = list(mongo.db.recipes.find().sort("avgrating", -1))
    recipes = allrecipes[0:5]

    return render_template("index.html", user=user, recipes=recipes)


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
def show_recipes(recipes, current_sorting, cuisine, difficulty):
    recipes = list(recipes)
    cuisine = cuisine
    difficulty = difficulty
    recipes_paginated = paginated(recipes)
    pagination = pagination_args(recipes)

    return render_template("recipes.html",
                           recipes=recipes_paginated,
                           pagination=pagination,
                           cuisine=cuisine,
                           difficulty=difficulty,
                           current_sorting=current_sorting)


# shows user favorites
@app.route("/favorites")
def favorites():
    if session.get("user"):
        user = mongo.db.users.find_one({"username": session["user"]})
    else:
        user = False
    return render_template("favorites.html", user=user)


# allows user to search for recipe
@app.route("/search",  methods=["GET", "POST"])
def search():
    query = request.form.get("query")
    recipes = mongo.db.recipes.find({"$text": {"$search": query}})
    cuisine = "all"
    difficulty = "all"
    sort = request.args.get("sort", None)
    if sort:
        sorter(recipes, sort)
        current_sorting = sort
    else:
        current_sorting = "Newer"
    return show_recipes(recipes, current_sorting, cuisine, difficulty)


# sorts recipes in particular orders
def sorter(recipes, sort):
    # sorts alphabetically
    if sort == "A-Z":
        recipes.sort("name")
        return recipes
    # sorts by newest added
    elif sort == "Newer":
        recipes.sort("_id", -1)
        return recipes
    # sorts by rating
    elif sort == "Rating":
        recipes.sort("avgrating", -1)
        return recipes
    # sorts by oldest
    elif sort == "Older":
        recipes.sort("_id", 1)
        return recipes
    else:
        return False


# gets all recipes
@app.route("/recipes")
def allRecipes():
    recipes = mongo.db.recipes.find().sort("_id", -1)
    cuisine = "all"
    difficulty = "all"

    sort = request.args.get("sort", None)

    if sort:
        sorter(recipes, sort)
        current_sorting = sort
    else:
        recipes.sort("_id", -1)
        current_sorting = "Newer"

    return show_recipes(recipes, current_sorting, cuisine, difficulty)


# gets filtered recipes
@app.route("/recipes/<cuisine>/<difficulty>")
def findRecipe(cuisine, difficulty):

    print(cuisine)
    print(difficulty)

    if cuisine == 'all':
        if difficulty == 'easy':
            recipes = mongo.db.recipes.find(
                {"difficulty": "easy"}).sort("_id", -1)
        elif difficulty == 'medium':
            recipes = mongo.db.recipes.find(
                {"difficulty": "medium"}).sort("_id", -1)
        elif difficulty == 'hard':
            recipes = mongo.db.recipes.find(
                {"difficulty": "hard"}).sort("_id", -1)
        elif difficulty == 'all':
            recipes = mongo.db.recipes.find().sort("_id", -1)
        else:
            return redirect(url_for('allRecipes'))

    else:
        if difficulty == 'easy':
            recipes = mongo.db.recipes.find(
                {"difficulty": "easy", "cuisine": cuisine}).sort("_id", -1)
        elif difficulty == 'medium':
            recipes = mongo.db.recipes.find(
                {"difficulty": "medium", "cuisine": cuisine}).sort("_id", -1)
        elif difficulty == 'hard':
            recipes = mongo.db.recipes.find(
                {"difficulty": "hard", "cuisine": cuisine}).sort("_id", -1)
        elif difficulty == 'all':
            recipes = mongo.db.recipes.find(
                {"cuisine": cuisine}).sort("_id", -1)
        else:
            return redirect(url_for('allRecipes'))

    sort = request.args.get("sort", None)

    if sort:
        sorter(recipes, sort)
        current_sorting = sort
    else:
        recipes.sort("_id", -1)
        current_sorting = "Newer"

    return show_recipes(recipes, current_sorting, cuisine, difficulty)


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

    return redirect(url_for("show_recipe", recipe_id=recipe_id))


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
        return redirect(url_for("show_recipe", recipe_id=recipe_id))

    reviews = mongo.db.reviews.find({"recipe": recipe_id})
    # gets average rating
    if recipe["rating"]:
        ratings = recipe["rating"]
        avg = round(sum(ratings)/len(ratings))
        mongo.db.recipes.update(
                {"_id": ObjectId(recipe_id)},
                {"$set": {"avgrating": avg}})
    else:
        avg = "No Reviews Yet!"

    # checks if this recipe has been favorited by the user
    if session.get("user"):
        user = mongo.db.users.find_one({"username": session["user"]})
        if user["favorite"]:
            for item in user["favorite"]:
                if item["_id"] == ObjectId(recipe_id):
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
    # gets session user
    user = mongo.db.users.find_one({"username": session["user"]})
    # gets current recipe
    recipe = mongo.db.recipes.find_one({"_id": ObjectId(recipe_id)})
    # pushes current recipe to session user's favorites
    mongo.db.users.update_one(user, {"$push": {"favorite": recipe}})
    flash("Recipe Added to Favourites")
    return redirect(url_for("favorites"))


# allows user to remove recipe from favorites
@app.route("/remove_favorite/<recipe_id>")
def remove_favorite(recipe_id):
    # gets session user
    user = mongo.db.users.find_one({"username": session["user"]})
    # gets current recipe
    recipe = mongo.db.recipes.find_one({"_id": ObjectId(recipe_id)})
    # gets recipe id
    recipeId = recipe["_id"]
    # gets array of user favorites and creates list
    favoriteArray = user["favorite"]
    # iterates through user favorites to find matching recipe id and assigns
    # this to recipe variable
    for favorite in favoriteArray:
        if favorite["_id"] == recipeId:
            recipe = favorite
    # removes unfavorited recipe from local list
    favoriteArray.remove(recipe)
    # updates mongo db array with new local list
    mongo.db.users.update_one({"username": session["user"]},
                              {"$set": {"favorite": favoriteArray}})
    flash("Recipe Removed from Favourites")
    return redirect(url_for("favorites"))


# allows user to add recipe
@app.route("/add_recipe", methods=["GET", "POST"])
def add_recipe():
    if request.method == "POST":
        date = datetime.datetime.now()
        recipe = {
            "name": request.form.get("rname"),
            "cuisine": request.form.get("cuisine").lower(),
            "difficulty": request.form.get("difficulty").lower(),
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
        return redirect(url_for("allRecipes"))

    return render_template("add_recipe.html")


# allows user to edit recipe
@app.route("/edit_recipe/<recipe_id>", methods=["GET", "POST"])
def edit_recipe(recipe_id):
    if request.method == "POST":
        edited = {
            "name": request.form.get("rname"),
            "difficulty": request.form.get("difficulty").lower(),
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
    # gets recipe
    recipe = mongo.db.recipes.find_one({"_id": ObjectId(recipe_id)})
    # gets recipe creator
    created_by = recipe["created_by"]
    # gets session user
    if session.get("user"):
        user = mongo.db.users.find_one({"username": session["user"]})
        # checks if session user is the creator (or admin account)
        if user["username"] == created_by or user["username"] == "admin":
            # deletes all instances of recipe in user favorites
            mongo.db.users.update(
                {},
                {"$pull": {"favorite": {"_id": ObjectId(recipe_id)}}},
                upsert=False,
                multi=True)
            # deletes recipe
            mongo.db.recipes.delete_one(recipe)
            flash("Recipe Deleted")
        # if no session user or incorrect user
        else:
            flash("Only the recipe creator is allowed to delete this recipe")
    else:
        flash("Only the recipe creator is allowed to delete this recipe")

    return redirect(url_for("allRecipes"))


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
            {
                "$or": [
                    {"username": request.form.get("username".lower())},
                    {"email": request.form.get("username".lower())}
                ]
            }
        )
        if existing_user:
            # ensure password is correct
            if check_password_hash(
                existing_user["password"], request.form.get("password")):
                    session["user"] = existing_user["username"]
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

    allrecipes = list(mongo.db.recipes.find().sort("avgrating", -1))
    recipes = allrecipes[0:5]

    if session["user"]:
        return render_template(
            "index.html", username=username, user=user, recipes=recipes)

    return redirect(url_for("login"))


# logs out user
@app.route("/logout")
def logout():
    # remove user from session cookies
    flash("Logged Out")
    session.pop("user")
    return redirect(url_for("login"))


# shows all cuisines
@app.route("/cuisines")
def all_cuisines():
    cuisines = list(mongo.db.cuisines.find().sort("_id", -1))
    return render_template("cuisines.html", cuisines=cuisines)


# allows adding a cuisine
@app.route("/add_cuisine", methods=["GET", "POST"])
def add_cuisine():
    if request.method == "POST":
        mongo.db.cuisines.insert_one(
            {"name": request.form.get("addcuisine").lower()})
        flash("Cuisine Successfully Added")
        return redirect(url_for("all_cuisines"))
    return render_template("add_cuisine.html")


# runs application
if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=True)

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
    """
    This function returns the main website homepage
    It needs to check if there is a user 'logged in'
    It also checks for the top rated recipes to display the top 5
    """
    # checks if there is a user saved in session
    if session.get("user"):
        user = mongo.db.users.find_one({"username": session["user"]})
    else:
        user = False

    # gets list of all recipes to display top 5 rated on homepage
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
    """
    This function compiles all the necessary information
    to render the recipes template
    It gets the recipes cursor and converts this
    to a list so it can be rendered
    It gets the currently selected cuisine
    It gets the currently selected difficulty
    It paginates the recipes
    It gets the pagination args for the recipes
    It gets all of the cuisines from the database
    """
    recipes = list(recipes)
    cuisine = cuisine
    difficulty = difficulty
    recipes_paginated = paginated(recipes)
    pagination = pagination_args(recipes)
    cuisines = list(mongo.db.cuisines.find().sort("name"))

    return render_template("recipes.html",
                           recipes=recipes_paginated,
                           pagination=pagination,
                           cuisine=cuisine,
                           difficulty=difficulty,
                           current_sorting=current_sorting,
                           cuisines=cuisines)


# shows user favorites
@app.route("/favorites")
def favorites():
    """
    This function checks if there is a user logged in
    and finds their favourited recipes to render to the template
    """
    if session.get("user"):
        user = mongo.db.users.find_one({"username": session["user"]})
    else:
        user = False
    return render_template("favorites.html", user=user)


# allows user to search for recipe
@app.route("/search",  methods=["GET", "POST"])
def search():
    """
    This function allows a user to search for a recipe
    It creates a query from the search input and searches
    the index for any matching items
    """
    # gets search query input
    query = request.form.get("query")
    # finds any info in recipes collection that matches the search query
    recipes = list(mongo.db.recipes.find({"$text": {"$search": query}}))
    recipes_paginated = paginated(recipes)
    pagination = pagination_args(recipes)
    return render_template("searchresults.html",
                           recipes=recipes_paginated,
                           pagination=pagination,
                           query=query)


# sorts recipes in particular orders
def sorter(recipes, sort):
    """
    This function takes the value from the recipe sort selector
    and returns the respective value
    """
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
    """
    This function finds all of the recipes on the database
    and automatically sorts by newest first
    """
    # all recipes
    recipes = mongo.db.recipes.find().sort("_id", -1)
    # default cusine is all
    cuisine = "all"
    # default difficulty is all
    difficulty = "all"
    # allows user to sort
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
    """
    This function returns filtered recipes depending on user selection
    """
    # first checks value of 'cuisine' from the url
    # if cuisine is all
    if cuisine == 'all':
        # display all easy recipes
        if difficulty == 'easy':
            recipes = mongo.db.recipes.find(
                {"difficulty": "easy"}).sort("_id", -1)
        # display all medium recipes
        elif difficulty == 'medium':
            recipes = mongo.db.recipes.find(
                {"difficulty": "medium"}).sort("_id", -1)
        # display all hard recipes
        elif difficulty == 'hard':
            recipes = mongo.db.recipes.find(
                {"difficulty": "hard"}).sort("_id", -1)
        # display all recipes
        elif difficulty == 'all':
            recipes = mongo.db.recipes.find().sort("_id", -1)
        # if user enters another value in url then return to all recipes
        else:
            flash("No such difficulty exists")
            return redirect(url_for('allRecipes'))

    # if cuisine is 'other'
    elif cuisine == 'other':
        # display all easy recipes + other
        if difficulty == 'easy':
            recipes = mongo.db.recipes.find(
                {"difficulty": "easy", "cuisine": "other"}).sort("_id", -1)
        # display all medium recipes + other
        elif difficulty == 'medium':
            recipes = mongo.db.recipes.find(
                {"difficulty": "medium", "cuisine": "other"}).sort("_id", -1)
        # display all hard recipes + other
        elif difficulty == 'hard':
            recipes = mongo.db.recipes.find(
                {"difficulty": "hard", "cuisine": "other"}).sort("_id", -1)
        # display all recipes + other
        elif difficulty == 'all':
            recipes = mongo.db.recipes.find(
                {"cuisine": "other"}).sort("_id", -1)
        # in case user enters another value in url then return to all recipes
        else:
            flash("No such difficulty exists")
            return redirect(url_for('allRecipes'))

    # if cuisine is included in database
    elif mongo.db.cuisines.find({"name": cuisine}).count():
        # display all easy recipes + cuisine
        if difficulty == 'easy':
            recipes = mongo.db.recipes.find(
                {"difficulty": "easy", "cuisine": cuisine}).sort("_id", -1)
        # display all medium recipes + cuisine
        elif difficulty == 'medium':
            recipes = mongo.db.recipes.find(
                {"difficulty": "medium", "cuisine": cuisine}).sort("_id", -1)
        # display all hard recipes + cuisine
        elif difficulty == 'hard':
            recipes = mongo.db.recipes.find(
                {"difficulty": "hard", "cuisine": cuisine}).sort("_id", -1)
        # display all recipes + cuisine
        elif difficulty == 'all':
            recipes = mongo.db.recipes.find(
                {"cuisine": cuisine}).sort("_id", -1)
        # in case user enters another value in url then return to all recipes
        else:
            flash("No such difficulty exists")
            return redirect(url_for('allRecipes'))
    # in case user enters another value in url then return to all recipes
    else:
        flash("This cuisine does not exist on our database")
        return redirect(url_for('allRecipes'))

    # allows user to sort
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
    """
    This function allows a user to delete their review
    It needs to find and delete the review
    The rating needs to also be deleted from the ratings array
    from the relevant recipe in order to correctly calculate the average
    """
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
    """
    This function displays the full recipe information
    This includes all the recipe data itself as well as all the reviews
    The post method allows a user to post a review if they are logged in
    The post input is hidden to users if they are not logged in
    """
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

        # gets rating from form input
        rating = int(request.form.get("rating"))
        # updates recipe document with the rating
        mongo.db.recipes.update_one(recipe, {"$push": {"rating": rating}})
        return redirect(url_for("show_recipe", recipe_id=recipe_id))

    # gets recipe reviews
    reviews = mongo.db.reviews.find({"recipe": recipe_id})
    # gets average rating from reviews
    if recipe["rating"]:
        ratings = recipe["rating"]
        # creates recipe average
        avg = round(sum(ratings)/len(ratings))
        mongo.db.recipes.update(
                {"_id": ObjectId(recipe_id)},
                {"$set": {"avgrating": avg}})
    # if no reviews for this recipe
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
    """
    This function allows a user to favourite a recipe if
    they are currently logged in
    """
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
    """
    This function allows a user to remove a recipe from
    their favourites if they are logged in
    """
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
    """
    This function allows a user to add a recipe
    The post method includes all of the necessary recipe information
    Validation is on the html form
    """
    cuisines = list(mongo.db.cuisines.find().sort("name"))
    if request.method == "POST":
        date = datetime.datetime.now()
        recipe = {
            "name": request.form.get("rname"),
            "cuisine": request.form.get("cuisine").lower(),
            "difficulty": request.form.get("difficulty").lower(),
            "prep_time": int(request.form.get("prep_time")),
            "cook_time": int(request.form.get("cook_time")),
            "serves": int(request.form.get("serves")),
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

    return render_template("add_recipe.html", cuisines=cuisines)


# allows user to edit recipe
@app.route("/edit_recipe/<recipe_id>", methods=["GET", "POST"])
def edit_recipe(recipe_id):
    """
    This function allows a user to edit a review they have created
    The form data is pulled from the database to pre fill in the inputs
    """
    cuisines = list(mongo.db.cuisines.find().sort("name"))
    if request.method == "POST":
        edited = {
            "name": request.form.get("rname"),
            "difficulty": request.form.get("difficulty").lower(),
            "prep_time": int(request.form.get("prep_time")),
            "cook_time": int(request.form.get("cook_time")),
            "serves": int(request.form.get("serves")),
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
    return render_template(
        "edit_recipe.html", recipe=recipe, cuisines=cuisines)


# allows user to delete recipe
@app.route("/delete_recipe/<recipe_id>")
def delete_recipe(recipe_id):
    """
    This function allows a user to delete a recipe they have created
    This also allows an admin user to delete a recipe
    """
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
            # deletes all associated reviews
            mongo.db.reviews.delete_many(
                {"recipe": recipe_id}
            )
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
    """
    This function allows a user to register an account
    The post method adds user data to the database
    The user is then automatically added to the session cookie
    and redirected to the home page
    """
    if request.method == "POST":
        # if username exists in db
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username".lower())})

        if existing_user:
            flash("Username already exists")
            return redirect(url_for("register"))
        # gets form input data and updates db accordingly
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
    """
    This function allows a user to log in using an existing account
    Validation exists on the html form and also using Javascript
    """
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
@app.route("/<username>", methods=["GET", "POST"])
def loggedin(username):
    """
    This function redirects a logged in user to the homepage
    and renders the top 5 recipes to display
    """
    # grabs session users username
    username = mongo.db.users.find_one(
        {"username": session["user"]})["username"]
    user = mongo.db.users.find_one({"username": session["user"]})
    # gets top 5 rated recipes to display on homepage
    allrecipes = list(mongo.db.recipes.find().sort("avgrating", -1))
    recipes = allrecipes[0:5]

    if session["user"]:
        return render_template(
            "index.html", username=username, user=user, recipes=recipes)

    return redirect(url_for("login"))


# logs out user
@app.route("/logout")
def logout():
    """
    This function allows a user to log out and removes them from
    the session cookie
    """
    # remove user from session cookies
    flash("Logged Out")
    session.pop("user")
    return redirect(url_for("login"))


# shows all cuisines and allows admin to add cuisines
@app.route("/cuisines", methods=["GET", "POST"])
def all_cuisines():
    """
    This function displays all cuisines from the database
    The post method allows admin to add more cuisines to the database
    The add form is made to be only visible to admin account using
    Jinja template language on the html page
    """
    # gets all cuisines
    cuisines = list(mongo.db.cuisines.find().sort("name"))
    if request.method == "POST":
        # gets form input data and updates db accordingly
        cuisine = {
            "name": request.form.get("addcuisine").lower(),
            "image": request.form.get("cuisine_image")
        }
        mongo.db.cuisines.insert_one(cuisine)

        flash("Cuisine Successfully Added")
        return redirect(url_for("all_cuisines"))

    return render_template("cuisines.html", cuisines=cuisines)


# allows admin to delete a cuisine
@app.route("/delete_cuisine/<cuisine_id>")
def delete_cuisine(cuisine_id):
    """
    This function allows admin to delete a cuisine
    It also sets all recipes of the deleted cuisine to 'other' cuisine instead
    """
    # gets cuisine
    cuisine = mongo.db.cuisines.find_one({"_id": ObjectId(cuisine_id)})
    # if any recipes have been set with this cuisine,
    # this default to "cuisine": "other"
    mongo.db.recipes.update(
        {"cuisine": cuisine["name"]}, {"$set": {"cuisine": "other"}})
    # deletes cuisine
    mongo.db.cuisines.delete_one(cuisine)
    flash("Cuisine Deleted")
    return redirect(url_for("all_cuisines"))


# for nonexistent urls allows user to safely return home
@app.errorhandler(404)
def not_found(e):
    """
    For an invalid url this allows user to safely return home
    """
    return render_template('404.html')


# runs application
if __name__ == "__main__":
    """
    Runs app
    """
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=os.environ.get("DEBUG"))

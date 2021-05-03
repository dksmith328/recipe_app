from flask import Flask, redirect, url_for, render_template, request, session, flash
from datetime import timedelta
from flaskext.mysql import MySQL
from passlib.hash import sha256_crypt
from dotenv import load_dotenv
import os
import re 
import requests

load_dotenv()
mysql = MySQL()
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

app.config['MYSQL_DATABASE_USER'] = os.getenv('MYSQL_DATABASE_USER')
app.config['MYSQL_DATABASE_PASSWORD'] = os.getenv('MYSQL_DATABASE_PASSWORD')
app.config['MYSQL_DATABASE_DB'] = os.getenv('MYSQL_DATABASE_DB')
app.config['MYSQL_DATABASE_HOST'] = os.getenv('MYSQL_DATABASE_HOST')
database = os.getenv('MYSQL_DATABASE_DB')
print(database)
mysql.init_app(app)

app.permanent_session_lifetime = timedelta(minutes=60)

# bring user to the home page 
@app.route('/')
def home():
    return render_template('index.html')

##### REGISTRATION PAGE #####

# bring user to the registration page 
@app.route('/showRegister')
def showRegister():
    return render_template('register.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    # Output message if there is an error 
    msg = ''
    try:
        # assign variables to info returned from the form 
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        password2 = request.form['password2']

        # assign variables to ensure password is without errors
        # password requires a length 8 or greater with complexity 
        length_error = len(password) < 8 
        digit_error = re.search(r"\d", password) is None 
        upper_error = re.search(r"[A-Z]", password) is None 
        symbol_error = re.search(r"[ !#$%&'()*+,-./[\\\]^_`{|}~"+r'"]', password) is None
        password_error = not (length_error or digit_error or upper_error or symbol_error)

        # if the length is between 8 and 15 characters 
        if len(username) > 7 and len(username) < 16:
            # if there are no errors in the password 
            if password_error: 
                # if both password entries match 
                if password == password2:
                    # if the user completed the form 
                    if username and email and password:
                        # create the connection to the database 
                        conn = mysql.connect()
                        cursor = conn.cursor()
                        #_hashed_password = generate_password_hash(password)
                        # this encrypts the password
                        cursor.callproc('sp_create_user',(username, email, sha256_crypt.encrypt(password)))
                        # assign data variable 
                        data = cursor.fetchall()

                        # if this is not 0, this username is already assigned 
                        if len(data) == 0:
                            conn.commit()
                            msg = 'You have successfully registered! Please login.'
                        else:
                            msg = 'Username already taken. Please try again.'
                # the password entries don't match             
                else:
                    msg = 'Passwords must match.'
                    return render_template('register.html', msg=msg)
            # the password does not match the requirements 
            else: 
                msg = 'Password must be 8 characters or more and contain an uppercase letter, a number, and a special character.'
        # the username does not match the requirements 
        else:
            msg = 'Username must be between 8 and 15 characters. Please re-register.'
    # registration is successful 
    finally:
        return render_template('register.html', msg=msg)


##### LOGIN PAGE #####

@app.route('/login', methods=['GET', 'POST'])
def login():
    msg=''
     # Check if "username" and "password" POST requests exist in user submitted form
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:

        # assign variables to info returned from form 
        username = request.form['username']
        password = request.form['password']

        # create the SQL connection 
        conn = mysql.connect()
        cursor = conn.cursor()

        # SQL query that checks for the username in the database 
        cursor.execute('SELECT * FROM users WHERE username = %s', (username))

        # if something is returned 
        if cursor is not None:
            # get the first match  
            existing_user = cursor.fetchone()

            try:
                # fetch the hashed password from the database (index 2)
                hashed = existing_user[2]
            except Exception:
                return render_template('login.html', msg='User not found. Please Register.')

            # If user exists in user table in database
            if existing_user and sha256_crypt.verify(password, hashed):
                # Create session data, we can access this data in other routes
                session['loggedin'] = True
                # assign the database entry ID to track for recipe submission 
                session['id'] = existing_user[0]
                # assign the database entry username to track for profile greeting 
                session['username'] = existing_user[1]
                username=session['username']

                # create SQL connection 
                conn = mysql.connect()
                cursor = conn.cursor()
                #_hashed_password = generate_password_hash(password)
                cursor.execute(f'SELECT * FROM {database}.recipes WHERE username = %s', (username))
                data = cursor.fetchall()

                return render_template('profile.html', username=session['username'].capitalize(), data=data)
            else:
                # Account doesnt exist or username/password incorrect
                return render_template('login.html', msg='Incorrect username/password!')
    return render_template("login.html", msg='')


@app.route('/logout')
def logout():
    # Remove session data, this will log the user out
   session.pop('loggedin', None)
   session.pop('id', None)
   session.pop('username', None)
   # Redirect to login page
   return redirect(url_for('login'))


##### FORGOT PASSWORD PAGE #####

@app.route('/show_forgot_password')
def show_forgot_password():
    return render_template('forgot_password.html')

@app.route('/forgot_password', methods=['POST'])
def forgot_password():
    return render_template('forgot_password')


##### PROFILE PAGE #####

@app.route('/profile', methods=['GET'])
def profile():
    msg=''
    # Check if user is loggedin
    if 'loggedin' in session:
        # User is loggedin create session variables 
        username=session['username']
        conn = mysql.connect()
        cursor = conn.cursor()
        #_hashed_password = generate_password_hash(password)
        cursor.execute(f'SELECT * FROM {database}.recipes WHERE username = %s', (username))
        data = cursor.fetchall()

        #bring user to their Profile page 
        return render_template('profile.html', username=session['username'].capitalize(), data=data)
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))

##### RECIPE SORTING #####

@app.route('/profile', methods=['POST'])
def sorting():
    # store the sorting request from the dropdown on page 
    sort = request.form.get("recipe-sort")

    # this is sorted based on the order the user enters recipes 
    if sort == "Default":
        username=session['username']
        conn = mysql.connect()
        cursor = conn.cursor()
        cursor.execute(f'SELECT * FROM {database}.recipes WHERE username = %s', (username))
        data = cursor.fetchall()

    # this is sorted alphabetically 
    if sort == "Alphabetical":
        username=session['username']
        conn = mysql.connect()
        cursor = conn.cursor()
        # SQL query using ORDER BY to sort alphabetically
        cursor.execute(f'SELECT * FROM {database}.recipes WHERE username = %s ORDER BY recipe_name', (username))
        data = cursor.fetchall()

    # this is sorted by Quisine 
    if sort == "Categorized":
        username=session['username']
        conn = mysql.connect()
        cursor = conn.cursor()
        # SQL query using ORDER BY to sort by quisine category 
        cursor.execute(f'SELECT * FROM {database}.recipes WHERE username = %s ORDER BY cuisine_category', (username))
        data = cursor.fetchall()

    return render_template('profile.html', username=session['username'].capitalize(), data=data)

##### ADD A NEW RECIPE #####

@app.route('/show_add_recipe')
def show_add_recipe():
    return render_template('add_recipe.html', username=session['username'].capitalize())

@app.route('/add_recipe', methods=['GET', 'POST'])
def add_recipe():
    msg=''
    # Check if "username" and "password" POST requests exist in user submitted form
    if request.method == 'POST' and 'cuisine_category' in request.form and 'recipe_name' in request.form and 'recipe_intro_text' in request.form and 'prep_time' in request.form and 'cook_time' in request.form and 'ingredients' in request.form and 'how_to_make' in request.form and 'image_url' in request.form:
        
        # assign variable to info returned from form 
        username = session['username']
        cuisine_category = request.form['cuisine_category']
        recipe_name = request.form['recipe_name']
        recipe_intro_text = request.form['recipe_intro_text']
        prep_time = request.form['prep_time']
        cook_time = request.form['cook_time']
        ingredients = request.form['ingredients']
        how_to_make = request.form['how_to_make']
        image_url = request.form['image_url']

        # if a user does not enter an image url --- here are some defaults 
        if cuisine_category == "Soups":
            image_url = "https://images.pexels.com/photos/539451/pexels-photo-539451.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=750&w=1260"
        elif image_url == "" and cuisine_category == "Appetizers":
            image_url = "https://images.pexels.com/photos/41967/appetizer-canape-canapes-cheese-41967.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=750&w=1260"
        elif image_url == "" and cuisine_category == "Salads":
            image_url = "https://images.pexels.com/photos/257816/pexels-photo-257816.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=750&w=1260"
        elif image_url == "" and cuisine_category == "Main-dishes":
            image_url = "https://images.pexels.com/photos/3791089/pexels-photo-3791089.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=750&w=1260"
        elif image_url == "" and cuisine_category == "Dessert":
            image_url = "https://images.pexels.com/photos/1028714/pexels-photo-1028714.jpeg?auto=compress&cs=tinysrgb&dpr=1&w=500"
        elif image_url == "" and cuisine_category == "Vegetarian":
            image_url = "https://images.pexels.com/photos/2347311/pexels-photo-2347311.jpeg?auto=compress&cs=tinysrgb&dpr=3&h=750&w=1260"
        elif image_url == "" and cuisine_category == "Other":
            image_url = "https://images.pexels.com/photos/3026806/pexels-photo-3026806.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=750&w=1260"
        elif image_url == "" and cuisine_category == "Breakfast":
            image_url = "https://images.pexels.com/photos/103124/pexels-photo-103124.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=750&w=1260"
        elif image_url == "" and cuisine_category == "Lunch":
            image_url = "https://images.pexels.com/photos/326278/pexels-photo-326278.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=750&w=1260"

        # create a SQL connection 
        conn = mysql.connect()
        cursor = conn.cursor()
        # insert the data from the form into the database 
        cursor.execute('INSERT INTO recipes(username, recipe_name, recipe_intro_text, prep_time, cook_time, ingredients, how_to_make, image_url, cuisine_category) VALUES( %s, %s, %s, %s, %s, %s, %s, %s, %s)', (username, recipe_name, recipe_intro_text, prep_time, cook_time, ingredients, how_to_make, image_url, cuisine_category))
        conn.commit()
        # get all of the user's recipes 
        cursor.execute(f'SELECT * FROM {database}.recipes WHERE username = %s', (username))
        data = cursor.fetchall()

        # return to profile page with the success message 
        return render_template("profile.html", username=session['username'].capitalize(), msg='Successfully added recipe!', data=data)

    return render_template("add_recipe.html", username=session['username'].capitalize(), msg='Recipe not added.')

##### SHOW RECIPE ##### 

# looks up a recipe and shows using its ID 
@app.route('/recipe_single/<id>')
def recipe_single(id):
    # create SQL connection 
    conn = mysql.connect()
    cursor = conn.cursor()

    # SQL query searching for the recipe ID 
    cursor.execute(f'SELECT * FROM {database}.recipes WHERE id= %s' , (id))
    page = cursor.fetchall()

    # show the single recipe page 
    return render_template("recipepage.html", page=page)


##### DELETE RECIPE #####

@app.route('/delete_recipe/<id>')
def delete_recipe(id):
    conn = mysql.connect()
    cursor = conn.cursor()
    # delete query by the recipe ID 
    cursor.execute('DELETE FROM recipes WHERE id= %s' , (id))
    conn.commit()

    username=session['username']
    conn = mysql.connect()
    cursor = conn.cursor()
    # get all of the user's recipes 
    cursor.execute(f'SELECT * FROM {database}.recipes WHERE username = %s', (username))
    data = cursor.fetchall()

    # show the user's profile page 
    return render_template('profile.html', username=session['username'].capitalize(), data=data)


##### EDIT RECIPE #####

@app.route('/edit_recipe/<id>')
def edit_recipe(id):
    msg=''

    conn = mysql.connect()
    cursor = conn.cursor()
    cursor.execute(f'SELECT * FROM {database}.recipes WHERE id= %s' , (id))
    page = cursor.fetchall()

    return render_template("edit_recipe.html", username=session['username'].capitalize(), page=page)

@app.route('/update_recipe/<id>', methods=['POST'])
def update_recipe(id):
    # assign variables to the data returned from the form 
    username = session['username']
    recipe_name = request.form['recipe_name']
    recipe_intro_text = request.form['recipe_intro_text']
    prep_time = request.form['prep_time']
    cook_time = request.form['cook_time']
    ingredients = request.form['ingredients']
    how_to_make = request.form['how_to_make']
    image_url = request.form['image_url']

    # create SQL connection 
    conn = mysql.connect()
    cursor = conn.cursor()
    # SQL query to UPDATE the data according to the editions 
    cursor.execute("UPDATE recipes SET recipe_name = '%s', recipe_intro_text = '%s', prep_time = '%s', cook_time = '%s', ingredients = '%s', how_to_make = '%s', image_url = '%s'  WHERE id = '%s'" % (recipe_name, recipe_intro_text, prep_time, cook_time, ingredients, how_to_make, image_url, id))
    conn.commit()
    cursor.execute(f'SELECT * FROM {database}.recipes WHERE username = %s', (username))
    data = cursor.fetchall()

    #bring user to their Profile page 
    return render_template('profile.html', username=session['username'].capitalize(), data=data)

##### RECIPE API CALL #####

# needs a query that is enter by the user on HTML form 
def edamam_search(query):
    # assign variable to the API call headers to create the endpoint 
    # these should be concealed 
    app_id = os.getenv('APP_ID')
    app_key = os.getenv('APP_KEY')

    # endpoint creation 
    curl = f"https://api.edamam.com/search?q={query}" \
           f"&app_id={app_id}" \
           f"&app_key={app_key}&from=0&to=20"

    # assign variable to the API call 
    response = requests.get(curl)
    # assign variable to the data items in the JSON (hits is the term declared by Edamam)
    hits = response.json()['hits']

    return hits

# show the API call results 
@app.route('/results')
def search():
    # 'ingredient' is what the user is searching by for the API call 
    ingredient = request.args.get('ingredient')

    hits = edamam_search(ingredient)
    print(hits)
    return render_template("results.html", ingredient=ingredient, hits=hits) 
    

if __name__ == "__main__":

    #db.create_all()
    app.run(debug=True)

from flask import Flask, redirect, url_for, render_template, request, session, flash
from datetime import timedelta
from flask_sqlalchemy import SQLAlchemy
from flaskext.mysql import MySQL
from werkzeug.security import generate_password_hash, check_password_hash

mysql = MySQL()
app = Flask(__name__)
app.secret_key = "hello"

app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = '!22w0rmt3ch22!'
app.config['MYSQL_DATABASE_DB'] = 'recipe'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)


#app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.sqlite3'
#app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.permanent_session_lifetime = timedelta(minutes=30)

#db = SQLAlchemy(app)

#class users(db.Model):
#    _id = db.Column("id", db.Integer, primary_key=True)
#    username = db.Column(db.String(100))
#    email = db.Column(db.String(100))
#    password = db.Column(db.String(100))



#    def  __init__(self, username, email, password):
#        self.username = username
#        self.email = email
#        self.password = password

#class recipes(db.Model):
#    _id = db.Column("id", db.Integer, primary_key=True)
#    recipe_name = db.Column(db.String(100))
#    recipe_intro_text = db.Column(db.String(1000))
#    prep_time = db.Column(db.String(100))
#    ingredients = db.Column(db.String(1000))
#    how_to_make = db.Column(db.String(1000))

#    def  __init__(self, recipe_name, recipe_intro_text, prep_time, ingredients, how_to_make):
#        self.recipe_name = recipe_name
#        self.recipe_intro_text = recipe_intro_text
#        self.prep_time = prep_time
#        self.ingredients = ingredients
#        self.how_to_make = how_to_make

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    msg=''
     # Check if "username" and "password" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        conn = mysql.connect()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = %s AND password = %s', (username, password))
        #existing_user = users.query.filter_by(username=username, password=password).first()
        existing_user = cursor.fetchone()
        # If account exists in accounts table in out database
        if existing_user:
            # Create session data, we can access this data in other routes
            session['loggedin'] = True
            session['id'] = existing_user[0]
            session['username'] = existing_user[1]
            # Redirect to home page
            username=session['username']
            conn = mysql.connect()
            cursor = conn.cursor()
            #_hashed_password = generate_password_hash(password)
            cursor.execute('SELECT * FROM recipe.recipes WHERE username = %s', (username))
            data = cursor.fetchall()

            return render_template('profile.html', username=session['username'].capitalize(), data=data)
        else:
            # Account doesnt exist or username/password incorrect
            return render_template('login.html', msg='Incorrect username/password!')
    return render_template("login.html", msg='')

# http://localhost:5000/python/logout - this will be the logout page
@app.route('/logout')
def logout():
    # Remove session data, this will log the user out
   session.pop('loggedin', None)
   session.pop('id', None)
   session.pop('username', None)
   # Redirect to login page
   return redirect(url_for('login'))


@app.route('/showRegister')
def showRegister():
    return render_template('register.html')


# http://localhost:5000/pythinlogin/register - this will be the registration page, we need to use both GET and POST requests
@app.route('/register', methods=['GET', 'POST'])
def register():
    # Output message if something goes wrong...
    msg = ''
    # Check if "username", "password" and "email" POST requests exist (user submitted form)
#    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:
        # Create variables for easy access
    try:
        username = request.form['username']
        password = request.form['password']

        if username and password:
            conn = mysql.connect()
            cursor = conn.cursor()
            #_hashed_password = generate_password_hash(password)
            cursor.callproc('sp_create_user',(username, password))
            data = cursor.fetchall()

            if len(data) == 0:
                conn.commit()
                msg = 'You have successfully registered! Please login.'
            else:
                msg = 'Username already taken. Please try again.'

    finally:
        cursor.close()
        conn.close()


        #        existing_user = users.query.filter_by(username=username).first()
                 # If account exists show error and validation checks
        #        if existing_user:
        #            msg = 'Account already exists!'

        #        else:
                    # Account doesnt exists and the form data is valid, now insert new account into accounts table
        #            usr = users(username, email, password)
        #            db.session.add(usr)
        #            db.session.commit()
        #            msg = 'You have successfully registered!'
        #    elif request.method == 'POST':
                # Form is empty... (no POST data)
        #        msg = 'Please fill out the form!'
            # Show registration form with message (if any)
    return render_template('register.html', msg=msg)



@app.route('/profile', methods=['GET'])
def profile():
    msg=''
    # Check if user is loggedin
    if 'loggedin' in session:
        # User is loggedin show them the home page
        username=session['username']
        conn = mysql.connect()
        cursor = conn.cursor()
        #_hashed_password = generate_password_hash(password)
        cursor.execute('SELECT * FROM recipe.recipes WHERE username = %s', (username))
        data = cursor.fetchall()

        return render_template('profile.html', username=session['username'].capitalize(), data=data)
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))

@app.route('/show_add_recipe')
def show_add_recipe():
    return render_template('add_recipe.html', username=session['username'].capitalize())

@app.route('/add_recipe', methods=['GET', 'POST'])
def add_recipe():
    msg=''
    # Check if "username" and "password" POST requests exist (user submitted form)
    if request.method == 'POST' and 'cuisine_category' in request.form and 'recipe_name' in request.form and 'recipe_intro_text' in request.form and 'prep_time' in request.form and 'ingredients' in request.form and 'how_to_make' in request.form and 'image_url' in request.form:
        username = session['username']
        cuisine_category = request.form['cuisine_category']
        recipe_name = request.form['recipe_name']
        recipe_intro_text = request.form['recipe_intro_text']
        prep_time = request.form['prep_time']
        ingredients = request.form['ingredients']
        how_to_make = request.form['how_to_make']
        image_url = request.form['image_url']


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

        conn = mysql.connect()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO recipes(username, recipe_name, recipe_intro_text, prep_time, ingredients, how_to_make, image_url, cuisine_category) VALUES( %s, %s, %s, %s, %s, %s, %s, %s)', (username, recipe_name, recipe_intro_text, prep_time, ingredients, how_to_make, image_url, cuisine_category))
        conn.commit()

        return render_template("add_recipe.html", username=session['username'].capitalize(), msg='Successfully added recipe!')

    return render_template("add_recipe.html", username=session['username'].capitalize(), msg='Recipe not added.')

@app.route('/recipe_single/<id>')
def recipe_single(id):
    conn = mysql.connect()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM recipe.recipes WHERE id= %s' , (id))
    page = cursor.fetchall()

    return render_template("recipepage.html", page=page)

@app.route('/delete_recipe/<id>')
def delete_recipe(id):
    conn = mysql.connect()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM recipes WHERE id= %s' , (id))
    conn.commit()

    username=session['username']
    conn = mysql.connect()
    cursor = conn.cursor()
    #_hashed_password = generate_password_hash(password)
    cursor.execute('SELECT * FROM recipe.recipes WHERE username = %s', (username))
    data = cursor.fetchall()

    return render_template('profile.html', username=session['username'].capitalize(), data=data)

@app.route('/edit_recipe/<id>', methods=['GET', 'POST'])
def edit_recipe(id):
    msg=''
    if request.method == 'POST' and 'recipe_name' in request.form and 'recipe_intro_text' in request.form and 'prep_time' in request.form and 'ingredients' in request.form and 'how_to_make' in request.form and 'image_url' in request.form:
        username = session['username']
        recipe_name = request.form['recipe_name']
        recipe_intro_text = request.form['recipe_intro_text']
        prep_time = request.form['prep_time']
        ingredients = request.form['ingredients']
        how_to_make = request.form['how_to_make']
        image_url = request.form['image_url']

        conn = mysql.connect()
        cursor = conn.cursor()
        edit_sql = 'UPDATE recipes SET recipe_name = %s, recipe_intro_text = %s, prep_time = %s, ingredients = %s, how_to_make = %s, image_url = %s  WHERE id = %s'
        values = (recipe_name, recipe_intro_text, prep_time, ingredients, how_to_make, image_url, id)
        cursor.execute(edit_sql,values)
        conn.commit()

        username=session['username']
        conn = mysql.connect()
        cursor = conn.cursor()
        #_hashed_password = generate_password_hash(password)
        cursor.execute('SELECT * FROM recipe.recipes WHERE username = %s', (username))
        data = cursor.fetchall()

        return render_template('profile.html', username=session['username'].capitalize(), data=data, msg="Successfully updated recipe!")


    conn = mysql.connect()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM recipe.recipes WHERE id= %s' , (id))
    page = cursor.fetchall()

    return render_template("edit_recipe.html", username=session['username'].capitalize(), page=page)


if __name__ == "__main__":

    #db.create_all()
    app.run(debug=True)

from flask import Flask, request, jsonify, redirect, url_for, render_template, redirect, session
from flask_cors import CORS
import psycopg2
from psycopg2.extras import DictCursor
from functools import wraps
import spacy
import bcrypt

app = Flask(__name__)
CORS(app)


nlp = spacy.load("en_core_web_sm")
app.secret_key='22222'


def get_db_connection():
    return psycopg2.connect(
        host="localhost",
        database="recipes_db",
        user="recipe_user",
        password="secure_password",
        cursor_factory=DictCursor
    )

@app.route('/index')
@login_required
def index():
    return render_template('index.html')


@app.route('/get-recipe', methods=['GET'])
@login_required
def get_recipe():
    try:
        ingredients_input = request.args.get('ingredients', '').lower()

        
        doc = nlp(ingredients_input)

        
        ingredients = [token.lemma_ for token in doc if len(token.text) > 2]
        original_ingredients = [token.text for token in doc if len(token.text) > 2]
        split_ingredients = ingredients_input.split()

       
        search_terms = list(set(ingredients + original_ingredients + split_ingredients))

        if not search_terms:
            return jsonify({"success": False, "message": "No valid ingredients found"}), 400

        
        conn = get_db_connection()
        cursor = conn.cursor()

        query = """
        SELECT name, ingredients, instructions, steps
        FROM recipes
        WHERE """ + " OR ".join([f"ingredients ILIKE %s" for _ in search_terms])

        cursor.execute(query, [f"%{term}%" for term in search_terms])
        results = cursor.fetchall()

        cursor.close()
        conn.close()

        if results:
            recipes = []
            for result in results:
                recipe_name, recipe_ingredients, instructions, steps = result
                recipe_ingredients_list = recipe_ingredients.lower().split(', ')
                matched = [ing for ing in search_terms if ing in recipe_ingredients_list]
                missing = [ing for ing in recipe_ingredients_list if ing not in search_terms]

                recipes.append({
                    "name": recipe_name,
                    "matched_ingredients": matched,
                    "missing_ingredients": missing,
                    "instructions": instructions,
                    "steps": steps.split(', ')
                })

            return jsonify({"success": True, "recipes": recipes})
        else:
            return jsonify({"success": False, "message": "No recipes found"}), 404
    except Exception as e:
        return jsonify({"success": False, "message": f"An error occurred: {str(e)}"}), 500
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/')
def home():
    return redirect(url_for('login_page'))


@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if request.method == 'GET':
        return render_template('login.html')

    elif request.method == 'POST':
        try:
            email = request.form.get('email')
            password = request.form.get('password')

            if not email or not password:
                return jsonify({"success": False, "message": "Email and password are required"}), 400

            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
            user = cursor.fetchone()

            if user and bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
                session['user_id'] = user['id']  # Oturumu başlatıyoruz
                return redirect(url_for('index'))
            else:
                return jsonify({"success": False, "message": "Invalid credentials"}), 401
        except Exception as e:
            return jsonify({"success": False, "message": f"An error occurred: {str(e)}"}), 500
       
@app.route('/logout_user')
def logout_user():
    
    session.pop('user_id', None)
    return redirect(url_for('login_page'))  

@app.route('/signup', methods=['GET', 'POST'])
def signup_page():
    if request.method == 'GET':
        return render_template('signup.html')  

    elif request.method == 'POST':
        try:
           
            email = request.form.get('email')
            username = request.form.get('username')
            password = request.form.get('password')

            
            if not email or not username or not password:
                return "All fields are required", 400

            
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

            
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (email, username, password) VALUES (%s, %s, %s)",
                (email, username, hashed_password.decode('utf-8'))
            )
            conn.commit()
            cursor.close()
            conn.close()

            
            return redirect(url_for('login_page'))

        except Exception as e:
            return f"An error occurred: {str(e)}", 500

if __name__ == "__main__":
    app.run(debug=True)

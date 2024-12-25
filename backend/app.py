from flask import Flask, request, jsonify, redirect, url_for, render_template, redirect, session
from flask_cors import CORS
import psycopg2
from psycopg2.extras import DictCursor
from functools import wraps
import spacy

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
def index():
    return render_template('index.html')


@app.route('/get-recipe', methods=['GET'])
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


if __name__ == "__main__":
    app.run(debug=True)

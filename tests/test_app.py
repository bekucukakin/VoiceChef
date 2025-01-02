import pytest
from unittest.mock import patch, MagicMock
from flask import Flask
from backend.app import get_db_connection, login_page, index, signup_page, get_recipe, logout_user

def test_get_db_connection_success():
    with patch('app.sqlite3.connect') as mock_connect:
        mock_connect.return_value = MagicMock()
        conn = get_db_connection()
        assert conn is not None
        mock_connect.assert_called_once()

def test_get_db_connection_failure():
    with patch('app.sqlite3.connect', side_effect=Exception('Database error')) as mock_connect:
        with pytest.raises(Exception) as exc_info:
            get_db_connection()
        assert str(exc_info.value) == 'Database error'

def test_login_success(client):
    response = client.post('/login', data={'username': 'valid_user', 'password': 'valid_password'})
    assert response.status_code == 200
    assert b'Welcome' in response.data

def test_login_failure(client):
    response = client.post('/login', data={'username': 'invalid_user', 'password': 'wrong_password'})
    assert response.status_code == 401
    assert b'Invalid credentials' in response.data

def test_index_access_with_login(client, logged_in_user):
    response = client.get('/')
    assert response.status_code == 200
    assert b'Home Page' in response.data

def test_index_access_without_login(client):
    response = client.get('/')
    assert response.status_code == 302  
    assert b'Redirecting' in response.data

def test_signup_success(client):
    response = client.post('/signup', data={'username': 'new_user', 'password': 'new_password'})
    assert response.status_code == 201
    assert b'Account created' in response.data

def test_signup_failure(client):
    response = client.post('/signup', data={'username': '', 'password': 'password'})
    assert response.status_code == 400
    assert b'Missing information' in response.data

def test_get_recipe_success(client):
    response = client.post('/get_recipe', data={'ingredients': 'eggs,flour'})
    assert response.status_code == 200
    assert b'Recipes found' in response.data

def test_get_recipe_no_results(client):
    response = client.post('/get_recipe', data={'ingredients': 'unknown_ingredient'})
    assert response.status_code == 404
    assert b'No recipes found' in response.data

def test_get_recipe_invalid_input(client):
    response = client.post('/get_recipe', data={'ingredients': ''})
    assert response.status_code == 400
    assert b'Invalid input' in response.data

def test_protected_route_without_login(client):
    response = client.get('/protected')
    assert response.status_code == 302  
    assert b'Redirecting' in response.data

def test_password_hashing():
    from werkzeug.security import check_password_hash, generate_password_hash
    password = 'secure_password'
    hashed_password = generate_password_hash(password)
    assert check_password_hash(hashed_password, password)

def test_logout_user(client, logged_in_user):
    response = client.get('/logout')
    assert response.status_code == 302  
    response = client.get('/protected')
    assert response.status_code == 302  

def test_db_error_handling():
    with patch('app.get_db_connection', side_effect=Exception('Database error')):
        with pytest.raises(Exception) as exc_info:
            get_db_connection()
        assert str(exc_info.value) == 'Database error'

def test_login_page_render(client):
    response = client.get('/login')
    assert response.status_code == 200
    assert b'Login' in response.data

def test_signup_page_render(client):
    response = client.get('/signup')
    assert response.status_code == 200
    assert b'Sign Up' in response.data

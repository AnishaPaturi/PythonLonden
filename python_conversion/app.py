import yaml
import os
import hashlib
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from login_backend_python.extensions import db
from login_backend_python.models import find_user_by_username
from python_conversion.token_filter import token_required, generate_token, refresh_token
from python_conversion.src.test_responder_data import test_bp
from python_conversion.models import get_dashboard_index_stats, get_dashboard_newdemos_states, get_dashboard_responder_file_data


app = Flask(__name__)

# Load config from YAML
config_path = os.path.join(os.path.dirname(__file__), 'config.yml')
with open(config_path, 'r') as f:
    config = yaml.safe_load(f)

app.config['SECRET_KEY'] = config['app']['secret_key']

# Database configuration for remote PostgreSQL
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://londen:FuseMind2024@db2204.laser2mail.com:5432/londen-local'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy
db.init_app(app)

# Register the global after_request handler for token refresh
refresh_token(app)

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    name = data.get('name')
    password = data.get('password')
    print("Received password:", password)

    if not name or not password:
        return jsonify({"error": "Name and password required"}), 400

    user = find_user_by_username(name)
    if user:
        print("Stored password hash:", user.password)
    else:
        print("User not found")

    # Hash the received password before comparison
    hashed_password = hashlib.md5(password.encode()).hexdigest()

    if user and user.password == hashed_password:
        token = generate_token(app, user)
        return jsonify({"message": "Login successful", "token": token})
    else:
        print("Password mismatch or user not found")
        return jsonify({"error": "Invalid credentials"}), 401

@app.route('/api/logout', methods=['POST'])
@token_required(app)
def logout(current_user):
    # With JWT, logout is handled client-side by discarding the token
    return jsonify({"message": "Logout successful. Please discard the token on client side."})

@app.route('/api/status', methods=['GET'])
@token_required(app)
def status(current_user):
    return jsonify({"logged_in": True, "name": current_user.name})

@app.route('/', methods=['GET'])
def home():
    return jsonify({"message": "Welcome to the Login Backend API"}), 200

@app.route('/api/login', methods=['GET'])
def login_get():
    return jsonify({"message": "Please use POST method to login with username and password"}), 200


app.register_blueprint(test_bp)

# Dashboard routes

@app.route('/api/dashboard/index', methods=['GET'])
@token_required(app)
def dashboard_index(current_user):
    resp = {}
    top10 = get_dashboard_index_stats(db)
    resp["stats"] = top10
    return jsonify(resp)

@app.route('/api/dashboard/mailed', methods=['GET'])
@token_required(app)
def dashboard_mailed(current_user):
    # Empty method in PHP, returning empty JSON
    return jsonify({})

@app.route('/api/dashboard/policy2009', methods=['GET'])
@token_required(app)
def dashboard_policy2009(current_user):
    # Empty method in PHP, returning empty JSON
    return jsonify({})

@app.route('/api/dashboard/potential', methods=['GET'])
@token_required(app)
def dashboard_potential(current_user):
    # Empty method in PHP, returning empty JSON
    return jsonify({})

@app.route('/api/dashboard/responserate', methods=['GET'])
@token_required(app)
def dashboard_responserate(current_user):
    # Empty method in PHP, returning empty JSON
    return jsonify({})

@app.route('/api/dashboard/newdemos', methods=['GET'])
@token_required(app)
def dashboard_newdemos(current_user):
    states = get_dashboard_newdemos_states(db)
    return jsonify(states)

@app.route('/api/dashboard/responderFile', methods=['GET'])
@token_required(app)
def dashboard_responderFile(current_user):
    data = get_dashboard_responder_file_data(db)
    return jsonify(data)

if __name__ == '__main__':
    app.run(debug=True)

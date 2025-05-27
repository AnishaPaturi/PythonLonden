import yaml
import os
import hashlib
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from login_backend_python.extensions import db
from login_backend_python.models import find_user_by_username
from python_conversion.token_filter import token_required, generate_token, refresh_token
from python_conversion.src.test_responder_data import test_bp


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

from python_conversion.token_filter import token_required

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
    from sqlalchemy import text
    resp = {}
    sql = text("""
        SELECT state_abbr, county_name, 
            (sales_2009 / (1.0 * mailed_count) * 100) AS sales_rate,
            sales_2009, mailed_count
        FROM counties
        WHERE mailed_count IS NOT NULL
            AND mailed_count > sales_2009
            AND mailed_count > 10000
        ORDER BY (sales_2009 / (1.0 * mailed_count) * 100) DESC
        LIMIT 8
    """)
    result = db.session.execute(sql)
    top10 = []
    for row in result:
        # row is a SQLAlchemy Row object, convert to dict properly
        row_dict = {key: value for key, value in row._mapping.items()}
        top10.append(row_dict)
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

from sqlalchemy import text

@app.route('/api/dashboard/newdemos', methods=['GET'])
@token_required(app)
def dashboard_newdemos(current_user):
    ohio_sql = text("SELECT * FROM county_prospects WHERE state_code='OH' ORDER BY county_name")
    texas_sql = text("SELECT * FROM county_prospects WHERE state_code='TX' ORDER BY county_name")
    ohio_result = db.session.execute(ohio_sql)
    texas_result = db.session.execute(texas_sql)
    states = {
        'OH': [dict(row) for row in ohio_result],
        'TX': [dict(row) for row in texas_result]
    }
    return jsonify(states)

from sqlalchemy import text

@app.route('/api/dashboard/responderFile', methods=['GET'])
@token_required(app)
def dashboard_responderFile(current_user):
    sql = text("""
        SELECT coalesce(state_name, state, '') as state, 
            coalesce(total_dups,0) + coalesce(policy,0) AS total, 
            coalesce(policy,0) as policy_holders, 
            coalesce(total_dups,0) - coalesce(total,0) AS household_duplicates,
            coalesce(total,0) AS net
        FROM (
            SELECT coalesce(state,'') AS state, count(*) as policy
            FROM responder_file
            WHERE cust_flag = 'Y'
            GROUP BY coalesce(state, '')
            ) AS p
        FULL OUTER JOIN (
            SELECT state, count(*) AS total, sum(cnt) AS total_dups
            FROM (
                SELECT address_2, postal, coalesce(state, '') AS state, count(*) as cnt
                FROM responder_file
                WHERE coalesce(cust_flag, 'N') <> 'Y'
                GROUP BY address_2, postal, coalesce(state, '')
            ) AS hh
            GROUP BY state
        ) AS h1 USING (state)
        JOIN state_lookup ON (state = state_code)
    """)
    result = db.session.execute(sql)
    data = [dict(row) for row in result]
    fields = {
        'state': 'C',
        'total': 'N',
        'policy_holders': 'N',
        'household_duplicates': 'N',
        'net': 'N'
    }
    return jsonify({'data': data, 'fields': fields})

if __name__ == '__main__':
    app.run(debug=True)











#python -c "import hashlib; print(hashlib.md5('06cac09'.encode()).hexdigest())"
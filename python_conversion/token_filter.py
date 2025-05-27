from flask import request, jsonify
import jwt
import datetime
from functools import wraps
from login_backend_python.models import find_user_by_username

# JSON schema for token response
def token_response_schema(username, token):
    return {
        "username": username,
        "token": token
    }

# Decorator to protect routes
def token_required(app):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            print("Request headers:", dict(request.headers))
            # Try different header cases for token
            token = request.headers.get('x-auth-token', None)
            if not token:
                token = request.headers.get('X-Auth-Token', None)
            if not token:
                token = request.headers.get('Authorization', None)
                if token and token.startswith('Bearer '):
                    token = token[7:]
            print("auth_header", token)

            if not token:
                return jsonify({'error': 'Token is missing!'}), 401

            try:
                # Decode the token
                data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
                current_user = find_user_by_username(data['name'])

                if not current_user:
                    return jsonify({'error': 'User not found!'}), 401

                kwargs['current_user'] = current_user

                # Generate new token with 5-minute expiry
                new_payload = {
                    'name': current_user.name,
                    'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=5)
                }
                new_token = jwt.encode(new_payload, app.config['SECRET_KEY'], algorithm="HS256")

            except jwt.ExpiredSignatureError:
                return jsonify({'error': 'Token has expired!'}), 401
            except jwt.InvalidTokenError as e:
                print(f"Invalid token error: {str(e)}")
                return jsonify({'error': 'Invalid token!'}), 401

            # Call the actual route
            response = f(*args, **kwargs)

            # Ensure the response is a proper Flask Response object
            if isinstance(response, tuple):
                resp = jsonify(response[0])
                resp.status_code = response[1]
            else:
                resp = response

            # Attach new token to response headers
            resp.headers['x-auth-token'] = new_token

            # Also add the new token to the JSON response body if possible
            try:
                json_data = resp.get_json()
                if isinstance(json_data, dict):
                    json_data['token'] = new_token
                    resp.set_data(jsonify(json_data).get_data())
                    # Removed adding token to 'results' or 'docs' as per user request
                    # if 'results' in json_data and isinstance(json_data['results'], dict):
                    #     json_data['results']['token'] = new_token
                    #     resp.set_data(jsonify(json_data).get_data())
                    # if 'docs' in json_data and isinstance(json_data['docs'], dict):
                    #     json_data['docs']['token'] = new_token
                    #     resp.set_data(jsonify(json_data).get_data())
                elif isinstance(json_data, list):
                    # Wrap list response in a dict to include token
                    wrapped = {
                        'data': json_data,
                        'token': new_token
                    }
                    resp.set_data(jsonify(wrapped).get_data())
            except Exception as e:
                print(f"Error adding token to response body: {e}")

            return resp  # ✅ THIS WAS MISSING

        return decorated
    return decorator

# Generate token
def generate_token(app, user):
    payload = {
        'name': user.name,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    }
    token = jwt.encode(payload, app.config['SECRET_KEY'], algorithm="HS256")
    return token

# Optional: Automatically refresh token after request (if not using token_required for all routes)
def refresh_token(app):
    @app.after_request
    def refresh(response):
        try:
            token = request.headers.get('x-auth-token', None)
            if token:
                data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
                current_user = find_user_by_username(data['name'])
                if current_user:
                    new_payload = {
                        'name': current_user.name,
                        'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=5)
                    }
                    new_token = jwt.encode(new_payload, app.config['SECRET_KEY'], algorithm="HS256")
                    response.headers['x-auth-token'] = new_token
        except Exception as e:
            print(f"Token refresh error: {e}")
        return response

from flask import request, jsonify
import jwt
import datetime
from functools import wraps

SECRET_KEY = 'your-secret-key'

class AuthController:
    def __init__(self):
        self.users = {
            'admin': {
                'password': 'admin123',
                'role': 'administrator'
            },
            'vip': {
                'password': 'vip123',
                'role': 'vip'
            },
            'user': {
                'password': 'user123',
                'role': 'user'
            }
        }

    def authenticate(self, username, password):
        if username in self.users and self.users[username]['password'] == password:
            token = jwt.encode({
                'user': username,
                'role': self.users[username]['role'],
                'exp': datetime.datetime.utcnow() + datetime.datetime.timedelta(hours=24)
            }, SECRET_KEY)
            return token
        return None

    def token_required(self, roles=[]):
        def decorator(f):
            @wraps(f)
            def decorated(*args, **kwargs):
                token = request.headers.get('Authorization')
                if not token:
                    return jsonify({'message': 'Token is missing'}), 401
                
                try:
                    token = token.split(" ")[1]  # Remove 'Bearer ' prefix
                    data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
                    if roles and data['role'] not in roles:
                        return jsonify({'message': 'Insufficient permissions'}), 403
                except:
                    return jsonify({'message': 'Invalid token'}), 401

                return f(*args, **kwargs)
            return decorated
        return decorator

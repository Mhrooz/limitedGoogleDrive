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
                'roles': ['administrator']
            },
            'vip': {
                'password': 'vip123',
                'role': 'vip'
            },
            'user': {
                'password': 'user123',
                'roles': ['user']
            }
        }

    def authenticate(self, username, password):
        if username in self.users and self.users[username]['password'] == password:
            token = jwt.encode({
                'user': username,
                'roles': self.users[username]['roles'],
                'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
            }, SECRET_KEY)
            return token
        return None

    def token_required(self, roles=[]):
        def decorator(f):
            @wraps(f)
            def decorated(*args, **kwargs):
                token = request.headers.get('Authorization')
                if not token:
                    return jsonify({'error': 'Token is missing'}), 401
                
                try:
                    token = token.split(" ")[1]  # Remove 'Bearer ' prefix
                    data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
                    user_roles = data.get('roles', [])
                    
                    if roles and not any(role in roles for role in user_roles):
                        return jsonify({'error': 'Insufficient permissions'}), 403
                        
                except jwt.ExpiredSignatureError:
                    return jsonify({'error': 'Token has expired'}), 401
                except jwt.InvalidTokenError:
                    return jsonify({'error': 'Invalid token'}), 401
                
                return f(*args, **kwargs)
            return decorated
        return decorator

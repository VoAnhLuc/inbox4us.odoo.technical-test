import jwt
import datetime
from odoo import http, models, fields
from odoo.http import request
from functools import wraps

SECRET_KEY = 'b%bz+hmxzky@^34)kgy-2olxp&08ha4f+3l&m#+_fybiww-r='

def validate_request(required_params=None, token_required=True):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Validate presence of JSON request
            if not request.jsonrequest:
                return {"error": "Missing JSON request body"}, 400

            # Validate required parameters
            data = request.jsonrequest.get('params', {})
            if required_params:
                missing_params = [param for param in required_params if param not in data]
                if missing_params:
                    return {
                        "error": f"Missing required parameters: {', '.join(missing_params)}"
                    }, 400

            # Validate Authorization token if required
            if token_required:
                auth_header = request.httprequest.headers.get('Authorization', '')
                if not auth_header:
                    return {"error": "Authorization header is missing!"}, 401

                token_parts = auth_header.split(' ')
                if len(token_parts) != 2 or token_parts[0] != 'Bearer':
                    return {"error": "Invalid token format"}, 401

                token = token_parts[1]
                try:
                    decoded_token = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
                    kwargs['decoded_token'] = decoded_token  # Pass decoded token to the controller method
                except jwt.ExpiredSignatureError:
                    return {"error": "Token has expired!"}, 401
                except jwt.InvalidTokenError:
                    return {"error": "Invalid token!"}, 401

            return func(*args, **kwargs)
        return wrapper
    return decorator

class AuthController(http.Controller):

    @http.route('/api/register', type='json', auth="none", methods=['POST'], cors='*', csrf=False)
    @validate_request(required_params=['name', 'phone', 'email', 'password'], token_required=False)
    def register(self, **kwargs):
        # TODO: Implement user registration logic
        name = kwargs.get("name")
        phone = kwargs.get("phone")
        email = kwargs.get("email")
        password = kwargs.get("password")
        print(kwargs)
        # Check if user already exists
        existing_user = request.env['res.users'].sudo().search([('login', '=', email)], limit=1)
        if existing_user:
            return {"error": "User already exists"}, 400

        # Create new user
        user = request.env['res.users'].sudo().create({
            'name': name,
            'login': email,
            'company_id': 1,
            'company_ids': [(6, 0, [1])],
            'password': password,  # Password will be hashed automatically by Odoo
        })

        # Create corresponding hotel customer record
        customer = request.env['hotel.customer'].sudo().create({
            'name': name,
            'email': email,
            'phone': phone,
        })

        return {"message": "User registered successfully", "user_id": user.id, "customer_id": customer.id}

    @http.route('/api/login', type='json', auth='none', methods=['POST'], cors='*', csrf=False)
    @validate_request(required_params=['email', 'password'], token_required=False)
    def login(self, **kwargs):
        # TODO: Implement user login logic and return JWT token
        # Extract login credentials from request
        email = kwargs.get("email")
        password = kwargs.get("password")

        # Authenticate and raise token
        try:
            uid = request.session.authenticate(request.session.db, email, password)

            user = request.env['res.users'].sudo().search([('id', '=', uid)], limit=1)
            customer = request.env['hotel.customer'].sudo().search([('email', '=', user.login)], limit=1)
            payload = {
                'id': user.id,
                'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1)
            }
            token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
            data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            print("_________________", data)
            return {"token": token, "user_id": user.id, "customer_id": customer.id}
        except Exception as e:
            return {"error": str(e)}, 500

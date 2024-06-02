import jwt
from odoo import http
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

class BookingController(http.Controller):

    @http.route('/api/bookings', type='json', auth='public', methods=['POST'], csrf=False)
    # @validate_request - TODO: handle request validation - Nice to have
    @validate_request(required_params=['room_id', 'checkin_date', 'checkout_date'], token_required=True)
    # @jwt_required - TODO: handle jwt token in the request
    def create_booking(self, **kwargs):
        # TODO: need to handle authentication access token
        # TODO: Implement booking creation logic
        # Note: need to check availability of the room

        try:
            # Decode token and get customer login
            decoded_token = kwargs.get('decoded_token')
            user_id = decoded_token.get('id')
            user = request.env['res.users'].sudo().search([('id', '=', user_id)], limit=1)
            customer = request.env['hotel.customer'].sudo().search([('email', '=', user.login)], limit=1)

            # Create new booking with customner login
            room_id = kwargs.get("room_id")
            checkin_date = kwargs.get("checkin_date")
            checkout_date = kwargs.get("checkout_date")

            room = request.env['hotel.room'].sudo().search([('id', '=', room_id)], limit=1)
            if not room:
                return {'error': 'Room not found'}

            if room.status == "available":
                booking = request.env['hotel.booking'].sudo().create({
                    'customer_id': customer.id,
                    'room_id': room_id,
                    'check_in_date': checkin_date,
                    'check_out_date': checkout_date,
                })
                room.status = 'booked'
            else:
                return {'error': 'Room has been booked or maintenance'}

            return {
                'success': True,
                'booking_id': booking.id,
                'booking_status': booking.status,
                'total_amount': booking.total_amount,
            }
        except Exception as e:
            return {"error": str(e)}, 500

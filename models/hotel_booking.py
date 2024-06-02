from odoo import models, fields, api
from datetime import datetime

class HotelBooking(models.Model):
    _name = 'hotel.booking'
    _description = 'Hotel Booking'

    customer_id = fields.Many2one('hotel.customer', string='Customer', required=True)
    room_id = fields.Many2one('hotel.room', string='Room', required=True)
    check_in_date = fields.Datetime(string='Check-in Date', required=True)
    check_out_date = fields.Datetime(string='Check-out Date', required=True)
    total_amount = fields.Float(string='Total Amount', compute='_compute_total_amount', store=True)
    status = fields.Selection([
        ('checkin', 'Checkin'),
        ('checkout', 'Checkout'),
        ('booked', 'Booked'),
    ], string='Status', default='booked')

    @api.depends('room_id', 'check_in_date', 'check_out_date')
    def _compute_total_amount(self):
        for booking in self:
            if booking.check_in_date and booking.check_out_date:
                num_nights = (booking.check_out_date - booking.check_in_date).days
                booking.total_amount = booking.room_id.price_per_night * num_nights

    @api.depends('check_in_date', 'check_out_date')
    def _compute_booking_status(self):
        current_time = datetime.now()
        for booking in self:
            if booking.check_in_date and booking.check_out_date:
                if booking.check_out_date < current_time:
                    booking.status = 'checkout'
                    booking.room_id.status = 'available'
                elif booking.check_in_date <= current_time < booking.check_out_date:
                    booking.status = 'checkin'
                else:
                    booking.status = 'booked'

    @api.model
    def update_booking_status(self):
        bookings = self.search([])
        bookings._compute_booking_status()

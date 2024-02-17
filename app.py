from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import random

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///parking.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Define database models
class ParkingSpot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    is_occupied = db.Column(db.Boolean, default=False)

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    car_type = db.Column(db.String(100))
    plate_number = db.Column(db.String(100))
    booking_time = db.Column(db.Integer)  # time in hours
    pin = db.Column(db.String(6))  # unique pin for booking
    spot_id = db.Column(db.Integer, db.ForeignKey('parking_spot.id'))

# Route for the home page
@app.route('/')
def index():
    return render_template('index.html')

# Utility function to generate a unique PIN
def generate_pin():
    return ''.join(random.choices('0123456789', k=6))

# Route to book a spot
@app.route('/book', methods=['GET', 'POST'])
def book():
    available_spots = ParkingSpot.query.filter_by(is_occupied=False).count()
    if request.method == 'POST':
        car_type = request.form.get('car_type')
        plate_number = request.form.get('plate_number').upper()  # Convert to uppercase
        booking_time = int(request.form.get('booking_time'))

        # Check if the plate number already exists
        existing_booking = Booking.query.filter_by(plate_number=plate_number).first()
        if existing_booking:
            return "Error: This car is already booked."

        # Find an available parking spot
        spot = ParkingSpot.query.filter_by(is_occupied=False).first()

        if spot:
            # Create a new booking
            pin = generate_pin()
            new_booking = Booking(car_type=car_type, plate_number=plate_number,
                                  booking_time=booking_time, pin=pin, spot_id=spot.id)
            spot.is_occupied = True  # Mark the spot as occupied

            db.session.add(new_booking)
            db.session.commit()

            return redirect(url_for('confirmation', pin=pin))
        else:
            return "Sorry, all spots are taken."

    # Count available spots
    available_spots = ParkingSpot.query.filter_by(is_occupied=False).count()
    return render_template('book.html', available_spots=available_spots)

# Route for the confirmation page
@app.route('/confirmation/<pin>')
def confirmation(pin):
    booking = Booking.query.filter_by(pin=pin).first_or_404()
    return render_template('confirmation.html', booking=booking)

# Route for user dashboard
@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if request.method == 'POST':
        pin = request.form.get('pin')
        booking = Booking.query.filter_by(pin=pin).first()
        if booking:
            return render_template('dashboard.html', booking=booking)
        else:
            return "Invalid PIN. Please try again."

    return render_template('dashboard.html')

# Route to cancel a booking
@app.route('/cancel/<int:booking_id>')
def cancel_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    spot = ParkingSpot.query.get(booking.spot_id)
    spot.is_occupied = False  # Free up the parking spot

    db.session.delete(booking)
    db.session.commit()
    if 'admin' in request.referrer:
        return redirect(url_for('admin'))
    else:
        return redirect(url_for('index'))


def initialize_parking_spots():
    if ParkingSpot.query.count() == 0:
        spots = [ParkingSpot() for _ in range(100)]
        db.session.bulk_save_objects(spots)
        db.session.commit()
        print("Initialized 100 parking spots.")

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if username == "admin" and password == "admin":
            all_bookings = Booking.query.all()
            return render_template('admin_dashboard.html', bookings=all_bookings)
        else:
            return "Invalid credentials."

    return render_template('admin_login.html')


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        initialize_parking_spots()  # Initialize parking spots
    app.run(debug=True)

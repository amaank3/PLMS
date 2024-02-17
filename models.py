from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class ParkingSpot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    location = db.Column(db.String(50), nullable=False)
    is_occupied = db.Column(db.Boolean, default=False)

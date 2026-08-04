from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Initialize SQLAlchemy database instance
db = SQLAlchemy()

class User(db.Model):
    """
    User model representing Admin, Trek Staff, and Trekkers.
    - Admin: Superuser managing treks, staff approvals, and blacklisting.
    - Staff: Trek guides who manage slots, trek status, and participant lists.
    - User (Trekker): Regular participants who explore and book treks.
    """
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False) # Hashed password storage
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    role = db.Column(db.String(20), nullable=False, default='User')  # 'Admin', 'Staff', 'User'
    status = db.Column(db.String(20), nullable=False, default='Active') # 'Active', 'Pending', 'Blacklisted'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships: One user can have multiple bookings; One staff can be assigned to multiple treks
    bookings = db.relationship('Booking', backref='user', lazy=True, cascade='all, delete-orphan')
    assigned_treks = db.relationship('Trek', backref='assigned_staff', lazy=True)

    def __repr__(self):
        return f'<User {self.username} ({self.role})>'


class Trek(db.Model):
    """
    Trek model storing trekking event details, slots, status, dates, and assigned staff.
    """
    __tablename__ = 'treks'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    difficulty = db.Column(db.String(20), nullable=False)  # 'Easy', 'Moderate', 'Hard'
    duration_days = db.Column(db.Integer, nullable=False)
    total_slots = db.Column(db.Integer, nullable=False)
    available_slots = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False, default=0.0)
    status = db.Column(db.String(20), nullable=False, default='Open')  # 'Open', 'Closed', 'Completed'
    start_date = db.Column(db.String(20), nullable=False)
    end_date = db.Column(db.String(20), nullable=False)
    
    # Foreign Key linking assigned Staff member
    assigned_staff_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship to Trek Bookings
    bookings = db.relationship('Booking', backref='trek', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Trek {self.name} - {self.location}>'


class Booking(db.Model):
    """
    Booking model linking a Trekker (User) to a Trek event with status tracking.
    """
    __tablename__ = 'bookings'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    trek_id = db.Column(db.Integer, db.ForeignKey('treks.id'), nullable=False)
    booking_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), nullable=False, default='Booked')  # 'Booked', 'Cancelled', 'Completed'
    seats = db.Column(db.Integer, nullable=False, default=1)

    def __repr__(self):
        return f'<Booking ID {self.id} - User {self.user_id} - Trek {self.trek_id}>'


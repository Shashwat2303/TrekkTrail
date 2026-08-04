"""
Seed script to populate initial sample data for Trekking Management Application.
This populates sample Treks, Staff members, and Trekker accounts for easy viva testing.
"""
from app import app, db
from models import User, Trek, Booking
from werkzeug.security import generate_password_hash

def seed_data():
    with app.app_context():
        # Ensure tables exist
        db.create_all()

        # 1. Create Default Admin if missing
        if not User.query.filter_by(username='admin').first():
            admin = User(
                username='admin',
                password=generate_password_hash('adminpassword'),
                full_name='System Admin',
                email='admin@trekking.com',
                phone='9876543210',
                role='Admin',
                status='Active'
            )
            db.session.add(admin)

        # 2. Create Sample Trek Staff
        staff1 = User.query.filter_by(username='staff_rahul').first()
        if not staff1:
            staff1 = User(
                username='staff_rahul',
                password=generate_password_hash('staff123'),
                full_name='Rahul Sharma',
                email='rahul@guides.com',
                phone='9811223344',
                role='Staff',
                status='Active'
            )
            db.session.add(staff1)

        staff2 = User.query.filter_by(username='staff_anita').first()
        if not staff2:
            staff2 = User(
                username='staff_anita',
                password=generate_password_hash('staff123'),
                full_name='Anita Verma',
                email='anita@guides.com',
                phone='9855667788',
                role='Staff',
                status='Active'
            )
            db.session.add(staff2)

        # 3. Create Sample Trekkers (Users)
        user1 = User.query.filter_by(username='trekker_rohit').first()
        if not user1:
            user1 = User(
                username='trekker_rohit',
                password=generate_password_hash('user123'),
                full_name='Rohit Kumar',
                email='rohit@gmail.com',
                phone='9711002233',
                role='User',
                status='Active'
            )
            db.session.add(user1)

        db.session.commit()

        # Re-query staff1 to get ID
        staff1 = User.query.filter_by(username='staff_rahul').first()
        staff2 = User.query.filter_by(username='staff_anita').first()

        # 4. Create Sample Treks
        if Trek.query.count() == 0:
            trek1 = Trek(
                name='Kedarkantha Winter Trek',
                location='Uttarakhand, India',
                difficulty='Easy',
                duration_days=4,
                total_slots=15,
                available_slots=14,
                price=3500.0,
                status='Open',
                start_date='2026-10-15',
                end_date='2026-10-19',
                assigned_staff_id=staff1.id
            )

            trek2 = Trek(
                name='Hampta Pass Trek',
                location='Manali, Himachal Pradesh',
                difficulty='Moderate',
                duration_days=5,
                total_slots=12,
                available_slots=12,
                price=5500.0,
                status='Open',
                start_date='2026-09-01',
                end_date='2026-09-06',
                assigned_staff_id=staff2.id
            )

            trek3 = Trek(
                name='Roopkund Trek',
                location='Garhwal, Uttarakhand',
                difficulty='Hard',
                duration_days=7,
                total_slots=10,
                available_slots=10,
                price=8500.0,
                status='Open',
                start_date='2026-11-10',
                end_date='2026-11-17',
                assigned_staff_id=staff1.id
            )

            db.session.add_all([trek1, trek2, trek3])
            db.session.commit()

        # 5. Create Sample Booking for user1 on trek1
        if Booking.query.count() == 0:
            trek1 = Trek.query.filter_by(name='Kedarkantha Winter Trek').first()
            user1 = User.query.filter_by(username='trekker_rohit').first()
            if trek1 and user1:
                booking1 = Booking(
                    user_id=user1.id,
                    trek_id=trek1.id,
                    status='Booked',
                    seats=1
                )
                db.session.add(booking1)
                db.session.commit()

        print("Database seeded with sample treks, staff, trekkers, and bookings successfully!")

if __name__ == '__main__':
    seed_data()

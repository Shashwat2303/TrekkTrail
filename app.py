import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Trek, Booking

app = Flask(__name__)
app.secret_key = 'trekking_app_secret_key_for_session_management'

# Database Configuration
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(BASE_DIR, 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize Database with Flask App
db.init_app(app)

# Helper Decorators / Access Controls
def is_logged_in():
    return 'user_id' in session

def get_current_user():
    if is_logged_in():
        return User.query.get(session['user_id'])
    return None

# Context Processor to pass current_user to all Jinja templates automatically
@app.context_processor
def inject_user():
    return dict(current_user=get_current_user())

# Initialize DB & Seed Admin User Programmatically
def init_db():
    with app.app_context():
        db.create_all()
        # Check if default admin exists
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            default_admin = User(
                username='admin',
                password=generate_password_hash('adminpassword'),
                full_name='System Admin',
                email='admin@trekking.com',
                phone='9999999999',
                role='Admin',
                status='Active'
            )
            db.session.add(default_admin)
            db.session.commit()
            print("Default admin created successfully.")

# ----------------- PUBLIC ROUTES ----------------- #

@app.route('/')
def index():
    # Show open treks on landing page
    open_treks = Trek.query.filter_by(status='Open').all()
    return render_template('index.html', treks=open_treks)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()

        if not user or not check_password_hash(user.password, password):
            flash('Invalid username or password.', 'danger')
            return redirect(url_for('login'))

        if user.status == 'Blacklisted':
            flash('Your account has been blacklisted by Admin.', 'danger')
            return redirect(url_for('login'))

        if user.role == 'Staff' and user.status == 'Pending':
            flash('Your staff registration is pending Admin approval.', 'warning')
            return redirect(url_for('login'))

        # Set session details
        session['user_id'] = user.id
        session['username'] = user.username
        session['role'] = user.role

        flash(f'Welcome back, {user.full_name}!', 'success')

        if user.role == 'Admin':
            return redirect(url_for('admin_dashboard'))
        elif user.role == 'Staff':
            return redirect(url_for('staff_dashboard'))
        else:
            return redirect(url_for('user_dashboard'))

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        full_name = request.form.get('full_name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        role = request.form.get('role', 'User')  # 'User' or 'Staff'

        # Check existing user
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists. Please choose another.', 'danger')
            return redirect(url_for('register'))

        # Staff registration requires Admin approval (Pending status)
        status = 'Pending' if role == 'Staff' else 'Active'

        hashed_password = generate_password_hash(password)
        new_user = User(
            username=username,
            password=hashed_password,
            full_name=full_name,
            email=email,
            phone=phone,
            role=role,
            status=status
        )

        db.session.add(new_user)
        db.session.commit()

        if role == 'Staff':
            flash('Staff registration successful! Waiting for Admin approval.', 'info')
        else:
            flash('Registration successful! You can now log in.', 'success')

        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('login'))


# ----------------- ADMIN ROUTES ----------------- #

@app.route('/admin/dashboard')
def admin_dashboard():
    if not is_logged_in() or session.get('role') != 'Admin':
        flash('Admin access required.', 'danger')
        return redirect(url_for('login'))

    search_query = request.args.get('search', '').strip()

    # Admin Statistics
    total_treks = Trek.query.count()
    total_users = User.query.filter(User.role != 'Admin').count()
    total_bookings = Booking.query.count()

    # Pending Staff Approvals
    pending_staff = User.query.filter_by(role='Staff', status='Pending').all()

    # All Staff & All Users
    all_staff = User.query.filter_by(role='Staff').all()
    
    # Query for Treks and Users with Search Filter
    if search_query:
        if search_query.isdigit():
            search_id = int(search_query)
            treks = Trek.query.filter(
                (Trek.name.ilike(f'%{search_query}%')) |
                (Trek.location.ilike(f'%{search_query}%')) |
                (Trek.id == search_id)
            ).all()
            users = User.query.filter(
                (User.role != 'Admin') &
                ((User.username.ilike(f'%{search_query}%')) |
                 (User.full_name.ilike(f'%{search_query}%')) |
                 (User.id == search_id))
            ).all()
        else:
            treks = Trek.query.filter(
                (Trek.name.ilike(f'%{search_query}%')) |
                (Trek.location.ilike(f'%{search_query}%'))
            ).all()
            users = User.query.filter(
                (User.role != 'Admin') &
                ((User.username.ilike(f'%{search_query}%')) |
                 (User.full_name.ilike(f'%{search_query}%')))
            ).all()
    else:
        treks = Trek.query.all()
        users = User.query.filter(User.role != 'Admin').all()

    all_bookings = Booking.query.order_by(Booking.booking_date.desc()).all()

    return render_template(
        'admin/dashboard.html',
        total_treks=total_treks,
        total_users=total_users,
        total_bookings=total_bookings,
        pending_staff=pending_staff,
        all_staff=all_staff,
        treks=treks,
        users=users,
        all_bookings=all_bookings,
        search_query=search_query
    )


@app.route('/admin/trek/add', methods=['GET', 'POST'])
def add_trek():
    if not is_logged_in() or session.get('role') != 'Admin':
        flash('Admin access required.', 'danger')
        return redirect(url_for('login'))

    staff_members = User.query.filter_by(role='Staff', status='Active').all()

    if request.method == 'POST':
        name = request.form.get('name')
        location = request.form.get('location')
        difficulty = request.form.get('difficulty')
        duration_days = int(request.form.get('duration_days', 1))
        total_slots = int(request.form.get('total_slots', 10))
        price = float(request.form.get('price', 0.0))
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        assigned_staff_id = request.form.get('assigned_staff_id')
        assigned_staff_id = int(assigned_staff_id) if assigned_staff_id and assigned_staff_id != '' else None

        new_trek = Trek(
            name=name,
            location=location,
            difficulty=difficulty,
            duration_days=duration_days,
            total_slots=total_slots,
            available_slots=total_slots,
            price=price,
            status='Open',
            start_date=start_date,
            end_date=end_date,
            assigned_staff_id=assigned_staff_id
        )

        db.session.add(new_trek)
        db.session.commit()
        flash('Trek route created successfully!', 'success')
        return redirect(url_for('admin_dashboard'))

    return render_template('admin/add_trek.html', staff_members=staff_members)


@app.route('/admin/trek/edit/<int:trek_id>', methods=['GET', 'POST'])
def edit_trek(trek_id):
    if not is_logged_in() or session.get('role') != 'Admin':
        flash('Admin access required.', 'danger')
        return redirect(url_for('login'))

    trek = Trek.query.get_or_404(trek_id)
    staff_members = User.query.filter_by(role='Staff', status='Active').all()

    if request.method == 'POST':
        trek.name = request.form.get('name')
        trek.location = request.form.get('location')
        trek.difficulty = request.form.get('difficulty')
        trek.duration_days = int(request.form.get('duration_days'))
        trek.price = float(request.form.get('price'))
        trek.start_date = request.form.get('start_date')
        trek.end_date = request.form.get('end_date')
        
        # Available slots recalculation
        new_total_slots = int(request.form.get('total_slots'))
        booked_seats = trek.total_slots - trek.available_slots
        trek.total_slots = new_total_slots
        trek.available_slots = max(0, new_total_slots - booked_seats)

        trek.status = request.form.get('status')
        assigned_staff_id = request.form.get('assigned_staff_id')
        trek.assigned_staff_id = int(assigned_staff_id) if assigned_staff_id and assigned_staff_id != '' else None

        db.session.commit()
        flash('Trek details updated successfully.', 'success')
        return redirect(url_for('admin_dashboard'))

    return render_template('admin/edit_trek.html', trek=trek, staff_members=staff_members)


@app.route('/admin/trek/delete/<int:trek_id>', methods=['POST'])
def delete_trek(trek_id):
    if not is_logged_in() or session.get('role') != 'Admin':
        flash('Admin access required.', 'danger')
        return redirect(url_for('login'))

    trek = Trek.query.get_or_404(trek_id)
    db.session.delete(trek)
    db.session.commit()
    flash('Trek removed successfully.', 'info')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/user/toggle-status/<int:user_id>', methods=['POST'])
def toggle_user_status(user_id):
    if not is_logged_in() or session.get('role') != 'Admin':
        flash('Admin access required.', 'danger')
        return redirect(url_for('login'))

    target_user = User.query.get_or_404(user_id)
    action = request.form.get('action') # 'approve', 'blacklist', 'activate'

    if action == 'approve':
        target_user.status = 'Active'
        flash(f'Staff member {target_user.username} approved successfully.', 'success')
    elif action == 'blacklist':
        target_user.status = 'Blacklisted'
        flash(f'User {target_user.username} has been blacklisted.', 'warning')
    elif action == 'activate':
        target_user.status = 'Active'
        flash(f'User {target_user.username} status set to Active.', 'success')

    db.session.commit()
    return redirect(url_for('admin_dashboard'))


# ----------------- STAFF ROUTES ----------------- #

@app.route('/staff/dashboard')
def staff_dashboard():
    if not is_logged_in() or session.get('role') != 'Staff':
        flash('Staff access required.', 'danger')
        return redirect(url_for('login'))

    user = get_current_user()
    if user.status != 'Active':
        flash('Your staff account is not active.', 'danger')
        return redirect(url_for('login'))

    # Get treks assigned to this staff member
    assigned_treks = Trek.query.filter_by(assigned_staff_id=user.id).all()

    return render_template('staff/dashboard.html', treks=assigned_treks)


@app.route('/staff/trek/manage/<int:trek_id>', methods=['GET', 'POST'])
def manage_trek(trek_id):
    if not is_logged_in() or session.get('role') != 'Staff':
        flash('Staff access required.', 'danger')
        return redirect(url_for('login'))

    user = get_current_user()
    trek = Trek.query.get_or_404(trek_id)

    # Ensure only assigned staff can manage this trek
    if trek.assigned_staff_id != user.id:
        flash('You are not assigned to manage this trek.', 'danger')
        return redirect(url_for('staff_dashboard'))

    if request.method == 'POST':
        trek.available_slots = int(request.form.get('available_slots'))
        new_status = request.form.get('status')
        trek.status = new_status

        # If trek is marked as Completed, update all active bookings for this trek to Completed
        if new_status == 'Completed':
            for booking in trek.bookings:
                if booking.status == 'Booked':
                    booking.status = 'Completed'

        db.session.commit()
        flash('Trek updated successfully.', 'success')
        return redirect(url_for('manage_trek', trek_id=trek.id))

    # Participant list for this trek
    bookings = Booking.query.filter_by(trek_id=trek.id).all()

    return render_template('staff/manage_trek.html', trek=trek, bookings=bookings)


# ----------------- USER (TREKKER) ROUTES ----------------- #

@app.route('/user/dashboard')
def user_dashboard():
    if not is_logged_in() or session.get('role') != 'User':
        flash('User access required.', 'danger')
        return redirect(url_for('login'))

    difficulty_filter = request.args.get('difficulty', '').strip()
    location_filter = request.args.get('location', '').strip()
    search_query = request.args.get('search', '').strip()

    query = Trek.query.filter_by(status='Open')

    if difficulty_filter:
        query = query.filter_by(difficulty=difficulty_filter)
    if location_filter:
        query = query.filter(Trek.location.ilike(f'%{location_filter}%'))
    if search_query:
        query = query.filter(
            (Trek.name.ilike(f'%{search_query}%')) |
            (Trek.location.ilike(f'%{search_query}%'))
        )

    treks = query.all()
    user_bookings = Booking.query.filter_by(user_id=session['user_id']).all()
    booked_trek_ids = [b.trek_id for b in user_bookings if b.status == 'Booked']

    return render_template(
        'user/dashboard.html',
        treks=treks,
        booked_trek_ids=booked_trek_ids,
        difficulty_filter=difficulty_filter,
        location_filter=location_filter,
        search_query=search_query
    )


@app.route('/user/trek/book/<int:trek_id>', methods=['POST'])
def book_trek(trek_id):
    if not is_logged_in() or session.get('role') != 'User':
        flash('User access required.', 'danger')
        return redirect(url_for('login'))

    user_id = session['user_id']
    trek = Trek.query.get_or_404(trek_id)

    # Core Validations: Status must be Open and Slots > 0
    if trek.status != 'Open':
        flash('This trek is currently not open for bookings.', 'danger')
        return redirect(url_for('user_dashboard'))

    if trek.available_slots <= 0:
        flash('Sorry, this trek is fully booked!', 'warning')
        return redirect(url_for('user_dashboard'))

    # Check existing booking for this user
    existing = Booking.query.filter_by(user_id=user_id, trek_id=trek.id, status='Booked').first()
    if existing:
        flash('You have already booked this trek.', 'info')
        return redirect(url_for('user_bookings'))

    # Process booking
    booking = Booking(user_id=user_id, trek_id=trek.id, status='Booked', seats=1)
    trek.available_slots -= 1

    db.session.add(booking)
    db.session.commit()

    flash(f'Trek "{trek.name}" booked successfully!', 'success')
    return redirect(url_for('user_bookings'))


@app.route('/user/bookings')
def user_bookings():
    if not is_logged_in() or session.get('role') != 'User':
        flash('User access required.', 'danger')
        return redirect(url_for('login'))

    user_id = session['user_id']
    bookings = Booking.query.filter_by(user_id=user_id).order_by(Booking.booking_date.desc()).all()
    return render_template('user/my_bookings.html', bookings=bookings)


@app.route('/user/booking/cancel/<int:booking_id>', methods=['POST'])
def cancel_booking(booking_id):
    if not is_logged_in() or session.get('role') != 'User':
        flash('User access required.', 'danger')
        return redirect(url_for('login'))

    booking = Booking.query.get_or_404(booking_id)
    if booking.user_id != session['user_id']:
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('user_bookings'))

    if booking.status == 'Booked':
        booking.status = 'Cancelled'
        # Restore available slot
        trek = Trek.query.get(booking.trek_id)
        if trek:
            trek.available_slots += 1
        db.session.commit()
        flash('Booking cancelled successfully.', 'info')

    return redirect(url_for('user_bookings'))


@app.route('/user/profile', methods=['GET', 'POST'])
def user_profile():
    if not is_logged_in():
        flash('Please login to view profile.', 'danger')
        return redirect(url_for('login'))

    user = get_current_user()

    if request.method == 'POST':
        user.full_name = request.form.get('full_name')
        user.email = request.form.get('email')
        user.phone = request.form.get('phone')

        new_password = request.form.get('password')
        if new_password and new_password.strip():
            user.password = generate_password_hash(new_password)

        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('user_profile'))

    return render_template('user/profile.html', user=user)


if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)

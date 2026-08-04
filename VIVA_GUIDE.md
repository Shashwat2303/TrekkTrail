# Trekking Management Application - Viva Defense & Project Guide

**Course**: App Dev I Project (May 2026)  
**Frameworks Used**: Python, Flask, Jinja2, HTML/CSS, Bootstrap 5, SQLite, Flask-SQLAlchemy

---

## 1. Project Overview

The **Trekking Management Application** is a multi-role web platform designed for adventure trekking organizations. It automates trek route administration, staff assignment, trekker bookings, slot allocation, and participant tracking.

### Roles & Responsibilities
1. **Admin (Superuser)**:
   - Pre-existing admin created automatically on database initialization (`admin` / `adminpassword`).
   - Create, edit, and delete trek routes.
   - Assign Trek Staff to specific trek routes.
   - Review and approve pending Trek Staff registrations.
   - Blacklist or activate staff and trekkers.
   - View application metrics (Total Treks, Total Users & Staff, Total Bookings).
   - Unified search across treks, staff, and users by name or numeric ID.

2. **Trek Staff (Guide)**:
   - Self-registers and awaits Admin approval (`Pending` status).
   - Manages assigned treks: updates available slots, changes trek status (`Open`, `Closed`, `Completed`).
   - Views participant lists for assigned treks.

3. **User (Trekker)**:
   - Self-registers and logs in.
   - Browses available open treks with difficulty (`Easy`, `Moderate`, `Hard`) and location filters.
   - Books treks (with strict overbooking protection).
   - Views booking history (`Booked`, `Cancelled`, `Completed`).
   - Cancels bookings (automatically restores available trek slots).
   - Manages account profile and updates password.

---

## 2. Technology Stack & Architecture

- **Backend**: Python 3.x with Flask Framework
- **Database**: SQLite 3 (programmatically created via `Flask-SQLAlchemy` ORM)
- **Frontend**: Jinja2 Templating Engine + HTML5 + CSS3 + Bootstrap 5 UI Framework
- **Security & Session**: Server-side session management (`flask.session`), Werkzeug password hashing (`generate_password_hash`, `check_password_hash`)

---

## 3. Database Schema (ER Model)

### Tables & Relationships

#### 1. `users` Table
- `id` (INTEGER, Primary Key)
- `username` (VARCHAR 50, Unique, Not Null)
- `password` (VARCHAR 255, Hashed, Not Null)
- `full_name` (VARCHAR 100, Not Null)
- `email` (VARCHAR 120, Not Null)
- `phone` (VARCHAR 20)
- `role` (VARCHAR 20: `'Admin'`, `'Staff'`, `'User'`)
- `status` (VARCHAR 20: `'Active'`, `'Pending'`, `'Blacklisted'`)
- `created_at` (DATETIME)

#### 2. `treks` Table
- `id` (INTEGER, Primary Key)
- `name` (VARCHAR 100, Not Null)
- `location` (VARCHAR 100, Not Null)
- `difficulty` (VARCHAR 20: `'Easy'`, `'Moderate'`, `'Hard'`)
- `duration_days` (INTEGER)
- `total_slots` (INTEGER)
- `available_slots` (INTEGER)
- `price` (FLOAT)
- `status` (VARCHAR 20: `'Open'`, `'Closed'`, `'Completed'`)
- `start_date` (VARCHAR 20)
- `end_date` (VARCHAR 20)
- `assigned_staff_id` (INTEGER, Foreign Key -> `users.id`)
- `created_at` (DATETIME)

#### 3. `bookings` Table
- `id` (INTEGER, Primary Key)
- `user_id` (INTEGER, Foreign Key -> `users.id`)
- `trek_id` (INTEGER, Foreign Key -> `treks.id`)
- `booking_date` (DATETIME)
- `status` (VARCHAR 20: `'Booked'`, `'Cancelled'`, `'Completed'`)
- `seats` (INTEGER, Default: 1)

---

## 4. Key viva Defense Questions & Answers

### Q1: How does authentication and role-based access control (RBAC) work in your application?
**Answer**:  
When a user logs in via `/login`, Flask checks the user's credentials against the hashed password using Werkzeug's `check_password_hash`. If valid, the user's `id`, `username`, and `role` are stored in Flask's encrypted cookie-backed `session` object.  
For protected routes (e.g., `/admin/dashboard`), controller functions check `session.get('role')`. If an unauthorized user attempts to access an admin or staff route, the request is redirected to `/login` with an alert message.

---

### Q2: How did you implement overbooking prevention?
**Answer**:  
Overbooking is prevented at the database query level inside the `book_trek` controller (`/user/trek/book/<trek_id>`):
1. The route retrieves the target `Trek` record.
2. It verifies that `trek.status == 'Open'` and `trek.available_slots > 0`.
3. It checks if the trekker already has an active booking for this trek (`Booking.query.filter_by(user_id=user_id, trek_id=trek.id, status='Booked').first()`).
4. If valid, `trek.available_slots` is decremented by 1, and a new `Booking` record is committed within a single atomic database transaction (`db.session.commit()`).

---

### Q3: Why did you use Flask-SQLAlchemy instead of writing raw SQL queries?
**Answer**:  
Flask-SQLAlchemy provides Object-Relational Mapping (ORM), which allows us to interact with the database using Python objects and classes (`User`, `Trek`, `Booking`) rather than writing manual SQL strings. This prevents SQL injection vulnerabilities through parameterized queries, simplifies schema creation via `db.create_all()`, and handles table relationships seamlessly using `db.relationship` and `db.ForeignKey`.

---

### Q4: How is the database created programmatically without DB Browser for SQLite?
**Answer**:  
In `app.py`, the database URI is configured to SQLite (`sqlite:///database.db`). The `init_db()` helper function executes `db.create_all()` inside Flask's application context (`with app.app_context():`). This programmatically generates all required SQL tables on startup if they do not already exist.

---

### Q5: What happens when a user cancels a booking?
**Answer**:  
When a trekker clicks cancel on `/user/booking/cancel/<booking_id>`:
1. The server checks that the booking belongs to the logged-in user.
2. The booking status is updated from `'Booked'` to `'Cancelled'`.
3. The associated trek's `available_slots` is incremented by 1 (`trek.available_slots += 1`).
4. `db.session.commit()` persists the transaction.

---

### Q6: How does Trek Staff registration and Admin approval work?
**Answer**:  
When a staff member registers on `/register` with role `'Staff'`, their account is created with `status='Pending'`. When they attempt to log in, `app.py` checks `if user.role == 'Staff' and user.status == 'Pending'` and blocks login.  
The Admin dashboard displays all pending staff members in an approval queue. When the Admin clicks "Approve", the user's status is changed to `'Active'`, allowing them to log in and access `/staff/dashboard`.

---

### Q7: Why are passwords stored as hashes instead of plain text?
**Answer**:  
Storing plain-text passwords is a major security risk. We use `generate_password_hash(password)` from Werkzeug to generate a secure PBKDF2 hash with a random salt. When logging in, `check_password_hash(user.password, input_password)` verifies the entry without ever storing or displaying raw passwords.

---

## 5. How to Run & Test the Application

### 1. Run Database Seeding Script (Optional)
```bash
python seed_sample_data.py
```

### 2. Start the Flask Application
```bash
python app.py
```
Open your browser and navigate to: `http://127.0.0.1:5000`

### 3. Demo Credentials
- **Admin**: Username: `admin` | Password: `adminpassword`
- **Staff**: Username: `staff_rahul` | Password: `staff123`
- **Trekker**: Username: `trekker_rohit` | Password: `user123`

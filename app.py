# app.py
from flask import Flask, render_template,redirect,url_for,request,redirect, url_for, session,flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from datetime import datetime
from flask import jsonify
from flask_mail import Mail, Message
from werkzeug.utils import secure_filename
import os
import random

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///voting.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

UPLOAD_FOLDER = 'static/images'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Flask-Mail configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'yogendrachaurasiya30@gmail.com'
app.config['MAIL_PASSWORD'] = 'rwmvymykfioubkig'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True

db = SQLAlchemy(app)
mail = Mail(app)

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    semester = db.Column(db.Integer, nullable=False)
    student_id = db.Column(db.String(8), nullable=False, unique=True)
    student_image = db.Column(db.String(200))

class OTPVerification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    otp = db.Column(db.String(6), nullable=False)
    verified = db.Column(db.Boolean, default=False, nullable=False)

@app.route('/')
def user_index():
    return redirect(url_for('home'))

@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/features')
def features():
    return render_template('features.html')

@app.route('/demo')
def demo():
    return render_template('demo.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/signin_layout')
def signin_layout():
    return render_template('signin_layout.html')

@app.route('/userLogin', methods=['GET', 'POST'])
def userLogin():
    if request.method == 'POST':
        email = request.form['email']
        user = Student.query.filter_by(email=email).first()
        if user:
            otp_verification = OTPVerification.query.filter_by(email=email).first()
            if not otp_verification or not otp_verification.verified:
                otp = generate_otp()
                session['otp'] = otp
                session['email'] = email  # Store user's email in session
                send_otp_email(email, otp)
                # Save or update OTP verification status in the database
                if not otp_verification:
                    otp_verification = OTPVerification(email=email, otp=otp)
                    db.session.add(otp_verification)
                else:
                    otp_verification.otp = otp
                    otp_verification.verified = False
                db.session.commit()
                return redirect(url_for('verify_otp'))
            else:
                flash("You have already logged in and voted.")
        else:
            flash("You are not registered with this email. Please register first.")
            
    return render_template('userLogin.html')

@app.route('/verify_otp', methods=['GET', 'POST'])
def verify_otp():
    if 'otp' in session and 'email' in session:
        if request.method == 'POST':
            otp_entered = request.form['otp']
            email = session['email']
            otp_verification = OTPVerification.query.filter_by(email=email).first()
            if otp_verification and otp_entered == otp_verification.otp:
                otp_verification.verified = True
                db.session.commit()
                session.pop('otp', None)
                session.pop('email', None)
                return redirect(url_for('index'))
            else:
                flash('Invalid OTP. Please try again.', 'error')
                return redirect(url_for('verify_otp'))
        return render_template('verify_otp.html')
    else:
        return redirect(url_for('userLogin'))

def generate_otp():
    return str(random.randint(100000, 999999))

def send_otp_email(email, otp):
    msg = Message('OTP Verification', sender='yogendrachaurasiya30@example.com', recipients=[email])
    msg.body = f'Your OTP for login is: {otp}'
    mail.send(msg)

@app.route('/userRegister', methods=['GET', 'POST'])
def userRegister():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        semester = request.form['semester']
        student_id = request.form['student_id']

        # Handle file upload
        if 'student_image' in request.files:
            student_image = request.files['student_image']
            if student_image.filename != '':
                filename = secure_filename(student_image.filename)
                image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                student_image.save(image_path)
            else:
                image_path = None
        else:
            image_path = None

        # Check if the email or rollNo already exists
        existing_email = Student.query.filter_by(email=email).first()
        existing_student_id = Student.query.filter_by(student_id=student_id).first()

        if existing_email:
            flash('User with this email already exists. Please use a different email.', 'error')
        elif existing_student_id:
            flash('User with this student ID already exists. Please use a different student ID.', 'error')
        else:
            new_student = Student(name=name, email=email, semester=semester, student_id=student_id, student_image=image_path)
            db.session.add(new_student)
            db.session.commit()
            return redirect(url_for('userLogin'))
    return render_template('userRegister.html')


class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

@app.route('/admin')
def admin():
    # Check if admin is logged in
    if 'admin_id' in session:
        # Get the current admin from the database
        admin_id = session['admin_id']
        current_admin = Admin.query.get(admin_id)
        return render_template('admin.html', current_admin=current_admin)
    else:
        return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None  # Initialize error message
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        admin = Admin.query.filter_by(username=username).first()
        if admin and admin.password == password:
            session['admin_id'] = admin.id
            return redirect(url_for('admin'))
        else:
            if not admin:
                flash('Username not found. Please try again.')
            else:
                flash('Incorrect password. Please try again.')
    return render_template('login.html', error=error)


@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None  # Initialize error message
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        existing_admin = Admin.query.filter_by(username=username).first()
        if existing_admin:
            flash('Username already exists. Please choose a different one.')
        else:
            new_admin = Admin(username=username, password=password)
            db.session.add(new_admin)
            db.session.commit()
            return redirect(url_for('login'))
    return render_template('register.html', error=error)


@app.route('/logout', methods=['GET', 'POST'])
def logout():
    if request.method == 'POST' or request.method == 'GET':
        session.pop('admin_id', None)
        return render_template('logout_success.html')

@app.route('/logout/success')
def logout_success():
    return render_template('logout_success.html')

class Election(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    election_id = db.Column(db.String(100), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    ongoing = db.Column(db.Boolean, default=False)
    candidates = db.relationship('Candidate', backref='election', lazy=True)  

    def _init_(self, election_id, name):
        self.election_id = election_id
        self.name = name

class Candidate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    image_path = db.Column(db.String(200))
    votes = db.Column(db.Integer, default=0)
    election_id = db.Column(db.Integer, db.ForeignKey('election.id'), nullable=False)

@app.route('/index')
def index():
    candidates = Candidate.query.all()
    for candidate in candidates:
        if candidate.image_path:
            candidate.image_url = url_for('static', filename='images/' + os.path.basename(candidate.image_path))
        else:
            candidate.image_url = None
    return render_template('index.html', candidates=candidates)

@app.route('/vote', methods=['POST'])
def vote():
    if request.method == 'POST':
        candidate_id = request.form['candidate']
        candidate = Candidate.query.filter_by(id=candidate_id).first()
        if candidate:
            candidate.votes += 1
            db.session.commit()

            email = session.get('email')
            if email:
                user = Student.query.filter_by(email=email).first()
                if user:
                    user.has_voted = True
                    db.session.commit()
                    return redirect(url_for('userLogout'))
                else:
                    return "User not found"
            else:
                return redirect(url_for('userLogout'))
        else:
            return "Candidate not found"
    else:
        return "Method not allowed"

    
@app.route('/userLogout')
def userLogout():
    return render_template('userLogout.html' )

@app.route('/view_elections')
def view_elections():
    elections = Election.query.all()
    return render_template('view_elections.html', elections=elections)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}

@app.route('/add_candidates/<int:election_id>/<int:num_candidates>', methods=['GET', 'POST'])
def add_candidates(election_id, num_candidates):
    if request.method == 'GET':
        return render_template('add_candidates.html', election_id=election_id, num_candidates=num_candidates)
    elif request.method == 'POST':
        with app.app_context():
            for i in range(num_candidates):
                candidate_name = request.form[f'candidate_name_{i}']
                candidate_description = request.form[f'candidate_description_{i}']
                # Handle file upload
                candidate_image = request.files[f'candidate_image_{i}']
                if candidate_image and allowed_file(candidate_image.filename):
                    filename = secure_filename(candidate_image.filename)
                    image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    candidate_image.save(image_path)
                else:
                    image_path = None
                candidate = Candidate(name=candidate_name, description=candidate_description, image_path=image_path, election_id=election_id)
                db.session.add(candidate)
            db.session.commit()
            return redirect(url_for('admin'))
    
@app.route('/create_election', methods=['GET', 'POST'])
def create_election():
    if request.method == 'POST':
        election_name = request.form['election_name']
        election_id = request.form['election_id']
        num_candidates = int(request.form['num_candidates'])

        try:
            with app.app_context():
                new_election = Election(election_id=election_id, name=election_name)
                db.session.add(new_election)
                db.session.commit()
                db.session.refresh(new_election)
        except IntegrityError as e:
            db.session.rollback()
            return "Failed to create election. An election with the same ID already exists."
        return redirect(url_for('add_candidates', election_id=new_election.id, num_candidates=num_candidates))
    return render_template('create_election.html')

@app.route('/start_session/<int:election_id>')
def start_session(election_id):
    election = Election.query.get_or_404(election_id)
    if not election.ongoing:
        election.ongoing = True
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Voting session started'})
    else:
        return jsonify({'status': 'error', 'message': 'Voting session already ongoing'})

@app.route('/end_session/<int:election_id>')
def end_session(election_id):
    election = Election.query.get_or_404(election_id)
    if election.ongoing:
        election.ongoing = False
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Voting session ended'})
    else:
        return jsonify({'status': 'error', 'message': 'No ongoing voting session'})

@app.route('/view_candidates')
def view_candidates():
    candidates = Candidate.query.all()

    if not candidates:
        return render_template('no_candidates_found.html')
    
    candidates_with_images = []
    for candidate in candidates:
        if candidate.image_path:
            candidate_image_url = url_for('static', filename=candidate.image_path)
        else:
            candidate_image_url = None
        candidates_with_images.append({'candidate': candidate, 'image_url': candidate_image_url})
    return render_template('view_candidates.html', candidates=candidates)

@app.route('/update_candidate/<int:candidate_id>', methods=['GET', 'POST'])
def update_candidate(candidate_id):
    candidate = Candidate.query.get(candidate_id)
    if candidate:
        if request.method == 'GET':
            return render_template('update_candidate.html', candidate=candidate)
        elif request.method == 'POST':
            candidate.name = request.form['candidate_name']
            candidate.description = request.form['candidate_description']
            # Handle file upload
            candidate_image = request.files['candidate_image']
            if candidate_image and allowed_file(candidate_image.filename):
                filename = secure_filename(candidate_image.filename)
                image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                candidate_image.save(image_path)
                candidate.image_path = image_path
            db.session.commit()
            return redirect(url_for('view_candidates'))
    else:
        return "Candidate not found"

@app.route('/delete_candidate/<int:candidate_id>', methods=['POST'])
def delete_candidate(candidate_id):
    candidate = Candidate.query.get(candidate_id)
    if candidate:
        db.session.delete(candidate)
        db.session.commit()
    return redirect(url_for('view_candidates'))
       


@app.route('/result')
def result():
    candidates = Candidate.query.all()
    winner = None
    max_votes = 0
    for candidate in candidates:
        if candidate.image_path:
            candidate.image_url = url_for('static', filename='images/' + os.path.basename(candidate.image_path))
        else:
            candidate.image_url = None
        if candidate.votes > max_votes:
            max_votes = candidate.votes
            winner = candidate
    return render_template('result.html', candidates=candidates, winner=winner)



if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
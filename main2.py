from datetime import datetime
from flask import Flask, request, render_template, url_for, flash, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_required, login_user, logout_user, current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import os
import enum
from sqlalchemy import Enum as SqlEnum
from dotenv import load_dotenv

load_dotenv()

app= Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pomodoro.db'
app.config['SECRET_KEY'] = 'you-will-neve7-guess'
db = SQLAlchemy(app)
login_manager = LoginManager()

login_manager.init_app(app)

class SessionTypes(enum.Enum):
    pomodoro = "pomodoro"
    short_break = "short_break"
    long_break = "long_break"
    
class SessionStatus(enum.Enum):
    completed = "completed"
    skipped = "skipped"
    cancelled = "cancelled"
    

class Users(UserMixin, db.Model):
    
    __tablename__ = "users"
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True)
    name = db.Column(db.String(80))
    email = db.Column(db.String(120), unique=True)
    password = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    oauth_provider = db.Column(db.String(50))  # e.g., 'google'

    
    # Relationships:
    sessions = db.relationship("PomodoroSessions", backref="user", lazy=True)
    settings = db.relationship("UserSetting", backref="user", uselist=False)
    goals = db.relationship("UserGoals", backref="user", lazy=True)
    daily_stats = db.relationship("DailyStats", backref="user", lazy=True)
    
class PomodoroSessions(db.Model):
    
    __tablename__ = 'pomodoro_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    session_type = db.Column(SqlEnum(SessionTypes), nullable=False)
    status = db.Column(SqlEnum(SessionStatus), nullable=False, default=SessionStatus.completed)
    
    start_time = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    end_time = db.Column(db.DateTime)
    duration_minutes = db.Column(db.Integer)
    
    
class UserSetting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    pomodoro_duration = db.Column(db.Integer, default=25)
    short_break_duration = db.Column(db.Integer, default=5)
    long_break_duration = db.Column(db.Integer, default=15)
    
    auto_start_next = db.Column(db.Boolean, default=True)
    dark_mode = db.Column(db.Boolean, default=False)
    
    
class UserGoals(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    goal = db.Column(db.String(255), nullable=False)
    estimated_time = db.Column(db.Integer, nullable=False)
    completed = db.Column(db.Boolean, nullable=False, default=False)
    last_completed = db.Column(db.DateTime, default=datetime.utcnow)
    
    
class DailyStats(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    
    date = db.Column(db.DateTime, nullable=False)
    pomodoros_completed = db.Column(db.Integer, nullable=False, default=0)
    minutes_focused = db.Column(db.Integer, default=0)
    short_breaks_taken = db.Column(db.Integer, default=0)
    long_breaks_taken = db.Column(db.Integer, default=0)
    
    
# Models of the dataset are completed now working with the authentication.


@login_manager.user_loader
def user_loader(user_id):
    return Users.query.get(user_id)


@app.route('/')
def home_page():
    return render_template('index.html')



@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        username = request.form.get('username')
        password = request.form.get('password')
        user = Users.query.filter_by(username=username).first()
        
        if not user:
            flash("Sorry but the username does not exisits.", 'error')
            return redirect(url_for('login'))
        elif check_password_hash(user.password, password):
            user.last_login = datetime.utcnow()
            db.session.commit()
            login_user(user)
            return redirect(url_for('home_page'))
        else:
                flash("Incorrect password.", 'error')
                return redirect(url_for('login'))
        
    return render_template("login.html")

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form.get('name')
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirmed_password = request.form.get('confirm_password')
        
        existing_user = Users.query.filter_by(username=username).first()
        existing_email = Users.query.filter_by(email=email).first()
        if existing_user:
            flash("Username already registered, try changing the username.", 'error')
            return redirect(url_for('signup'))
        elif existing_email:
            flash("Email already registered, try logging in.", 'error')
            return redirect(url_for('login'))
        elif password != confirmed_password:
            flash("Sorry, make sure the passwords are the same in both fields.", 'error')
            return redirect(url_for('signup'))
        
        else:
            password = generate_password_hash(password, method='pbkdf2:sha256', salt_length=8)
            user = Users(
                name=name,
                username=username,
                email=email,
                password=password,
                last_login=datetime.utcnow()
            )
            try:
                db.session.add(user)
                db.session.commit()
                login_user(user)
                return redirect(url_for('timer'))
            except Exception as e:
                db.session.rollback()
                return f"Sorry we ran into this problem: {e}"

            
    return render_template('signup.html')

@app.route("/timer")
def timer():
    return render_template("timer.html", short_break_duration=5*60, long_break_duration=15*60, focus_session=1*10)

goals_number=0



@app.route("/goals1", methods=['GET', 'POST'])
@login_required
def goals1():
    if request.method == "POST":
        task = request.form.get('task')
        estimated_pomodoros = request.form.get('number')
        notes = request.form.get('notes')
        print(task, estimated_pomodoros, notes)
        new_task = UserGoals(
            user_id=current_user.id,
            goal=task,
            completed=False,
            estimated_time=estimated_pomodoros
        )
        db.session.add(new_task)
        try:
            db.session.commit()
            print("data has reached the database")
        except Exception as e:
            db.session.rollback()
            print(f"Sorry we ran into this problem: {e}")
    user_goals = UserGoals.query.filter_by(user_id=current_user.id).all()
    return render_template("goals1.html", goals=user_goals)

@app.route('/update_task_status', methods=['POST'])
@login_required
def update_task_status():
    data = request.get_json()
    goal_id = data.get('goal_id')
    status = data.get('status')
    goal = UserGoals.query.filter_by(id=goal_id, user_id=current_user.id).first()
    if goal:
        if status:
            goal.completed = True
        else:
            db.session.delete(goal)
        try:
            db.session.commit()
            return '', 200
        except Exception as e:
            db.session.rollback()
            return str(e), 500
    return 'Goal not found', 404


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        app.run(debug=True)

from datetime import datetime
from flask_login import UserMixin
from itsdangerous import URLSafeTimedSerializer as Serializer
from flask import current_app

# This will be set by the app
db = None
login_manager = None

def init_db(database, login_mgr):
    global db, login_manager
    db = database
    login_manager = login_mgr
    
    # Set up the user loader after login_manager is initialized
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

# Define models only after db is initialized
def create_models():
    global User, Lesson, Course
    
    class User(db.Model, UserMixin):
        id = db.Column(db.Integer, primary_key=True)
        fname = db.Column(db.String(25), nullable=False)
        lname = db.Column(db.String(25), nullable=False)
        username = db.Column(db.String(25), unique=True, nullable=False)
        email = db.Column(db.String(120), unique=True, nullable=False)
        password = db.Column(db.String(60), nullable=False)
        bio = db.Column(db.Text, nullable= True)
        image_file = db.Column(db.String(20), nullable=False, default='default.png')
        last_reset_token = db.Column(db.String(100), nullable=True)
        reset_attempts = db.Column(db.Integer, default=0)
        last_reset_attempt = db.Column(db.DateTime, nullable=True)
        is_admin = db.Column(db.Boolean, default=False, nullable=False)
        password_changed_at = db.Column(db.DateTime, nullable=True)
        last_login = db.Column(db.DateTime, nullable=True)
        lesson = db.relationship('Lesson', backref='author', lazy=True)
        
        def get_reset_token(self):
            s = Serializer(current_app.config['SECRET_KEY'])
            import time
            import secrets
            token = s.dumps({
                'user_id': self.id, 
                'timestamp': time.time(),
                'random': secrets.token_hex(8)
            }, salt='pw-reset')
            # Store the token to prevent reuse
            self.last_reset_token = token
            db.session.commit()
            return token
        @staticmethod
        def verify_reset_token(token, age=3600):
            s = Serializer(current_app.config['SECRET_KEY'])
            try:
                data = s.loads(token, salt='pw-reset', max_age=age)
            except:
                return None
            user_id = data.get('user_id') if isinstance(data, dict) else data
            user = User.query.get(user_id)
            
            # Check if token matches the last issued token (prevents reuse)
            if user and user.last_reset_token != token:
                return None
                
            return user

        def can_request_reset(self):
            """Check if user can request password reset (rate limiting)"""
            from datetime import datetime, timedelta
            
            # Handle None values from database
            if self.reset_attempts is None:
                self.reset_attempts = 0
                
            # If no previous attempts, allow
            if not self.last_reset_attempt:
                return True, None
                
            # If last attempt was more than 5 minutes ago, reset counter
            if self.last_reset_attempt < datetime.utcnow() - timedelta(minutes=5):
                self.reset_attempts = 0
                db.session.commit()
                return True, None
                
            # If less than 3 attempts in last 5 minutes, allow
            if self.reset_attempts < 3:
                return True, None
                
            # Calculate time until next attempt allowed
            next_attempt_time = self.last_reset_attempt + timedelta(minutes=5)
            remaining_time = next_attempt_time - datetime.utcnow()
            remaining_minutes = int(remaining_time.total_seconds() / 60) + 1
            
            return False, remaining_minutes

        def increment_reset_attempt(self):
            """Increment reset attempt counter"""
            from datetime import datetime
            
            # Handle None values from database
            if self.reset_attempts is None:
                self.reset_attempts = 0
            self.reset_attempts += 1
            self.last_reset_attempt = datetime.utcnow()
            db.session.commit()

        def __repr__(self):
            return f"User('{self.fname}', '{self.lname}', '{self.username}', '{self.email}', '{self.image_file}')"

    class Lesson(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        title = db.Column(db.String(100), nullable=False)
        date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
        content = db.Column(db.Text, nullable=False)
        thumbnail = db.Column(db.String(20), nullable=False, default='default.jpg')
        slug = db.Column(db.String(32), nullable=False)
        user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
        course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)

        def __repr__(self):
            return f"Lesson('{self.title}', '{self.date_posted}')"

    class Course(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        title = db.Column(db.String(50), unique=True, nullable=False)
        description = db.Column(db.String(150), nullable=False)
        icon = db.Column(db.String(20), nullable=False, default="default_course.jpg")
        lessons = db.relationship("Lesson", backref="course_name", lazy=True)

        def __repr__(self):
            return f"Course('{self.title}')"
    
    return User, Lesson, Course

# Initialize models as None initially
User = None
Lesson = None
Course = None
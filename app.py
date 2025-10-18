import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_ckeditor import CKEditor
from flask_mail import Mail
from config import Config

# Initialize extensions (without app context first)
db = SQLAlchemy()
migrate = Migrate()
bcrypt = Bcrypt()
login_manager = LoginManager()
ckeditor = CKEditor()
mail = Mail()

def create_app():
    # 1. Initialize app
    app = Flask(__name__, template_folder='raven/templates', static_folder='raven/static')
    app.config.from_object(Config)

    # 2. Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    ckeditor.init_app(app)
    mail.init_app(app)

    # 3. Login manager configs
    login_manager.login_view = 'users.login'
    login_manager.login_message_category = 'info'

    # 4. Import and initialize models
    from models import init_db, create_models
    init_db(db, login_manager)
    User, Lesson, Course = create_models()

    # 5. Import and register blueprints
    from main import main as main_bp
    from courses import courses as courses_bp
    from lessons import lessons as lessons_bp
    from users import users as users_bp
    from admin import admin as admin_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(courses_bp, url_prefix='/courses')
    app.register_blueprint(lessons_bp, url_prefix='/lessons')
    app.register_blueprint(users_bp, url_prefix='/users')
    app.register_blueprint(admin_bp)

    return app

# Create the app instance
app = create_app()

if __name__ == '__main__':
    app.run(debug=True, port=5000)

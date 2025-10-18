import os
import secrets
from PIL import Image
from flask import render_template, url_for, flash, redirect, request, abort
from sqlalchemy import or_
from .forms import RegistrationForm, LoginForm, UpdateProfileForm, RequestResetForm, ResetPasswordForm
from app import db, bcrypt, mail
from models import User, Lesson, Course
from flask_login import login_user, current_user, logout_user, login_required
from flask_mail import Message
from . import users


@users.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(
            fname=form.fname.data,
            lname=form.lname.data,
            username=form.username.data,
            email=form.email.data,
            password=hashed_password
        )
        db.session.add(user)
        db.session.commit()
        flash(f"Account created for {form.username.data} successfully", 'success')
        return redirect(url_for('users.login'))
    return render_template('register.html', title="Register", form=form)



@users.route("/login", methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            # Update last login time
            from datetime import datetime
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            login_user(user, remember=form.remember_me.data)
            next_page = request.args.get('next')
            flash('Login Successful!', 'success')
            return redirect(next_page) if next_page else redirect(url_for('main.home'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title="Login", form=form)


@users.route('/reset_password', methods=['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            # Check rate limiting
            can_reset, remaining_time = user.can_request_reset()
            if not can_reset:
                flash(f'Too many reset attempts. Please wait {remaining_time} minutes before trying again.', 'warning')
                return redirect(url_for('users.reset_request'))
            
            # Increment attempt counter
            user.increment_reset_attempt()
            send_reset_email(user)
        # Always show the same message to prevent email enumeration
        flash('If this account exists, you will receive an email with instructions.', 'info')
        return redirect(url_for('users.login'))
    return render_template('reset_password.html', title='Reset Password', form=form)



@users.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    user = User.verify_reset_token(token)
    if user is None:
        from app import app
        app.logger.info(f"Invalid token attempted: {token}")
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('users.reset_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user.password = hashed_password
        # Clear the reset token after successful use
        user.last_reset_token = None
        db.session.commit()
        flash('Your password has been updated! You can now log in.', 'success')
        return redirect(url_for('users.login'))
    return render_template('reset_token.html', title='Reset Password', form=form)



@users.route("/profile", methods=['GET', 'POST'])
@login_required
def profile():
    profile_form = UpdateProfileForm()

    # Delete User Photo
    if request.method == "POST" and "delete_picture" in request.form:
        current_user.image_file = "default.png"
        db.session.commit()
        flash("Your profile picture has been reset to default.", "info")
        return redirect(url_for("main.dashboard"))

    # Update profile
    if profile_form.validate_on_submit():
        if profile_form.picture.data:
            # delete old user picture if not default
            delete_if_not_default('static/user_pics', current_user.image_file, 'default.png')
            picture_file = save_picture(profile_form.picture.data, 'static/user_pics', output_size=(150,150))
            current_user.image_file = picture_file

        current_user.fname = profile_form.fname.data
        current_user.lname = profile_form.lname.data
        current_user.username = profile_form.username.data
        current_user.email = profile_form.email.data
        current_user.bio = profile_form.bio.data

        db.session.commit()
        flash('Your profile has been updated.', 'success')
        return redirect(url_for('users.profile'))

    elif request.method == 'GET':
        profile_form.fname.data = current_user.fname
        profile_form.lname.data = current_user.lname
        profile_form.username.data = current_user.username
        profile_form.email.data = current_user.email
        profile_form.bio.data = current_user.bio

    image_file = url_for('static', filename=f"user_pics/{current_user.image_file}")
    return render_template('profile.html', title="Profile", profile_form=profile_form, image_file=image_file, active_tab="profile")



@users.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('main.home'))



@users.route("/author/<int:author_id>")
def author(author_id: int):
    author_obj = User.query.get_or_404(author_id)
    # Courses authored: any course that has lessons by this user
    author_lessons = Lesson.query.filter_by(user_id=author_obj.id).all()
    course_ids = sorted({l.course_id for l in author_lessons})
    courses = Course.query.filter(Course.id.in_(course_ids)).all() if course_ids else []

    total_courses = len(courses)
    return render_template(
        "author.html",
        title=f"{author_obj.fname} {author_obj.lname}",
        author=author_obj,
        courses=courses,
        total_courses=total_courses
    )



# Save uploaded images with random names and optional resizing
def save_picture(form_picture, path, output_size=None):
    from app import app
    
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_name = random_hex + f_ext
    picture_path = os.path.join(app.root_path, path, picture_name)

    if f_ext.lower() == ".svg":
        form_picture.save(picture_path)
    else:
        i = Image.open(form_picture)
        if output_size:
            # Maintain aspect by fitting inside the box
            i.thumbnail(output_size)
        i.save(picture_path)

    return picture_name

# Delete old files if they're not the default ones
def delete_if_not_default(directory: str, filename: str, default_name: str) -> None:
    from app import app
    
    if not filename or filename == default_name:
        return
    try:
        os.remove(os.path.join(app.root_path, directory, filename))
    except FileNotFoundError:
        pass

# Send password reset email 
def send_reset_email(user):
    from app import app
    
    token = user.get_reset_token()
    reset_url = url_for('users.reset_token', token=token, _external=True)

    subject = "Password Reset Request"
    sender = app.config.get('MAIL_DEFAULT_SENDER') or app.config.get('MAIL_USERNAME') or 'noreply@example.com'
    msg = Message(subject=subject, recipients=[user.email], sender=sender)
    msg.body = (
        f"To reset your password, visit the following link:\n\n{reset_url}\n\n"
        "If you did not make this request then simply ignore this email and no changes will be made."
    )
    msg.html = (
        f"<p>To reset your password, click the link below:</p>"
        f"<p><a href=\"{reset_url}\">Reset Password</a></p>"
        f"<p>If you did not make this request then simply ignore this email and no changes will be made.</p>"
    )
    try:
        mail.send(msg)
    except Exception as e:
        # Log and fallback to printing the URL for development convenience
        app.logger.error(f"Failed to send reset email to {user.email}: {e}")
        app.logger.info(f"Password reset link for {user.email}: {reset_url}")


def send_reset_emali(user):
    # Backwards compatibility alias for send_reset_email
    return send_reset_email(user)

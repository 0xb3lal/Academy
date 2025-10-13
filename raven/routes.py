import os
import secrets
from PIL import Image
from flask import render_template, url_for, flash, redirect, request, abort
from sqlalchemy import or_
from raven.forms import RegistrationForm, LoginForm, UpdateProfileForm, NewLessonForm, NewCourseForm, RequestResetForm, ResetPasswordForm
from raven.models import User, Lesson, Course
from raven import app, db, bcrypt, mail
from flask_login import login_user, current_user, logout_user, login_required
from flask_mail import Message
# ------------------------
# Home route
# ------------------------

@app.route("/")
@app.route("/home")
def home():
    # Show up to 5 courses on home
    total_courses = Course.query.count()
    courses = Course.query.order_by(Course.id.asc()).limit(5).all()
    # One representative lesson per course (earliest lesson)
    lessons_unique = []
    for c in courses:
        first_lesson = (
            Lesson.query
            .filter_by(course_id=c.id)
            .order_by(Lesson.date_posted.asc(), Lesson.id.asc())
            .first()
        )
        if first_lesson:
            lessons_unique.append(first_lesson)
    return render_template('home.html', courses=courses, lessons=lessons_unique, css='home.css', total_courses=total_courses)


# ------------------------
# About route
# ------------------------

@app.route("/about")
def about():
    return render_template('about.html', title="About")


# ------------------------
# Register route
# ------------------------

@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
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
        return redirect(url_for('login'))
    return render_template('register.html', title="Register", form=form)


# ------------------------
# Login route
# ------------------------

@app.route("/login", methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember_me.data)
            next_page = request.args.get('next')
            flash('Login Successful!', 'success')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title="Login", form=form)


@app.route('/reset_password', methods=['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            # Check rate limiting
            can_reset, remaining_time = user.can_request_reset()
            if not can_reset:
                flash(f'Too many reset attempts. Please wait {remaining_time} minutes before trying again.', 'warning')
                return redirect(url_for('reset_request'))
            
            # Increment attempt counter
            user.increment_reset_attempt()
            send_reset_email(user)
        # Always show the same message to prevent email enumeration
        flash('If this account exists, you will receive an email with instructions.', 'info')
        return redirect(url_for('login'))
    return render_template('reset_password.html', title='Reset Password', form=form)


# ------------------------
# Password Reset: Set new password
# ------------------------

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    user = User.verify_reset_token(token)
    if user is None:
        app.logger.info(f"Invalid token attempted: {token}")
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('reset_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user.password = hashed_password
        # Clear the reset token after successful use
        user.last_reset_token = None
        db.session.commit()
        flash('Your password has been updated! You can now log in.', 'success')
        return redirect(url_for('login'))
    return render_template('reset_token.html', title='Reset Password', form=form)


# ------------------------
# Dashboard route
# ------------------------

@app.route("/dashboard", methods=['GET'])
@login_required
def dashboard():
    return render_template('dashboard.html', title="Dashboard", active_tab=None)


# ------------------------
# Profile route
# ------------------------

@app.route("/dashboard/profile", methods=['GET', 'POST'])
@login_required
def profile():
    profile_form = UpdateProfileForm()

    # Delete User Photo
    if request.method == "POST" and "delete_picture" in request.form:
        current_user.image_file = "default.png"
        db.session.commit()
        flash("Your profile picture has been reset to default.", "info")
        return redirect(url_for("dashboard"))

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
        return redirect(url_for('profile'))

    elif request.method == 'GET':
        profile_form.fname.data = current_user.fname
        profile_form.lname.data = current_user.lname
        profile_form.username.data = current_user.username
        profile_form.email.data = current_user.email
        profile_form.bio.data = current_user.bio

    image_file = url_for('static', filename=f"user_pics/{current_user.image_file}")
    return render_template('profile.html', title="Profile", profile_form=profile_form, image_file=image_file, active_tab="profile")


# ------------------------
# Logout route
# ------------------------

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))


# ------------------------
# New Course route
# ------------------------

@app.route("/dashboard/new_course", methods=["GET", "POST"])
@login_required
def new_course():
    form = NewCourseForm()

    if form.validate_on_submit():
        
        if form.icon.data:
            icon_file = save_picture(form.icon.data, "static/course_icons", output_size=(200, 200))
        else:
            icon_file = None

        course = Course(
            title=form.title.data,
            description=form.description.data,
            icon=icon_file if icon_file else Course.icon.default.arg
        )
        db.session.add(course)
        db.session.commit()
        flash("Course created successfully!", "success")
        return redirect(url_for("new_course"))

    return render_template(
        "new_course.html",
        title="Create New Course",
        form=form,
        active_tab="courses"
    )


# ------------------------
# New Lesson route
# ------------------------

@app.route("/dashboard/new_lesson", methods=["GET", "POST"])
@login_required
def new_lesson():
    new_lesson_form = NewLessonForm()
    new_lesson_form.course.choices = [(c.id, c.title) for c in Course.query.all()]  

    if new_lesson_form.validate_on_submit():
        thumbnail_file = None
        if new_lesson_form.thumbnail.data:
            thumbnail_file = save_picture(new_lesson_form.thumbnail.data, "static/lesson_thumbnails", output_size=(1280, 720))

        lesson = Lesson(
            title=new_lesson_form.title.data,
            slug=new_lesson_form.slug.data.replace(" ", "-"),
            content=new_lesson_form.content.data,
            thumbnail=thumbnail_file if thumbnail_file else Lesson.thumbnail.default.arg,
            course_id=new_lesson_form.course.data,  
            author=current_user
        )

        db.session.add(lesson)
        db.session.commit()
        flash("Your lesson has been created!", "success")
        return redirect(url_for("new_lesson"))

    return render_template(
        "new_lesson.html",
        title="New Lesson",
        new_lesson_form=new_lesson_form,
        active_tab="new_lesson"
    )


# ------------------------
# Lesson details route
# ------------------------

@app.route("/lesson/<string:lesson_slug>")
@login_required
def lesson(lesson_slug):
    lesson_obj = Lesson.query.filter_by(slug=lesson_slug).first()
    if not lesson_obj:
        abort(404)
    # Fetch all lessons for the same course in a stable order
    course_lessons = (
        Lesson.query
        .filter_by(course_id=lesson_obj.course_id)
        .order_by(Lesson.date_posted.asc(), Lesson.id.asc())
        .all()
    )

    # Determine current index and neighbors
    current_index = next((idx for idx, l in enumerate(course_lessons) if l.id == lesson_obj.id), None)
    prev_lesson = course_lessons[current_index - 1] if current_index is not None and current_index > 0 else None
    next_lesson = course_lessons[current_index + 1] if current_index is not None and current_index < len(course_lessons) - 1 else None

    return render_template(
        "lesson.html",
        title=lesson_obj.title,
        lesson=lesson_obj,
        course_lessons=course_lessons,
        current_index=current_index,
        prev_lesson=prev_lesson,
        next_lesson=next_lesson
    )


# ------------------------
# Course details route
# ------------------------

@app.route("/course/<string:course_title>")
@login_required
def course(course_title):
    course_obj = Course.query.filter_by(title=course_title).first()
    if not course_obj:
        abort(404)
    page = request.args.get("page", 1, type=int)
    lessons = (
        Lesson.query
        .filter_by(course_id=course_obj.id)
        .order_by(Lesson.date_posted.asc(), Lesson.id.asc())
        .paginate(page=page, per_page=6)
    )
    return render_template(
        "course.html",
        title=course_obj.title,
        course=course_obj,
        lessons=lessons
    )


# ------------------------
# Author profile route
# ------------------------

@app.route("/author/<int:author_id>")
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
# ------------------------
# Courses  route
# ------------------------

@app.route("/allcourses")
@login_required
def allcourses():
    page = request.args.get("page", 1, type=int)
    allcourses = Course.query.paginate(page=page, per_page=6)
    return render_template("all_courses.html", title="All Courses", courses=allcourses)

# ------------------------
# user lessons route
# ------------------------

@app.route("/dashboard/user_lessons", methods=["GET", "POST"])
@login_required
def user_lessons():
    page = request.args.get("page", 1, type=int)
    lessons = (
        Lesson.query
        .filter_by(user_id=current_user.id)
        .order_by(Lesson.date_posted.desc(), Lesson.id.desc())
        .paginate(page=page, per_page=6)
    )
    return render_template(
        "user_lessons.html", title="Your Lessons", active_tab="user_lessons", lessons=lessons
    )


# ------------------------
# Lesson edit/delete routes
# ------------------------

@app.route("/dashboard/lessons/<int:lesson_id>/edit", methods=["GET", "POST"])
@login_required
def edit_lesson(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)
    if lesson.author.id != current_user.id:
        abort(403)
    form = NewLessonForm()
    form.course.choices = [(c.id, c.title) for c in Course.query.all()]

    if request.method == 'GET':
        form.course.data = lesson.course_id
        form.title.data = lesson.title
        form.slug.data = lesson.slug
        form.content.data = lesson.content

    if form.validate_on_submit():
        if form.thumbnail.data:
            # delete old thumbnail if not default
            delete_if_not_default('static/lesson_thumbnails', lesson.thumbnail, Lesson.thumbnail.default.arg)
            thumbnail_file = save_picture(form.thumbnail.data, "static/lesson_thumbnails", output_size=(1280, 720))
            lesson.thumbnail = thumbnail_file
        lesson.title = form.title.data
        lesson.slug = form.slug.data.replace(" ", "-")
        lesson.content = form.content.data
        lesson.course_id = form.course.data
        db.session.commit()
        flash("Lesson updated successfully.", "success")
        return redirect(url_for('user_lessons'))

    return render_template('edit_lesson.html', title='Edit Lesson', form=form, lesson=lesson, active_tab='user_lessons')


@app.route("/dashboard/lessons/<int:lesson_id>/delete", methods=["POST"])
@login_required
def delete_lesson(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)
    if lesson.author.id != current_user.id:
        abort(403)
    # delete stored thumbnail if not default
    delete_if_not_default('static/lesson_thumbnails', lesson.thumbnail, Lesson.thumbnail.default.arg)
    db.session.delete(lesson)
    db.session.commit()
    flash("Lesson deleted.", "info")
    return redirect(url_for('user_lessons'))


# ------------------------
# Helper Functions
# ------------------------


# Save uploaded images with random names and optional resizing
def save_picture(form_picture, path, output_size=None):
    
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
    if not filename or filename == default_name:
        return
    try:
        os.remove(os.path.join(app.root_path, directory, filename))
    except FileNotFoundError:
        pass

# Send password reset email 

def send_reset_email(user):
    token = user.get_reset_token()
    reset_url = url_for('reset_token', token=token, _external=True)

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
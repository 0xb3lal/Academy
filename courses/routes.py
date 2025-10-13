import os
import secrets
from PIL import Image
from flask import render_template, url_for, flash, redirect, request, abort
from .forms import NewCourseForm
from app import db
from models import User, Lesson, Course
from flask_login import login_required, current_user
from . import courses

# ------------------------
# New Course route
# ------------------------

@courses.route("/new_course", methods=["GET", "POST"])
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
        return redirect(url_for("courses.new_course"))

    return render_template(
        "new_course.html",
        title="Create New Course",
        form=form,
        active_tab="courses"
    )


# ------------------------
# Course details route
# ------------------------

@courses.route("/course/<string:course_title>")
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
# Courses route
# ------------------------

@courses.route("/allcourses")
@login_required
def allcourses():
    page = request.args.get("page", 1, type=int)
    allcourses = Course.query.paginate(page=page, per_page=6)
    return render_template("all_courses.html", title="All Courses", courses=allcourses)


# ------------------------
# Helper Functions
# ------------------------

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

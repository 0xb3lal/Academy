import os
import secrets
from PIL import Image
from flask import render_template, url_for, flash, redirect, request, abort
from .forms import NewLessonForm
from app import db
from models import User, Lesson, Course
from flask_login import login_required, current_user
from . import lessons

# ------------------------
# New Lesson route
# ------------------------

@lessons.route("/new_lesson", methods=["GET", "POST"])
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
        return redirect(url_for("lessons.new_lesson"))

    return render_template(
        "new_lesson.html",
        title="New Lesson",
        new_lesson_form=new_lesson_form,
        active_tab="new_lesson"
    )


# ------------------------
# Lesson details route
# ------------------------

@lessons.route("/lesson/<string:lesson_slug>")
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
# user lessons route
# ------------------------

@lessons.route("/user_lessons", methods=["GET", "POST"])
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

@lessons.route("/lessons/<int:lesson_id>/edit", methods=["GET", "POST"])
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
        return redirect(url_for('lessons.user_lessons'))

    return render_template('edit_lesson.html', title='Edit Lesson', form=form, lesson=lesson, active_tab='user_lessons')


@lessons.route("/lessons/<int:lesson_id>/delete", methods=["POST"])
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
    return redirect(url_for('lessons.user_lessons'))


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

# Delete old files if they're not the default ones
def delete_if_not_default(directory: str, filename: str, default_name: str) -> None:
    from app import app
    
    if not filename or filename == default_name:
        return
    try:
        os.remove(os.path.join(app.root_path, directory, filename))
    except FileNotFoundError:
        pass

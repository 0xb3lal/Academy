from flask import render_template, url_for, redirect, request
from sqlalchemy import or_
from app import db
from models import User, Lesson, Course
from flask_login import login_required
from . import main

# ------------------------
# Home route
# ------------------------

@main.route("/")
@main.route("/home")
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

@main.route("/about")
def about():
    return render_template('about.html', title="About")


# ------------------------
# Dashboard route
# ------------------------

@main.route("/dashboard", methods=['GET'])
@login_required
def dashboard():
    return render_template('dashboard.html', title="Dashboard", active_tab=None)

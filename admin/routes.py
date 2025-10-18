from flask import render_template, url_for, flash, redirect, request, abort, jsonify
from flask_login import login_required, current_user
from sqlalchemy import func, desc
from datetime import datetime, timedelta
from . import admin
from .forms import AdminUserForm, AdminCourseForm, AdminLessonForm, AdminStatsForm
from app import db
from models import User, Lesson, Course

def admin_required(f):
    """Decorator to require admin access"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

@admin.route('/admin')
@login_required
@admin_required
def dashboard():
    """Admin Dashboard"""
    # Get statistics
    total_users = User.query.count()
    total_courses = Course.query.count()
    total_lessons = Lesson.query.count()
    total_admins = User.query.filter_by(is_admin=True).count()
    
    # Recent activity
    recent_users = User.query.order_by(desc(User.id)).limit(5).all()
    recent_lessons = Lesson.query.order_by(desc(Lesson.date_posted)).limit(5).all()
    recent_courses = Course.query.order_by(desc(Course.id)).limit(5).all()
    
    # User registration stats (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    new_users_30_days = User.query.filter(User.id >= 1).count()  # Simplified for demo
    
    stats = {
        'total_users': total_users,
        'total_courses': total_courses,
        'total_lessons': total_lessons,
        'total_admins': total_admins,
        'new_users_30_days': new_users_30_days
    }
    
    return render_template('admin/dashboard.html', 
                         stats=stats,
                         recent_users=recent_users,
                         recent_lessons=recent_lessons,
                         recent_courses=recent_courses)

@admin.route('/admin/users')
@login_required
@admin_required
def manage_users():
    """Manage Users"""
    page = request.args.get('page', 1, type=int)
    users = User.query.paginate(page=page, per_page=10, error_out=False)
    return render_template('admin/users.html', users=users)

@admin.route('/admin/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    """Edit User"""
    user = User.query.get_or_404(user_id)
    form = AdminUserForm(original_username=user.username, original_email=user.email)
    
    if form.validate_on_submit():
        user.fname = form.fname.data
        user.lname = form.lname.data
        user.username = form.username.data
        user.email = form.email.data
        user.bio = form.bio.data
        user.is_admin = form.is_admin.data
        
        # تحديث كلمة المرور إذا تم إدخالها
        if form.new_password.data:
            from app import bcrypt
            from datetime import datetime
            user.password = bcrypt.generate_password_hash(form.new_password.data).decode('utf-8')
            user.password_changed_at = datetime.utcnow()
            message = f'User {user.username} has been updated with new password!'
        else:
            message = f'User {user.username} has been updated!'
        
        db.session.commit()
        flash(message, 'success')
        return redirect(url_for('admin.manage_users'))
    
    elif request.method == 'GET':
        form.fname.data = user.fname
        form.lname.data = user.lname
        form.username.data = user.username
        form.email.data = user.email
        form.bio.data = user.bio
        form.is_admin.data = user.is_admin
    
    return render_template('admin/edit_user.html', form=form, user=user)

@admin.route('/admin/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    """Delete User"""
    user = User.query.get_or_404(user_id)
    
    # Prevent admin from deleting themselves
    if user.id == current_user.id:
        flash('You cannot delete your own account!', 'danger')
        return redirect(url_for('admin.manage_users'))
    
    # Delete user's lessons first
    Lesson.query.filter_by(user_id=user.id).delete()
    
    db.session.delete(user)
    db.session.commit()
    flash(f'User {user.username} has been deleted!', 'success')
    return redirect(url_for('admin.manage_users'))

@admin.route('/admin/users/<int:user_id>/reset_password', methods=['POST'])
@login_required
@admin_required
def reset_user_password(user_id):
    """Reset User Password"""
    user = User.query.get_or_404(user_id)
    
    # Generate new password hash
    from app import bcrypt
    from datetime import datetime
    new_password = "123456"  # Default password
    user.password = bcrypt.generate_password_hash(new_password).decode('utf-8')
    user.password_changed_at = datetime.utcnow()
    
    db.session.commit()
    flash(f'Password for user {user.username} has been reset to: {new_password}', 'success')
    return redirect(url_for('admin.manage_users'))

@admin.route('/admin/courses')
@login_required
@admin_required
def manage_courses():
    """Manage Courses"""
    page = request.args.get('page', 1, type=int)
    courses = Course.query.paginate(page=page, per_page=10, error_out=False)
    return render_template('admin/courses.html', courses=courses)

@admin.route('/admin/courses/<int:course_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_course(course_id):
    """Edit Course"""
    course = Course.query.get_or_404(course_id)
    form = AdminCourseForm()
    
    if form.validate_on_submit():
        course.title = form.title.data
        course.description = form.description.data
        course.icon = form.icon.data if form.icon.data else course.icon
        
        db.session.commit()
        flash(f'Course {course.title} has been updated!', 'success')
        return redirect(url_for('admin.manage_courses'))
    
    elif request.method == 'GET':
        form.title.data = course.title
        form.description.data = course.description
        form.icon.data = course.icon
    
    return render_template('admin/edit_course.html', form=form, course=course)

@admin.route('/admin/courses/<int:course_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_course(course_id):
    """Delete Course"""
    course = Course.query.get_or_404(course_id)
    
    # Delete all lessons in this course first
    Lesson.query.filter_by(course_id=course.id).delete()
    
    db.session.delete(course)
    db.session.commit()
    flash(f'Course {course.title} has been deleted!', 'success')
    return redirect(url_for('admin.manage_courses'))

@admin.route('/admin/lessons')
@login_required
@admin_required
def manage_lessons():
    """Manage Lessons"""
    page = request.args.get('page', 1, type=int)
    lessons = Lesson.query.paginate(page=page, per_page=10, error_out=False)
    return render_template('admin/lessons.html', lessons=lessons)

@admin.route('/admin/lessons/<int:lesson_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_lesson(lesson_id):
    """Edit Lesson"""
    lesson = Lesson.query.get_or_404(lesson_id)
    form = AdminLessonForm()
    
    if form.validate_on_submit():
        lesson.title = form.title.data
        lesson.content = form.content.data
        lesson.course_id = form.course_id.data
        
        db.session.commit()
        flash(f'Lesson {lesson.title} has been updated!', 'success')
        return redirect(url_for('admin.manage_lessons'))
    
    elif request.method == 'GET':
        form.title.data = lesson.title
        form.content.data = lesson.content
        form.course_id.data = lesson.course_id
    
    return render_template('admin/edit_lesson.html', form=form, lesson=lesson)

@admin.route('/admin/lessons/<int:lesson_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_lesson(lesson_id):
    """Delete Lesson"""
    lesson = Lesson.query.get_or_404(lesson_id)
    
    db.session.delete(lesson)
    db.session.commit()
    flash(f'Lesson {lesson.title} has been deleted!', 'success')
    return redirect(url_for('admin.manage_lessons'))

@admin.route('/admin/stats')
@login_required
@admin_required
def statistics():
    """Admin Statistics"""
    # User statistics
    total_users = User.query.count()
    admin_users = User.query.filter_by(is_admin=True).count()
    regular_users = total_users - admin_users
    
    # Content statistics
    total_courses = Course.query.count()
    total_lessons = Lesson.query.count()
    
    # Most active users (by lesson count)
    active_users = db.session.query(User, func.count(Lesson.id).label('lesson_count'))\
        .join(Lesson, User.id == Lesson.user_id)\
        .group_by(User.id)\
        .order_by(desc('lesson_count'))\
        .limit(10).all()
    
    # Course popularity
    popular_courses = db.session.query(Course, func.count(Lesson.id).label('lesson_count'))\
        .join(Lesson, Course.id == Lesson.course_id)\
        .group_by(Course.id)\
        .order_by(desc('lesson_count'))\
        .limit(10).all()
    
    stats = {
        'total_users': total_users,
        'admin_users': admin_users,
        'regular_users': regular_users,
        'total_courses': total_courses,
        'total_lessons': total_lessons
    }
    
    return render_template('admin/statistics.html', 
                         stats=stats,
                         active_users=active_users,
                         popular_courses=popular_courses)

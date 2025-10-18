from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, SelectField, BooleanField, IntegerField, PasswordField
from wtforms.validators import DataRequired, Length, Email, ValidationError, EqualTo, Optional
from models import User, Course, Lesson

class AdminUserForm(FlaskForm):
    fname = StringField('First Name', validators=[DataRequired(), Length(min=2, max=25)])
    lname = StringField('Last Name', validators=[DataRequired(), Length(min=2, max=25)])
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=25)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    bio = TextAreaField('Bio')
    is_admin = BooleanField('Admin Status')
    new_password = PasswordField('New Password (Optional)', validators=[Optional(), Length(min=6, max=60)])
    confirm_password = PasswordField('Confirm New Password', validators=[Optional(), EqualTo('new_password')])
    submit = SubmitField('Update User')

    def __init__(self, original_username=None, original_email=None, *args, **kwargs):
        super(AdminUserForm, self).__init__(*args, **kwargs)
        self.original_username = original_username
        self.original_email = original_email

    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=self.username.data).first()
            if user:
                raise ValidationError('Username already exists!')

    def validate_email(self, email):
        if email.data != self.original_email:
            user = User.query.filter_by(email=self.email.data).first()
            if user:
                raise ValidationError('Email already exists!')
    
    def validate_new_password(self, new_password):
        if new_password.data and len(new_password.data) < 6:
            raise ValidationError('Password must be at least 6 characters long.')
    
    def validate_confirm_password(self, confirm_password):
        if self.new_password.data and confirm_password.data != self.new_password.data:
            raise ValidationError('Passwords must match.')

class AdminCourseForm(FlaskForm):
    title = StringField('Course Title', validators=[DataRequired(), Length(min=2, max=50)])
    description = TextAreaField('Description', validators=[DataRequired(), Length(min=10, max=150)])
    icon = StringField('Icon Filename', validators=[Length(max=100)])
    submit = SubmitField('Update Course')

class AdminLessonForm(FlaskForm):
    title = StringField('Lesson Title', validators=[DataRequired(), Length(min=2, max=100)])
    content = TextAreaField('Content', validators=[DataRequired()])
    course_id = SelectField('Course', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Update Lesson')

    def __init__(self, *args, **kwargs):
        super(AdminLessonForm, self).__init__(*args, **kwargs)
        self.course_id.choices = [(course.id, course.title) for course in Course.query.all()]

class AdminStatsForm(FlaskForm):
    submit = SubmitField('Refresh Statistics')

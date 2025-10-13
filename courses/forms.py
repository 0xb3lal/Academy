from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length


# New Course Form
class NewCourseForm(FlaskForm):
    title = StringField("Course Name", validators=[DataRequired(), Length(max=50)])
    description = TextAreaField("Course Description", validators=[DataRequired(), Length(max=150)])
    icon = FileField("Icon", validators=[FileAllowed(["jpg", "png", "jpeg", "svg"], "Images only!")])
    submit = SubmitField("Create")

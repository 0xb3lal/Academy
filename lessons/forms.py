from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, SubmitField, SelectField
from wtforms.validators import DataRequired, Length
from flask_ckeditor import CKEditorField


# New Lesson Form 
class NewLessonForm(FlaskForm):
    course = SelectField("Course", coerce=int, validators=[DataRequired()])
    title = StringField("Lesson Title", validators=[DataRequired(), Length(max=100)])
    slug = StringField(
        "Lesson Slug",
        validators=[DataRequired(), Length(max=32)],
        render_kw={"placeholder": "Descriptive short version of your title. SEO friendly"}
    )
    content = CKEditorField("Lesson Content", validators=[DataRequired()])
    thumbnail = FileField("Thumbnail", validators=[FileAllowed(["jpg", "jpeg", "png", "svg"], "Images only!")])
    submit = SubmitField("Post")

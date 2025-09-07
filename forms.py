from flask_wtf import FlaskForm
from wtforms import HiddenField, SelectField, StringField, SubmitField
from wtforms.validators import URL, DataRequired, Optional


class AddServerForm(FlaskForm):
    url = StringField(
        "URL",
        validators=[DataRequired(), URL()],
        render_kw={
            "placeholder": "Enter URL...",
            "class": "form-control",
            "style": "max-width: 500px;",
        },
    )
    submit = SubmitField("Submit", render_kw={"class": "btn btn-default"})


class SearchForm(FlaskForm):
    q = StringField(
        "Search",
        validators=[Optional()],
        render_kw={
            "placeholder": "Enter Search...",
            "class": "form-control",
            "style": "max-width: 500px;",
        },
    )
    server_id = SelectField(
        "Server",
        choices=[("", "All Servers")],
        validators=[Optional()],
        coerce=str,
        render_kw={"class": "form-control", "style": "max-width: 300px;"},
    )
    service_type = SelectField(
        "Service Type",
        choices=[
            ("", "All Types"),
            ("MapServer", "Map Server"),
            ("FeatureServer", "Feature Server"),
        ],
        validators=[Optional()],
        render_kw={"class": "form-control", "style": "max-width: 300px;"},
    )
    submit = SubmitField("Search", render_kw={"class": "btn btn-default"})


class ServerActionForm(FlaskForm):
    action = HiddenField("Action", default="Spider Again")
    submit = SubmitField("Spider Again", render_kw={"class": "btn btn-primary"})

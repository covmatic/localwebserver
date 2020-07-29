from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms import SubmitField
from wtforms import SelectField
from flask_wtf.file import FileField, FileRequired
from wtforms.validators import DataRequired


class NewRunForm(FlaskForm):
    process_uuid = StringField('Process UUID', [DataRequired()])
    operator_id = StringField('Operator ID', [DataRequired()])
    supervisor_id = StringField('Supervisor ID', [DataRequired()])
    container_in = StringField('Input Container Barcode', [DataRequired()])
    container_out = StringField('Output Container Barcode', [DataRequired()])
    protocol_type = SelectField('Type', validators=[DataRequired()], coerce=int)
    submit = SubmitField('Submit')


class RunStatusForm(FlaskForm):
    process_uuid = StringField('Process UUID', [DataRequired()])
    submit = SubmitField('Submit')


class CreateProtocolType(FlaskForm):
    name = StringField('Protocol type name', [DataRequired()])
    module_name = StringField('Module name', [DataRequired()])
    filename = StringField('Module file name', [DataRequired()])
    checksum = StringField('SHA 256 sum of the imported module', [DataRequired()])
    #module = FileField('Module', validators=[FileRequired()])
    submit = SubmitField('Submit')

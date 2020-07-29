from database import session
from flask import Blueprint, jsonify
from flask import render_template
from forms.form_protocol_automation import NewRunForm
from forms.form_protocol_automation import RunStatusForm
from forms.form_protocol_automation import CreateProtocolType
from models.protocols import Protocol
from models.protocols import ProtocolType
from werkzeug.utils import secure_filename

bp_automation = Blueprint('automation', __name__)


def retrieve_protocol_types():
    protocol_types = list()
    for pt in ProtocolType.query.all():
        t = tuple([pt.id, pt.name])
        protocol_types.append(t)
    print(protocol_types)
    return protocol_types


@bp_automation.route('/automation', methods=['GET', 'POST'])
def execute_automation():
    message = ""
    form = NewRunForm()
    form.protocol_type.choices = retrieve_protocol_types()
    if form.validate_on_submit():
        try:
            protocol = Protocol(
                process_uuid=form.process_uuid.data,
                container_in=form.container_in.data,
                container_out=form.container_out.data,
                operator_id=form.operator_id.data,
                supervisor_id=form.supervisor_id.data,
                protocol_id=form.protocol_type.data
            )
            session.add(protocol)
            session.commit()
            message = "A new run has been scheduled for protocol. Process UUID: {}".format(form.process_uuid.data)
        except Exception as e:
            message = "Failed to schedule a run for protocol {} Process UUID: {}".format(
                form.protocol_type,
                form.process_uuid.data
            )
    else:
        print(form.errors)
    return render_template('automation_new.html', title="New Run", msg=message, form=form)


@bp_automation.route('/automation/status', methods=['GET', 'POST'])
def check_status():
    message = ""
    title = "Automation Status"
    form = RunStatusForm()
    if form.validate_on_submit():
        process_uuid = form.process_uuid.data
        protocol = Protocol.query.filter_by(process_uuid=process_uuid).first()
        if protocol:
            message = "Protocol {} of type {} belonging to Process UUID {} is {}".format(
                protocol.id,
                protocol.protocol_type.name,
                protocol.process_uuid,
                protocol.status
            )
            return render_template('automation_status.html', title=title, msg=message, form=form), 200
        else:
            message = "No protocol found for Process UUID {}".format(process_uuid)
            return render_template('automation_status.html', title=title, msg=message, form=form), 404
    else:
        print(form.errors)
    return render_template('automation_status.html', title=title, msg=message, form=form), 200


@bp_automation.route('/protocol_types', methods=['GET', 'POST'])
def create_new_protocol_type():
    message = ""
    title = "Create a new protocol type"
    form = CreateProtocolType()
    if form.validate_on_submit():
        try:
            protocol_type = ProtocolType(
                created_by="admin",
                name=form.name.data,
                filename=form.filename.data,
                module_name=form.module_name.data,
                checksum=form.checksum.data
            )
            session.add(protocol_type)
            session.commit()
            message = "Successfully created new Protocol Type \"{}\" ({})".format(
                protocol_type.name,
                protocol_type.filename
            )
        except Exception as e:
            message = "Failed to create new Protocol Type {}  - Error: {}".format(form.name.data, str(e))
    else:
        print(form.errors)
    return render_template('protocol_new.html', title=title, msg=message, form=form), 200


@bp_automation.route('/protocol_types/list', methods=['GET', 'POST'])
def list_protocol_type():
    title = "Protocol types"
    protocol_types = ProtocolType.query.all()
    protocol_types_list = list()
    for p in protocol_types:
        protocol_types_list.append(p.serialize())
    return render_template('protocol_list.html', title=title, protocol_types=protocol_types_list), 200

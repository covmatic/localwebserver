from database import session
from models.protocols import Protocol
from datetime import timedelta
from timeloop import Timeloop
from utils import secure_load_opentrons_module


app = object()
scheduler = Timeloop()


def start_scheduler(app_ctx):
    global app
    app = app_ctx
    scheduler.start(block=False)


@scheduler.job(interval=timedelta(seconds=5))
def check_new_tasks():
    print("Checking new tasks")
    protocol = Protocol.query.filter_by(status="queued").first()
    if protocol is not None:
        protocol.set_running()
        session.add(protocol)
        session.commit()
        try:
            # Call your code using execute_automation()
            # execute_automation()
            module = secure_load_opentrons_module(
                module_name=protocol.protocol_type.module_name,
                file_path=app.config["OT2_MODULES_PATH"],
                filename=protocol.protocol_type.filename,
                checksum=protocol.protocol_type.checksum,
                verify=False
            )
            otm = module.OpenTronsModule(
                usr=app.config["OT2_ROBOT_USER"],
                pwd=app.config["OT2_ROBOT_PASSWORD"],
                key_file=app.config["OT2_SSH_KEY"],
                target_ip=app.config["OT2_TARGET_IP_ADDRESS"],
                protocol_path=app.config["OT2_PROTOCOL_PATH"],
                protocol_file=app.config["OT2_PROTOCOL_FILE"],
                remote_path=app.config["OT2_REMOTE_LOG_FILEPATH"]
            )
            # Call your routine here
            otm.test_import()
            protocol.set_completed()
            session.add(protocol)
            session.commit()
        except Exception as e:
            protocol.set_failed()
            session.add(protocol)
            session.commit()
            print(e)

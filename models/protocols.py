from database import Base
from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import BigInteger
from sqlalchemy import String
from sqlalchemy import Boolean
from sqlalchemy import Float
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from utils import unix_epoch_now


class Protocol(Base):

    __tablename__ = 'protocols'
    id = Column(Integer, primary_key=True)
    process_uuid = Column(String, nullable=False)
    creation_date = Column(BigInteger, nullable=False, default=lambda: unix_epoch_now())
    last_update = Column(BigInteger, nullable=False, default=lambda: unix_epoch_now())
    end_date = Column(BigInteger, nullable=True)
    input_container_ids = Column(String, nullable=True)
    output_container_id = Column(String, nullable=True)
    status = Column(String, nullable=False, default='queued')
    lab_equipment = Column(String, nullable=True)
    avg_process_temp = Column(Float, nullable=True)
    operator_id = Column(String, nullable=True)
    supervisor_id = Column(Integer, nullable=True)
    success = Column(Boolean, nullable=True)
    protocol_type_id = Column(Integer, ForeignKey('protocol_types.id'))
    protocol_type = relationship('ProtocolType')

    def __init__(self, process_uuid, container_in, container_out, operator_id, supervisor_id, protocol_id):
        self.process_uuid = process_uuid
        self.operator_id = operator_id
        self.supervisor_id = supervisor_id
        self.input_container_ids = container_in
        self.output_container_id = container_out
        self.protocol_type_id = protocol_id

    def set_paused(self):
        self.set_status('paused')

    def set_running(self):
        self.set_status('running')

    def set_status(self, status):
        self.status = status
        self.last_update = unix_epoch_now()

    def set_completed(self):
        self.set_status('completed')
        self.success=True
        self.end_date = unix_epoch_now()

    def set_aborted(self):
        self.set_status('aborted')
        self.end_date = unix_epoch_now()
        self.success = False

    def set_failed(self):
        self.set_status('failed')
        self.success = False

    def set_avg_temp(self, temp):
        self.avg_process_temp = temp

    def serialize(self):
        return dict(
            id=self.id,
            process_uuid=self.process_uuid,
            operator_id=self.operator_id,
            supervisor_id=self.supervisor_id,
            creation_date=self.creation_date,
            last_update=self.last_update,
            container_in=self.input_container_ids,
            container_out=self.output_container_id,
            protocol_id=self.protocol_type_id,
            protocol=self.protocol_type.name,
            end_date=self.end_date,
            status=self.status,
            lab_equipment=self.lab_equipment,
            avg_run_temperature=self.avg_process_temp,
            success=self.success
        )


class ProtocolType(Base):

    __tablename__ = 'protocol_types'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    filename = Column(String, nullable=False)
    module_name = Column(String, nullable=False)
    checksum = Column(String, nullable=False)
    creation_date = Column(BigInteger, nullable=False, default=lambda: unix_epoch_now())
    last_update = Column(BigInteger, nullable=False, default=lambda: unix_epoch_now())
    created_by = Column(String, nullable=False)
    dismissed = Column(Boolean, nullable=False, default=False)

    def __init__(self, name, created_by, filename, module_name, checksum):
        self.name = name
        self.created_by = created_by
        self.module_name = module_name
        self.filename = filename
        self.checksum = checksum

    def serialize(self):
        return dict(
            id=self.id,
            name=self.name,
            created_by=self.created_by,
            creation_date=self.creation_date,
            last_update=self.last_update,
            filename=self.filename,
            module_name=self.module_name,
            checksum=self.checksum,
            dismissed=self.dismissed
        )

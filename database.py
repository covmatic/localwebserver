from flask import current_app
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy_repr import RepresentableBase

Session = sessionmaker(autocommit=False, autoflush=False)
session = scoped_session(Session)
Base = declarative_base(cls=RepresentableBase)
Base.query = session.query_property()


def init_db(app=current_app):
    engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'], convert_unicode=True)
    Session.configure(bind=engine)
    Base.metadata.create_all(bind=engine)
    app.teardown_request(teardown_session)


def teardown_session(exception=None):
    session.remove()

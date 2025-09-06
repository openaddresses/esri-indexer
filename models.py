from app import db

from sqlalchemy import func
from sqlalchemy.dialects.postgresql import JSON


class EsriServer(db.Model):
    __tablename__ = 'servers'

    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime(), default=func.now())
    updated_at = db.Column(db.DateTime(), onupdate=func.now())
    job_id = db.Column(db.String(), nullable=True)

    url = db.Column(db.String(), unique=True)
    status = db.Column(db.String(), default='added')
    last_crawled = db.Column(db.DateTime(), nullable=True)

    def __repr__(self):
        return '<EsriServer {}: {}>'.format(self.id, self.url)


class Service(db.Model):
    __tablename__ = 'services'

    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime(), default=func.now())
    server_id = db.Column(db.Integer, db.ForeignKey('servers.id'))

    service_data = db.Column(JSON())
    name = db.Column(db.String())
    service_type = db.Column(db.String())

    server = db.relationship(
        EsriServer,
        backref=db.backref(
            'services',
            lazy='dynamic',
            cascade='delete,all',
        )
    )


class Layer(db.Model):
    __tablename__ = 'layers'

    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime(), default=func.now())
    service_id = db.Column(db.Integer, db.ForeignKey('services.id'))

    layer_data = db.Column(JSON())
    name = db.Column(db.String())

    service = db.relationship(
        Service,
        backref=db.backref(
            'layers',
            lazy='dynamic',
            cascade='delete,all',
        )
    )

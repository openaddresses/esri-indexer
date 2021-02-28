import datetime
import os
from sqlalchemy.exc import IntegrityError
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask import Flask, flash, redirect, render_template, request, url_for

import redis
from rq import Queue
import requests

from urllib.parse import urlparse, urlunparse
from indexer import Indexer


app = Flask(__name__)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['REDIS_URL'] = os.environ.get('REDIS_URL', 'redis://localhost:6379')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'aohi49fjnorj')
db = SQLAlchemy(app)
migrate = Migrate(app, db)
redis_conn = redis.from_url(app.config['REDIS_URL'])
q = Queue(connection=redis_conn)

from models import EsriServer, Service, Layer


def index_esri_server(server_id):
    app.logger.info('Indexing ESRI server %s', server_id)
    server = EsriServer.query.get(server_id)

    if not server:
        app.logger.error('ESRI server %s was not found', server_id)
        return

    server.status = 'importing'
    db.session.add(server)
    db.session.commit()

    resulting_status = 'errored'
    try:
        indexer = Indexer(app.logger)
        services = indexer.spider_services(server.url)
        for service in services:
            service_details = indexer.get_service_details(service.get('url'))

            db_service = Service(
                server=server,
                name=service.get('name'),
                service_type=service.get('type'),
                service_data=service_details,
            )
            db.session.add(db_service)

            layers = service_details.get('layers', [])
            for layer in layers:
                db_layer = Layer(
                    service=db_service,
                    name=layer.get('name'),
                    layer_data=layer,
                )
                db.session.add(db_layer)
        resulting_status = 'imported'
    except requests.exceptions.RequestException:
        app.logger.exception('Problem indexing ESRI server %s', server_id)
    except ValueError:
        app.logger.exception('Problem indexing ESRI server %s', server_id)

    server.status = resulting_status
    server.job_id = None
    server.last_crawled = datetime.datetime.utcnow
    db.session.add(server)
    db.session.commit()


@app.route('/', methods=['GET', 'POST'])
def index():
    errors = []

    if request.method == 'POST':
        url = request.form['url']

        url_parts = urlparse(url)

        if url_parts.scheme not in ('http', 'https'):
            flash("That doesn't seem to be a valid URL", category="error")
            return redirect(url_for('index'))

        server = EsriServer(url=urlunparse(url_parts))
        db.session.add(server)
        try:
            db.session.commit()
        except IntegrityError:
            flash("That URL has already been added", category="error")
            return redirect(url_for('index'))

        job = q.enqueue_call(
            func='app.index_esri_server',
            args=(server.id,),
            result_ttl=5000,
        )

        server.status = 'queued'
        server.job_id = job.get_id()
        db.session.add(server)
        db.session.commit()

        flash("Queued the URL for crawling.", category="success")
        return redirect(url_for('index'))

    servers = EsriServer.query.paginate(page=int(request.args.get('page', 1)))

    return render_template('index.html', servers=servers)


@app.route('/servers/<int:server_id>', methods=['GET'])
def show_server(server_id):
    server = EsriServer.query.get_or_404(server_id)

    return render_template('show_server.html', server=server)


@app.route('/servers/<int:server_id>/services/<int:service_id>', methods=['GET'])
def show_service(server_id, service_id):
    server = EsriServer.query.get_or_404(server_id)
    service = Service.query.get_or_404(service_id)

    return render_template('show_service.html', server=server, service=service)


@app.route('/search', methods=['GET'])
def search():
    results = Layer.query \
        .filter(Layer.name.ilike('%{}%'.format(request.args.get('q'))))

    which_server = request.args.get('server_id')
    if which_server and which_server.isdigit():
        results = results.join(Service).filter(Service.server_id == int(which_server))

    page = request.args.get('page', 1)
    if not isinstance(page, int) and not page.isdigit():
        page = 1

    results = results.paginate(page=page)

    return render_template('show_search.html', results=results)


if __name__ == '__main__':
    app.run()

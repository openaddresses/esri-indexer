import os
from flask.ext.sqlalchemy import SQLAlchemy
from flask import Flask, render_template, request

from urlparse import urlparse
from indexer import get_services, get_service_details


app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('HEROKU_POSTGRESQL_VIOLET_URL')
db = SQLAlchemy(app)

from models import *


@app.route('/', methods=['GET', 'POST'])
def index():
    errors = []

    errored_url = None
    if request.method == 'POST':
        url = request.form['url']

        url_parts = urlparse(url)

        if url_parts.scheme not in ('http', 'https'):
            errors.append('That URL is not valid.')
            errored_url = url
        else:
            server = EsriServer(url=url)
            db.session.add(server)
            db.session.commit()

            services = get_services(url)
            for service in services:
                service_details = get_service_details(service.get('url'))

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
            db.session.commit()

    servers = EsriServer.query.paginate(page=int(request.args.get('page', 1)))

    return render_template('index.html', servers=servers, errors=errors, errored_url=errored_url)

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
    results = Layer.query.filter_by(name=request.args.get('q')).paginate(int(request.args.get('page', 1)))

    return render_template('show_search.html', results=results)

if __name__ == '__main__':
    app.run()

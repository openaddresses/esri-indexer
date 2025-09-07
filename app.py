import datetime
import os
from urllib.parse import urlparse, urlunparse

import redis
import requests
from flask import Flask, flash, redirect, render_template, request, url_for
from flask_wtf.csrf import CSRFProtect
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from rq import Queue
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from indexer import Indexer
from forms import AddServerForm, SearchForm, ServerActionForm

app = Flask(__name__)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["REDIS_URL"] = os.environ.get("REDIS_URL", "redis://localhost:6379")
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "aohi49fjnorj")
db = SQLAlchemy(app)
migrate = Migrate(app, db)
csrf = CSRFProtect(app)
redis_conn = redis.from_url(app.config["REDIS_URL"])
q = Queue(connection=redis_conn)


# Import models after db is defined to avoid circular imports
from models import EsriServer, Layer, Service


def index_esri_server(server_id):
    app.logger.info("Indexing ESRI server %s", server_id)
    server = EsriServer.query.get(server_id)

    if not server:
        app.logger.error("ESRI server %s was not found", server_id)
        return

    server.status = "importing"
    db.session.add(server)
    db.session.commit()

    resulting_status = "errored"
    try:
        indexer = Indexer(app.logger)
        services = indexer.spider_services(server.url)
        for service in services:
            service_url = service.get("url")
            try:
                service_details = indexer.get_service_details(service_url)
            except ValueError:
                app.logger.exception(
                    "Error getting details for service %s", service_url
                )
                continue

            db_service = Service.query.filter_by(
                server_id=server.id,
                name=service.get("name"),
                service_type=service.get("type"),
            ).first()

            if not db_service:
                db_service = Service(
                    server=server,
                    name=service.get("name"),
                    service_type=service.get("type"),
                )

            db_service.service_data = service_details
            db.session.add(db_service)
            db.session.flush()  # Flush to get the service ID

            layers = service_details.get("layers", [])
            for layer in layers:
                db_layer = Layer.query.filter_by(
                    service_id=db_service.id,
                    name=layer.get("name"),
                ).first()

                if not db_layer:
                    db_layer = Layer(
                        service=db_service,
                        name=layer.get("name"),
                    )

                db_layer.layer_data = layer
                db.session.add(db_layer)
        resulting_status = "imported"
    except requests.exceptions.RequestException:
        app.logger.exception("Problem indexing ESRI server %s", server_id)
    except ValueError:
        app.logger.exception("Problem indexing ESRI server %s", server_id)

    server.status = resulting_status
    server.job_id = None
    server.last_crawled = func.now()
    db.session.add(server)
    db.session.commit()


@app.route("/", methods=["GET", "POST"])
def index():
    form = AddServerForm()
    search_form = SearchForm()

    if form.validate_on_submit():
        url = form.url.data
        url_parts = urlparse(url)

        server = EsriServer(url=urlunparse(url_parts))
        db.session.add(server)
        try:
            db.session.commit()
        except IntegrityError:
            flash("That URL has already been added", category="error")
            return redirect(url_for("index"))

        job = q.enqueue_call(
            func="app.index_esri_server",
            args=(server.id,),
            result_ttl=5000,
        )

        server.status = "queued"
        server.job_id = job.get_id()
        db.session.add(server)
        db.session.commit()

        flash("Queued the server for crawling.", category="success")
        return redirect(url_for("index"))

    servers = EsriServer.query.paginate(page=int(request.args.get("page", 1)))

    return render_template("index.html", servers=servers, form=form, search_form=search_form)


@app.route("/servers/<int:server_id>", methods=["GET", "POST"])
def show_server(server_id):
    server = EsriServer.query.get_or_404(server_id)
    form = ServerActionForm()

    if form.validate_on_submit():
        if server.status not in ("errored", "imported"):
            flash("Can't re-crawl a server with state %s" % server.status)
            return redirect(url_for("index"))

        job = q.enqueue_call(
            func="app.index_esri_server",
            args=(server.id,),
            result_ttl=5000,
        )

        server.status = "queued"
        server.job_id = job.get_id()
        db.session.add(server)
        db.session.commit()

        flash("Queued the server for crawling.", category="success")
        return redirect(url_for("index"))

    return render_template("show_server.html", server=server, form=form)


@app.route("/servers/<int:server_id>/services/<int:service_id>", methods=["GET"])
def show_service(server_id, service_id):
    server = EsriServer.query.get_or_404(server_id)
    service = Service.query.get_or_404(service_id)

    return render_template("show_service.html", server=server, service=service)


@app.route("/search", methods=["GET"])
def search():
    form = SearchForm()

    # Populate server choices for the select field
    servers = EsriServer.query.all()
    form.server_id.choices = [('', 'All Servers')] + [(str(s.id), s.url) for s in servers]

    query = request.args.get("q", "")
    results = Layer.query.filter(Layer.name.ilike("%{}%".format(query)))

    which_server = request.args.get("server_id")
    if which_server and which_server.isdigit():
        results = results.join(Service).filter(Service.server_id == int(which_server))

    service_type = request.args.get("service_type")
    if service_type:
        results = results.join(Service).filter(Service.service_type == service_type)

    page = request.args.get("page", 1)
    if isinstance(page, str) and page.isdigit():
        page = int(page)
    elif not isinstance(page, int):
        page = 1

    results = results.paginate(page=page)

    # Pre-populate form with current search parameters
    form.q.data = query
    if which_server and which_server.isdigit():
        form.server_id.data = int(which_server)
    if service_type:
        form.service_type.data = service_type

    return render_template("show_search.html", results=results, form=form)


if __name__ == "__main__":
    app.run()

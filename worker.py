from rq import Connection, Queue, Worker

from app import app, redis_conn

listen = ["default"]


if __name__ == "__main__":
    with app.app_context():
        with Connection(redis_conn):
            worker = Worker(list(map(Queue, listen)))
            worker.work()

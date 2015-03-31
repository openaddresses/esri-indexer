from rq import Worker, Queue, Connection
from app import redis_conn, app

listen = ['default']


if __name__ == '__main__':
    with app.app_context():
        with Connection(redis_conn):
            worker = Worker(list(map(Queue, listen)))
            worker.work()

from datetime import datetime, timedelta
from pytz import utc
from sqlalchemy import asc
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_

from flask_config import Config

db = SQLAlchemy()
from data.order import Order, PROCESSING, QUEUED


def get_next_order_to_process() -> Order:
    # Find the next queued order and mark it as "Processing".
    # If an order has been in the "Processing" state for more than 10 minutes,
    # then assume something has gone wrong and retry it
    updated_row_ids = list(
        db.session.execute(
            """
    UPDATE [orders]
    SET status = 'Processing',
    date_processing = :currentTime,
    processed_by = :instanceId
    OUTPUT INSERTED.id
    WHERE id = (
        SELECT TOP 1 id
        FROM orders
        WHERE orders.status = 'Queued'
        OR (status = 'Processing' AND date_processing < DATEADD(minute, -10, :currentTime))
        ORDER BY orders.date_placed ASC
    )
    """,
            params={
                "currentTime": datetime.now(tz=utc),
                "instanceId": Config.INSTANCE_ID
            },
        )
    )
    if len(updated_row_ids) == 0:
        return None
    order_to_process = (
        db.session.query(Order)
        .filter(Order.id == updated_row_ids[0][0])  # There should be exactly one result
        .first()
    )
    db.session.commit()
    return order_to_process


def save_order(order):
    db.session.add(order)
    db.session.commit()


def get_all_orders():
    return db.session.query(Order).all()


def get_orders_to_display():
    return (
        db.session.query(Order)
        .filter(
            or_(Order.date_processed == None, Order.date_processed >= _display_cutoff())
        )
        .order_by(asc(Order.date_placed))
        .limit(20)
        .all()
    )


def get_queued_count():
    return db.session.query(Order).filter(or_(Order.status == QUEUED, Order.status == PROCESSING)).count()


def get_recently_processed_count():
    return (
        db.session.query(Order)
        .filter(Order.date_processed >= _display_cutoff())
        .count()
    )


def get_recently_placed_count():
    return (
        db.session.query(Order).filter(Order.date_placed >= _display_cutoff()).count()
    )


def _display_cutoff():
    return datetime.now(utc) - timedelta(minutes=10)


def add_order(product, customer, date_placed, date_processed, download):
    order = Order(product, customer, date_placed, date_processed, None, download, None, None)
    db.session.add(order)
    db.session.commit()
    return order


def add_orders(orders):
    db.session.bulk_save_objects(orders)
    db.session.commit()


def clear_orders():
    db.session.query(Order).delete()
    db.session.commit()


def count_orders():
    return db.session.query(Order).count()


def initialise_database(app):
    db.init_app(app)

    with app.app_context():
        db.create_all()  # creates table if not present

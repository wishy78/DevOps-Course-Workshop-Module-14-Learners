from datetime import datetime, timedelta
from pytz import utc
from sqlalchemy import asc
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_, and_
import logging

from flask_config import Config

db = SQLAlchemy()
from data.order import Order, PROCESSING, QUEUED, FAILED


def get_next_order_to_process() -> Order:
    # Find the next queued order and mark it as "Processing".
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
        ORDER BY orders.date_placed ASC
    )
    """,
            params={
                "currentTime": datetime.now(tz=utc),
                "instanceId": Config.INSTANCE_ID,
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


def requeue_stuck_orders():
    requeued_count =(
        db.session.query(Order)
        .filter(
            and_(
                Order.status == PROCESSING,
                # Orders that have been processing for 15 minutes
                # are assumed to be stuck
                Order.date_processing < datetime.now() - timedelta(minutes=15),
            )
        )
        .update({"failed_count": Order.failed_count + 1, "status": QUEUED})
    )
    db.session.commit()
    if requeued_count > 0:
        logging.info(f"Requeued {requeued_count} stuck orders")


def mark_retried_orders_as_failed():
    failed_count = (
        db.session.query(Order)
        .filter(and_(Order.status == QUEUED, Order.failed_count > 2))
        .update({"status": FAILED})
    )
    db.session.commit()
    if failed_count > 0:
        logging.info(f"Marked {failed_count} orders as failed")


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
    return (
        db.session.query(Order)
        .filter(or_(Order.status == QUEUED, Order.status == PROCESSING))
        .count()
    )


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
    order = Order(
        product, customer, date_placed, date_processed, None, download, None, None
    )
    db.session.add(order)
    db.session.commit()
    return order


def add_orders(orders):
    db.session.bulk_save_objects(orders)
    db.session.commit()


def clear_orders():
    db.session.execute("TRUNCATE TABLE [orders]")
    db.session.commit()


def count_orders():
    return db.session.query(Order).count()


def initialise_database(app):
    db.init_app(app)

    with app.app_context():
        db.create_all()  # creates table if not present

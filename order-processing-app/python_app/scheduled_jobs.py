import requests
from datetime import datetime
from PIL import Image
from pathlib import Path
from apscheduler.schedulers.background import BackgroundScheduler

from python_app.processing.process_image import process_image
from python_app.utils.timeit import time_it
from python_app.data.database import get_next_order_to_process, mark_retried_orders_as_failed, requeue_stuck_orders, save_order
from python_app.flask_config import Config


def initialise_scheduled_jobs(app):
    if (not Config.SCHEDULED_JOB_ENABLED):
        app.logger.warn("Scheduled job disabled")
        return
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        func=process_next_order,
        args=[app],
        trigger="interval",
        max_instances=app.config["SCHEDULED_JOB_MAX_INSTANCES"],
        seconds=app.config["SCHEDULED_JOB_INTERVAL_SECONDS"],
    )
    scheduler.start()


def process_next_order(app):
    with app.app_context():
        requeue_stuck_orders()
        mark_retried_orders_as_failed()
        order = get_next_order_to_process()
        if order == None:
            app.logger.warn(f"No orders to process")
            return

        app.logger.info(f"Processing order {order.id} at {str(datetime.now())}")

        try:
            process_order(order)
            app.logger.info(f"Successfully processed order {order.id}")
        except:
            app.logger.exception(f"Failed to process order {order.id}")
            order.mark_for_retry()
            save_order(order)


def process_order(order):
    image = load_img(order.image_url)

    (edginess, result_image) = process_image(image)
    save_image(result_image, str(order.image_id))
    order.edginess = edginess

    order.set_as_processed()
    save_order(order)

@time_it
def load_img(url) -> Image.Image:
    return Image.open(requests.get(url, stream=True).raw)

@time_it
def save_image(pic: Image.Image, name: str):
    dir_path = Path(Config.IMAGE_OUTPUT_FOLDER)
    dir_path.mkdir(exist_ok=True)
    pic.save(dir_path.joinpath(name + ".png"), "PNG")

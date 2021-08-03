from flask import Flask, render_template, request, send_from_directory
from datetime import datetime, timezone

from flask_config import Config
from data.database import initialise_database, add_order, clear_orders, count_orders, get_orders_to_display, get_queued_count, get_recently_placed_count, get_recently_processed_count
from scheduled_jobs import initialise_scheduled_jobs
from products import create_product_download
import requests
import logging

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
app.config.from_object(Config)

initialise_database(app)
initialise_scheduled_jobs(app)


@app.route("/")
def index():
    orders = get_orders_to_display()
    total_orders = count_orders()
    queue_count = get_queued_count()
    recently_placed_count = get_recently_placed_count()
    recently_processed_count = get_recently_processed_count()

    return render_template(
        "layout.html", orders=orders, queue_count=queue_count, recently_placed_count=recently_placed_count,
        recently_processed_count=recently_processed_count, total_count=total_orders,
        instance_id=app.config["INSTANCE_ID"]
    )

@app.route("/count")
def count():
    return { 'count': count_orders() }


@app.route("/new", methods=["POST"])
def new_order():
    product = request.json["product"]
    customer = request.json["customer"]
    date_placed = request.json["date_placed"] or datetime.now(tz=timezone.utc)
    date_processed = request.form.get("date_processed")
    download = create_product_download(product)

    try:
        order = add_order(product, customer, date_placed, date_processed, download)
    except Exception as e:
        return str(e)

    return f"Added: {order}"


@app.route('/output_images/<path:path>')
def send_js(path):
    response = send_from_directory(app.config["IMAGE_OUTPUT_FOLDER"], path)
    response.cache_control.max_age = 3600
    response.cache_control.no_cache = None
    return response

@app.route("/scenario", methods=["POST"])
def set_scenario():
    scenario = request.json["scenario"]

    response = requests.post(
        app.config["FINANCE_PACKAGE_URL"] + "/scenario",
        json=scenario
    )
    response.raise_for_status()

    return f"Set scenario to: {scenario}"



@app.route("/reset", methods=["POST"])
def reset_orders():
    rows = count_orders()
    clear_orders()
    return f"Deleted {rows} rows."


if __name__ == "__main__":
    app.run()

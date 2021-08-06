from sqlalchemy.dialects.mssql import DATETIMEOFFSET
from datetime import datetime
from pytz import utc, timezone
from pathlib import Path

from data.database import db
from flask_config import Config

local_timezone = timezone("Europe/London")

COMPLETE = "Complete"
QUEUED = "Queued"
FAILED = "Failed"
PROCESSING = "Processing"


class Order(db.Model):
    __tablename__ = "orders"
    id = db.Column(db.Integer, primary_key=True)
    product = db.Column(db.String(100), nullable=False)
    customer = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(100), nullable=False)
    date_processing = db.Column(DATETIMEOFFSET, nullable=True)
    date_placed = db.Column(DATETIMEOFFSET, nullable=False)
    date_processed = db.Column(DATETIMEOFFSET, nullable=True)
    processed_by = db.Column(db.String(100), nullable=True)
    download = db.Column(db.LargeBinary, nullable=True)
    edginess = db.Column(db.Integer, nullable=True)
    failed_count = db.Column(db.Integer, nullable=False, default=0)

    def __init__(
        self, product, customer, date_placed, date_processed, date_processing, download, edginess, processed_by
    ):
        self.product = product
        self.customer = customer
        self.date_placed = date_placed
        self.date_processed = date_processed
        self.date_processing = date_processing
        self.status = "Complete" if self.date_processed else "Queued"
        self.download = download
        self.edginess = edginess
        self.processed_by = processed_by

    def __repr__(self):
        return f"<Order {self.id}: {self.product}, {self.customer}, {self.date_placed}, {self.date_processed} >"

    @property
    def date_placed_local(self):
        return self.date_placed.astimezone(local_timezone)

    @property
    def date_processed_local(self):
        return self.date_processed.astimezone(local_timezone)

    @property
    def processing_duration_seconds(self):
        if self.date_processing == None:
            return None
        time_delta = (
            self.date_processed or datetime.now(tz=utc)
        ) - self.date_processing
        return time_delta.seconds

    @property
    def image_id(self):
        return (self.id % 1000) + 1

    @property
    def image_url(self):
        return f"https://m14workshopimages.blob.core.windows.net/m14images/{self.image_id}.jpg"

    @property
    def output_image_path(self):
        return f"/output_images/{self.image_id}.png"

    def mark_for_retry(self):
        self.status = QUEUED
        self.failed_count = self.failed_count + 1

    def set_as_processed(self):
        self.date_processed = datetime.now(tz=utc)
        self.status = COMPLETE

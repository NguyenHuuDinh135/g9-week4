"""AWS Lambda handler for Monitoring API."""

from mangum import Mangum

from monitoring_api import app

handler = Mangum(app, lifespan="off")

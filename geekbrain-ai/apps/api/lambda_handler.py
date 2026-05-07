"""AWS Lambda handler wrapping the FastAPI app via Mangum."""

from mangum import Mangum

from src.server import app

handler = Mangum(app, lifespan="off")

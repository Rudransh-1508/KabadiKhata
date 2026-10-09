"""AWS Lambda entry point: the same FastAPI app, behind API Gateway. Used by template.yaml."""

from mangum import Mangum

from api.app import app

handler = Mangum(app, lifespan="off")

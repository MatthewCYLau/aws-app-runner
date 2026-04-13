from fastapi import FastAPI
from api.config.database import Base, engine
from api.config.logging import setup_logging
from api.product.views import router as product_router

Base.metadata.create_all(bind=engine)


setup_logging()

app = FastAPI()

app.include_router(product_router)


@app.get("/")
def up():
    return "Up!"

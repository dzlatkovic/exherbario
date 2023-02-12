import uvicorn
from fastapi import FastAPI

from app.db import Base
from app.db.database import engine

from app.field_loc.routes import field_loc_router

Base.metadata.create_all(bind=engine)


def init_app():
    app = FastAPI()
    app.include_router(field_loc_router)
    return app


app = init_app()


@app.get("/", include_in_schema=False)
def hello_world():
    return {"message": "In Progress"}


if __name__ == "__main__":
    uvicorn.run(app)

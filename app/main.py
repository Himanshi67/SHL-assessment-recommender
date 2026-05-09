from fastapi import FastAPI
from app.routers.health import router as health_router
from app.routers.chat import router as chat_router
from fastapi.middleware.cors import CORSMiddleware
import logging

# Configure structured logging for the app
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("shl_recommender")
logger.setLevel(logging.DEBUG)

app = FastAPI(title="SHL Assessment Recommender")


@app.get("/")
def root():
    return {"message": "SHL Assessment Recommender is running"}


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins for testing
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(health_router)
app.include_router(chat_router)

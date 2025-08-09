from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from app.logging_config import setup_logging
from app.routes.keywords import router as keywords_router
from app.routes.mentions import router as mentions_router
from app.routes.scraping import router as scraping_router
from app.scheduler import start_scheduler, shutdown_scheduler


load_dotenv()
setup_logging()

app = FastAPI(title="Proactive Public Health Shield API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(keywords_router)
app.include_router(mentions_router)
app.include_router(scraping_router)


@app.get("/")
def root():
    return {"message": "Proactive Public Health Shield API running"}


@app.on_event("startup")
def on_startup():
    start_scheduler()


@app.on_event("shutdown")
def on_shutdown():
    shutdown_scheduler()



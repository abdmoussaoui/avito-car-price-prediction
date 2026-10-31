"""Entry point. Launch with uvicorn main:app --app-dir src."""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from api.routes import router
from models.loader import CONFIG
from models.predict import CarPricePredictor

@asynccontextmanager
async def lifespan(app: FastAPI):
    CONFIG["log_path"].parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(filename=CONFIG["log_path"], level=logging.INFO,
                        format="%(asctime)s - %(levelname)s - %(message)s")
    app.state.predictor = CarPricePredictor()
    yield
    app.state.predictor = None

app = FastAPI(title="AutoValeur · Car Price Prediction API", version="1.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True, allow_methods=["GET", "POST"], allow_headers=["Content-Type"],
)
app.include_router(router)

@app.exception_handler(RequestValidationError)
async def validation_error(request: Request, exc: RequestValidationError):
    errors = [{"loc": e["loc"], "msg": e["msg"], "type": e["type"]} for e in exc.errors()]
    return JSONResponse(status_code=422, content=jsonable_encoder({"detail": errors}))

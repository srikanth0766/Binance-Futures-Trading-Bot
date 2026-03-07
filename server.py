"""
server.py
~~~~~~~~~
Lightweight FastAPI wrapper around the existing trading bot modules.

Exposes a single POST /api/order endpoint that the React frontend calls.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import logging

from bot.config import load_settings
from bot.logging_config import setup_logging
from bot.validators import validate_all
from bot.client import BinanceClient
from bot.orders import OrderManager
from bot.exceptions import BinanceAPIError, TradingBotError

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    app.state.settings = load_settings()
    logger.info("FastAPI server started")
    yield
    logger.info("FastAPI server shutting down")


app = FastAPI(title="Trading Bot API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class OrderRequest(BaseModel):
    symbol: str
    side: str
    order_type: str
    quantity: float
    price: Optional[float] = None


@app.post("/api/order")
def place_order(order_req: OrderRequest):
    try:
        # Use string-based validators (they accept strings, so convert floats)
        params = validate_all(
            symbol=order_req.symbol,
            side=order_req.side,
            order_type=order_req.order_type,
            quantity=str(order_req.quantity),
            price=str(order_req.price) if order_req.price is not None else None,
        )

        client = BinanceClient(app.state.settings)
        manager = OrderManager(client)

        if params.order_type == "MARKET":
            result = manager.place_market_order(
                symbol=params.symbol,
                side=params.side,
                quantity=params.quantity,
            )
        else:
            result = manager.place_limit_order(
                symbol=params.symbol,
                side=params.side,
                quantity=params.quantity,
                price=params.price,  # type: ignore
            )

        return {"status": "success", "message": "Order placed successfully", "data": result}

    except BinanceAPIError as e:
        logger.error(f"Binance API Error: {e.code} - {e.msg}")
        raise HTTPException(status_code=400, detail=f"Binance Error ({e.code}): {e.msg}")
    except TradingBotError as e:
        logger.error(f"Bot Error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)

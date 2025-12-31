from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import json
import asyncio
import os
import sys

# Ensure project root is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.environment.negotiator_env import NegotiatorEnv
from src.agents.hybrid_agent import HybridAgent
from fastapi import Request
from fastapi.responses import JSONResponse
import logging
import time
import glob
from datetime import datetime
import numpy as np
import re
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Union, List

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("EquilibriumX")
security_logger = logging.getLogger("EquilibriumX.Security")

app = FastAPI(title="EquilibriumX API Gateway")

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global error: {exc}", exc_info=True)
    
    # In production, hide sensitive error details
    env = os.getenv("ENV", "development")
    if env == "production":
        return JSONResponse(
            status_code=500,
            content={"type": "error", "message": "Internal Server Error"},
        )
    else:
        return JSONResponse(
            status_code=500,
            content={"type": "error", "message": "Internal Server Error", "detail": str(exc)},
        )

# Security Headers Middleware
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' https://cdn.jsdelivr.net 'unsafe-inline'; "
            "style-src 'self' https://fonts.googleapis.com 'unsafe-inline'; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data:;"
        )
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response

app.add_middleware(SecurityHeadersMiddleware)

# Enable CORS with restrictions
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:8000,http://localhost:3000,http://127.0.0.1:8000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
)

class ConnectionManager:
    def __init__(self, max_connections: int = 100):
        self.active_connections: list[WebSocket] = []
        self.max_connections = max_connections

    async def connect(self, websocket: WebSocket):
        if len(self.active_connections) >= self.max_connections:
            await websocket.close(code=1008, reason="Server at capacity")
            security_logger.warning(f"Connection rejected: max capacity ({self.max_connections}) reached")
            return False
        await websocket.accept()
        self.active_connections.append(websocket)
        return True

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.warning(f"Failed to broadcast to connection: {e}")

manager = ConnectionManager()

# Mount static files (CSS, JS)
frontend_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")
app.mount("/static", StaticFiles(directory=frontend_path), name="static")

@app.get("/")
async def root():
    return FileResponse(os.path.join(frontend_path, "index.html"))

# --- Session Management ---
SESSIONS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "sessions")
os.makedirs(SESSIONS_DIR, exist_ok=True)

@app.get("/api/sessions")
async def list_sessions():
    files = glob.glob(os.path.join(SESSIONS_DIR, "*.json"))
    sessions = []
    for f in files:
        try:
            with open(f, "r") as jf:
                data = json.load(jf)
                sessions.append({
                    "id": data.get("id"),
                    "timestamp": data.get("timestamp"),
                    "rounds": len(data.get("turns", [])),
                    "result": "Deal" if data.get("deal_price") else "No Deal"
                })
        except (json.JSONDecodeError, KeyError, IOError) as e:
            logger.warning(f"Skipping malformed session file: {f} - {e}")
            continue
    # Sort by timestamp descending
    sessions.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    return sessions

@app.get("/api/sessions/{session_id}")
async def get_session(session_id: str, request: Request):
    # Security: Validate session_id format to prevent path traversal
    if not re.match(r'^session_\d+$', session_id):
        security_logger.warning(f"Invalid session ID attempted from {request.client.host}: {session_id}")
        return JSONResponse(status_code=400, content={"message": "Invalid session ID format"})
    
    file_path = os.path.join(SESSIONS_DIR, f"{session_id}.json")
    
    # Security: Verify the resolved path is within SESSIONS_DIR to prevent directory traversal
    if not os.path.abspath(file_path).startswith(os.path.abspath(SESSIONS_DIR)):
        security_logger.error(f"Path traversal attempt from {request.client.host}: {session_id}")
        return JSONResponse(status_code=403, content={"message": "Access denied"})
    
    if os.path.exists(file_path):
        security_logger.info(f"Session {session_id} accessed from {request.client.host}")
        with open(file_path, "r") as f:
            return json.load(f)
    return JSONResponse(status_code=404, content={"message": "Session not found"})

@app.websocket("/ws/negotiate")
async def websocket_negotiate(websocket: WebSocket):
    # Security: Check connection limit
    connected = await manager.connect(websocket)
    if not connected:
        return  # Connection rejected due to capacity
    
    try:
        # 1. Initialize logic
        num_items = 3
        env = NegotiatorEnv(config={"max_rounds": 10, "num_items": num_items})
        obs, info = env.reset()
        
        supplier = HybridAgent(role="Supplier", persona="aggressive", mock_llm=True)
        retailer = HybridAgent(role="Retailer", persona="cooperative", mock_llm=True)
        # Inject num_items for demo purpose
        supplier.num_items = num_items
        retailer.num_items = num_items
        
        agents = {"supplier": supplier, "retailer": retailer}
        
        manual_mode = False
        
        session_id = f"session_{int(time.time())}"
        session_data = {
            "id": session_id,
            "timestamp": datetime.now().isoformat(),
            "config": {"num_items": num_items, "max_rounds": env.max_rounds},
            "initial_state": {
                "val_s": env.val_s.tolist(),
                "val_r": env.val_r.tolist()
            },
            "turns": []
        }

        await websocket.send_json({
            "type": "init",
            "val_s": env.val_s.tolist(),
            "val_r": env.val_r.tolist(),
            "max_rounds": env.max_rounds,
            "num_items": num_items
        })

        # 2. Negotiation Loop
        done = False
        while not done:
            # Check for control messages from client
            try:
                control_msg = await asyncio.wait_for(websocket.receive_json(), timeout=0.1)
                if control_msg.get("type") == "toggle_manual":
                    manual_mode = control_msg.get("value", False)
                    await websocket.send_json({"type": "log", "message": f"Manual Mode: {'ON' if manual_mode else 'OFF'}"})
                elif control_msg.get("type") == "human_action" and manual_mode:
                    pass
            except asyncio.TimeoutError:
                pass

            proposer_id = env.current_proposer
            agent = agents[proposer_id]
            
            action_type = None
            prices = None
            message = ""

            if manual_mode:
                # Wait for human input
                await websocket.send_json({"type": "wait_for_human", "agent": proposer_id})
                human_data = await websocket.receive_json()
                if human_data.get("type") == "human_action":
                    action_type = int(human_data["action"])
                    # Support both single float and list for backward compatibility with current UI
                    raw_price = human_data.get("price", 0)
                    if isinstance(raw_price, (int, float)):
                        prices = np.array([raw_price] * num_items, dtype=np.float32)
                    else:
                        prices = np.array(raw_price, dtype=np.float32)
                    
                    message = human_data.get("message", "")
                    action_data = {"type": action_type, "price": prices}
                else:
                    action_data = agent.get_strategic_action(obs[proposer_id])
                    action_type = action_data["type"]
                    prices = action_data["price"]
            else:
                # RL Strategy
                action_data = agent.get_strategic_action(obs[proposer_id])
                action_type = action_data["type"]
                prices = action_data["price"]
                # LLM Message
                if action_type == 1:
                    message = await agent.speak(prices)
            
            # Step Env
            actions = {proposer_id: action_data}
            obs, rewards, terminations, truncations, infos = env.step(actions)
            
            # Use average price for the main chart, or first price?
            # Let's send the whole list to the frontend
            payload = {
                "type": "turn",
                "round": env.current_round,
                "agent": proposer_id,
                "action": ["ACCEPT", "COUNTER", "QUIT"][action_type],
                "price": prices.tolist() if isinstance(prices, np.ndarray) else prices,
                "message": message,
                "surplus": rewards
            }
            session_data["turns"].append(payload)
            await websocket.send_json(payload)
            
            # Switch turn history for agents
            other_id = "retailer" if proposer_id == "supplier" else "supplier"
            agents[other_id].update_history(prices)
            
            done = any(terminations.values()) or any(truncations.values())
            
            if not manual_mode:
                await asyncio.sleep(1.5)

        # 3. Final Result
        final_payload = {
            "type": "end",
            "deal_price": env.deal_prices.tolist() if env.deal_prices is not None else None,
            "final_rewards": rewards
        }
        session_data.update(final_payload)
        
        # Save Session
        with open(os.path.join(SESSIONS_DIR, f"{session_id}.json"), "w") as f:
            json.dump(session_data, f, indent=4)
            
        await websocket.send_json(final_payload)

    except WebSocketDisconnect:
        logger.info("Client disconnected normally.")
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"Error in WebSocket session: {e}", exc_info=True)
        try:
            await websocket.send_json({"type": "error", "message": "Session crashed", "detail": str(e)})
        except:
            pass
        manager.disconnect(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

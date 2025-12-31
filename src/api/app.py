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
from fastapi.responses import JSONResponse
from fastapi import Request
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("EquilibriumX")

app = FastAPI(title="EquilibriumX API Gateway")

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"type": "error", "message": "Internal Server Error", "detail": str(exc)},
    )

# Enable CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            await connection.send_json(message)

manager = ConnectionManager()

# Mount static files (CSS, JS)
frontend_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")
app.mount("/static", StaticFiles(directory=frontend_path), name="static")

@app.get("/")
async def root():
    return FileResponse(os.path.join(frontend_path, "index.html"))

@app.websocket("/ws/negotiate")
async def websocket_negotiate(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        # 1. Initialize logic
        env = NegotiatorEnv(config={"max_rounds": 10})
        obs, info = env.reset()
        
        supplier = HybridAgent(role="Supplier", persona="aggressive", mock_llm=True)
        retailer = HybridAgent(role="Retailer", persona="cooperative", mock_llm=True)
        agents = {"supplier": supplier, "retailer": retailer}
        
        manual_mode = False

        await websocket.send_json({
            "type": "init",
            "val_s": env.val_s,
            "val_r": env.val_r,
            "max_rounds": env.max_rounds
        })

        # 2. Negotiation Loop
        done = False
        while not done:
            # Check for control messages from client
            try:
                # Non-blocking check for control messages
                control_msg = await asyncio.wait_for(websocket.receive_json(), timeout=0.1)
                if control_msg.get("type") == "toggle_manual":
                    manual_mode = control_msg.get("value", False)
                    await websocket.send_json({"type": "log", "message": f"Manual Mode: {'ON' if manual_mode else 'OFF'}"})
                elif control_msg.get("type") == "human_action" and manual_mode:
                    # If we get a human action while in manual mode, we process it below
                    pass
            except asyncio.TimeoutError:
                pass

            proposer_id = env.current_proposer
            agent = agents[proposer_id]
            
            action_type = None
            price = None
            message = ""

            if manual_mode:
                # Wait for human input
                await websocket.send_json({"type": "wait_for_human", "agent": proposer_id})
                human_data = await websocket.receive_json()
                if human_data.get("type") == "human_action":
                    action_type = int(human_data["action"])
                    price = float(human_data["price"])
                    message = human_data.get("message", "")
                    action_data = {"type": action_type, "price": np.array([price], dtype=np.float32)}
                else:
                    # Fallback to AI if unexpected message
                    action_data = agent.get_strategic_action(obs[proposer_id])
                    action_type = action_data["type"]
                    price = float(action_data["price"][0])
            else:
                # RL Strategy
                action_data = agent.get_strategic_action(obs[proposer_id])
                action_type = action_data["type"]
                price = float(action_data["price"][0])
                # LLM Message
                if action_type == 1:
                    message = await agent.speak(price)
            
            # Step Env
            actions = {proposer_id: action_data}
            obs, rewards, terminations, truncations, infos = env.step(actions)
            
            # Update history for visualization
            rounded_price = round(price, 2)
            
            payload = {
                "type": "turn",
                "round": env.current_round,
                "agent": proposer_id,
                "action": ["ACCEPT", "COUNTER", "QUIT"][action_type],
                "price": rounded_price,
                "message": message,
                "surplus": rewards
            }
            await websocket.send_json(payload)
            
            # Switch turn history for agents
            other_id = "retailer" if proposer_id == "supplier" else "supplier"
            agents[other_id].update_history(price)
            
            done = any(terminations.values()) or any(truncations.values())
            
            # Artificial delay for frontend visualization (only in AI mode)
            if not manual_mode:
                await asyncio.sleep(1.5)

        # 3. Final Result
        await websocket.send_json({
            "type": "end",
            "deal_price": env.deal_price,
            "final_rewards": rewards
        })

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

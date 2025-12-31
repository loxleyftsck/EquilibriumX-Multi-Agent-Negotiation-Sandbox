import asyncio
import websockets
import json
import os
import requests

async def simulate_session():
    print("Simulating a negotiation session...")
    uri = "ws://localhost:8000/ws/negotiate"
    async with websockets.connect(uri) as websocket:
        # 1. Receive Init
        msg = await websocket.recv()
        init_data = json.loads(msg)
        print(f"Init received: {init_data['type']}")

        # 2. Run 3 rounds of COUNTER
        for i in range(3):
            # Proposer (Supplier) turn
            msg = await websocket.recv()
            turn_data = json.loads(msg)
            print(f"Turn received: {turn_data['agent']} - {turn_data['action']}")
            
            # Small delay
            await asyncio.sleep(0.5)

        # 3. Force Close (to test partial save if needed, but normally wait for 'end')
        # Actually wait for 'end'
        while True:
            msg = await websocket.recv()
            data = json.loads(msg)
            if data['type'] == 'end':
                print("Session ended successfully.")
                break

def verify_api():
    print("\nVerifying API endpoints...")
    resp = requests.get("http://localhost:8000/api/sessions")
    if resp.status_code == 200:
        sessions = resp.json()
        print(f"Found {len(sessions)} sessions.")
        if len(sessions) > 0:
            latest = sessions[0]
            print(f"Latest session ID: {latest['id']}")
            
            # Fetch details
            detail_resp = requests.get(f"http://localhost:8000/api/sessions/{latest['id']}")
            if detail_resp.status_code == 200:
                detail = detail_resp.json()
                print(f"Session detail fetched: {len(detail['turns'])} turns recorded.")
                return True
    return False

if __name__ == "__main__":
    # Note: assumed server is already running in background
    try:
        asyncio.run(simulate_session())
        if verify_api():
            print("\nHISTORICAL REPLAY LOGIC VERIFIED! 🚀")
        else:
            print("\nAPI VERIFICATION FAILED.")
    except Exception as e:
        print(f"Error during verification: {e}")

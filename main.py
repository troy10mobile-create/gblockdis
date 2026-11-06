from fastapi import FastAPI, HTTPException, Header, Depends
from pydantic import BaseModel, HttpUrl
from typing import Dict, List, Optional
from datetime import datetime, timedelta, timezone
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Blockchain Discovery Service", version="1.0.0")

# Configuration
NETWORK_SECRET = os.getenv("NETWORK_SECRET", "dev-secret-change-me")
PEER_TTL_SECONDS = 180          # Consider a peer dead after 3 minutes without heartbeat
MAX_PEERS_RETURNED = 20

# In-memory store (perfectly fine for this use case)
# Structure: { node_id: peer_info }
peers: Dict[str, dict] = {}


class RegisterRequest(BaseModel):
    node_id: str
    public_url: HttpUrl
    network_id: str = "mainnet"
    version: str = "1.0.0"


def verify_secret(x_network_secret: Optional[str] = Header(None)):
    """Optional shared secret. If NETWORK_SECRET is set, require it."""
    if NETWORK_SECRET and NETWORK_SECRET != "dev-secret-change-me":
        if x_network_secret != NETWORK_SECRET:
            raise HTTPException(status_code=401, detail="Invalid network secret")
    return True


def cleanup_dead_peers():
    """Remove peers that haven't been seen recently."""
    now = datetime.now(timezone.utc)
    dead = [
        node_id for node_id, info in peers.items()
        if now - info["last_seen"] > timedelta(seconds=PEER_TTL_SECONDS)
    ]
    for node_id in dead:
        del peers[node_id]


@app.get("/")
def root():
    return {
        "service": "Blockchain Discovery",
        "status": "running",
        "active_peers": len(peers)
    }


@app.post("/register", response_model=dict)
def register(req: RegisterRequest, _: bool = Depends(verify_secret)):
    """
    A node calls this on startup (and periodically as a heartbeat).
    """
    cleanup_dead_peers()

    now = datetime.now(timezone.utc)

    peers[req.node_id] = {
        "node_id": req.node_id,
        "public_url": str(req.public_url).rstrip("/"),
        "network_id": req.network_id,
        "version": req.version,
        "last_seen": now
    }

    # Return a list of other live peers (same network)
    other_peers = [
        {
            "node_id": info["node_id"],
            "public_url": info["public_url"],
            "version": info["version"]
        }
        for info in peers.values()
        if info["node_id"] != req.node_id
        and info["network_id"] == req.network_id
    ]

    # Limit how many we return
    other_peers = other_peers[:MAX_PEERS_RETURNED]

    return {
        "status": "registered",
        "your_node_id": req.node_id,
        "peers": other_peers,
        "total_peers_on_network": len(other_peers) + 1
    }


@app.get("/peers")
def list_peers(network_id: str = "mainnet", _: bool = Depends(verify_secret)):
    """Optional: just get the current peer list without registering."""
    cleanup_dead_peers()

    result = [
        {
            "node_id": info["node_id"],
            "public_url": info["public_url"],
            "version": info["version"],
            "last_seen": info["last_seen"].isoformat()
        }
        for info in peers.values()
        if info["network_id"] == network_id
    ]
    return {"peers": result, "count": len(result)}


@app.get("/health")
def health():
    return {"status": "ok", "active_peers": len(peers)}

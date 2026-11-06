# Blockchain Discovery Service

Tiny always-on service whose only job is introducing nodes to each other.

All consensus, validation, and blockchain data stay fully distributed among the nodes.

## Features

- Node registration + heartbeat
- Returns list of live peers on the same network
- Optional shared `NETWORK_SECRET` for private networks
- Automatic cleanup of dead peers
- Extremely small footprint (perfect for Render free tier)

## Quick Start (Local)

```bash
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env and set a strong NETWORK_SECRET

uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## Deploy to Render

1. Push this folder to a GitHub repository
2. Create a new **Web Service** on Render
3. Settings:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. Environment Variable:
   - `NETWORK_SECRET` = a long random string
5. Deploy → copy the public URL

That URL is the only thing every node needs (`DISCOVERY_URL`).

## API

### `POST /register`
Register (or heartbeat) a node and receive other live peers.

Headers (optional but recommended):
```
X-Network-Secret: your-secret
```

Body:
```json
{
  "node_id": "node-abc123",
  "public_url": "https://my-node.onrender.com",
  "network_id": "mainnet",
  "version": "1.0.0"
}
```

### `GET /peers?network_id=mainnet`
List current live peers (without registering).

### `GET /health`
Simple health check.

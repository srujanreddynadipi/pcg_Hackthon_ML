# 🚀 Deployment Guide

## Local Development

### 1. Setup Virtual Environment
```bash
cd itsm-ai-api
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the API
```bash
cd app
python main.py
```

**Output:**
```
🚀 Starting ITSM AI API...
📥 Loading models from HuggingFace...
📥 Downloading models from viveksai12/itsm-ticket-classifier...
✅ Downloaded: resolver_router.pkl
✅ Downloaded: tfidf_vectorizer.pkl
✅ Downloaded: category_encoder.pkl
✅ Downloaded: impact_encoder.pkl
✅ Downloaded: urgency_encoder.pkl
📥 Loading Sentence-BERT model: sentence-transformers/all-MiniLM-L6-v2...
✅ Sentence-BERT loaded
✅ All models loaded successfully!
🎯 API ready to receive requests
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

### 4. Test the API
Open a new terminal:
```bash
cd app
python test_api.py
```

### 5. Access Documentation
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health Check: http://localhost:8000/health

---

## Docker Deployment

### Build Image
```bash
docker build -t itsm-ai-api:latest .
```

### Run Container
```bash
docker run -d \
  --name itsm-api \
  -p 8000:8000 \
  --restart unless-stopped \
  itsm-ai-api:latest
```

### Check Logs
```bash
docker logs -f itsm-api
```

### Stop Container
```bash
docker stop itsm-api
docker rm itsm-api
```

---

## Production Deployment

### Option 1: Cloud Run (GCP)
```bash
# Build and push to Container Registry
gcloud builds submit --tag gcr.io/PROJECT_ID/itsm-ai-api

# Deploy to Cloud Run
gcloud run deploy itsm-ai-api \
  --image gcr.io/PROJECT_ID/itsm-ai-api \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --timeout 60s
```

### Option 2: AWS ECS
```bash
# Build and push to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com

docker build -t itsm-ai-api .
docker tag itsm-ai-api:latest ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/itsm-ai-api:latest
docker push ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/itsm-ai-api:latest

# Create ECS service (use AWS Console or CLI)
```

### Option 3: Azure Container Instances
```bash
# Build and push to ACR
az acr build --registry REGISTRY_NAME --image itsm-ai-api:latest .

# Deploy to ACI
az container create \
  --resource-group RESOURCE_GROUP \
  --name itsm-ai-api \
  --image REGISTRY_NAME.azurecr.io/itsm-ai-api:latest \
  --cpu 2 \
  --memory 4 \
  --port 8000 \
  --dns-name-label itsm-ai-api
```

### Option 4: Kubernetes
```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: itsm-ai-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: itsm-ai-api
  template:
    metadata:
      labels:
        app: itsm-ai-api
    spec:
      containers:
      - name: api
        image: itsm-ai-api:latest
        ports:
        - containerPort: 8000
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 60
          periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: itsm-ai-api-service
spec:
  selector:
    app: itsm-ai-api
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
```

Deploy:
```bash
kubectl apply -f deployment.yaml
```

---

## Environment Variables

Create `.env` file (optional):
```env
# HuggingFace
HUGGINGFACE_REPO=viveksai12/itsm-ticket-classifier

# API Settings
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4

# Performance
DUPLICATE_THRESHOLD=0.70
KB_TOP_K=3
```

---

## Performance Tuning

### Increase Workers (Production)
```bash
uvicorn app.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 4 \
  --timeout-keep-alive 60
```

### Add Rate Limiting
Install: `pip install slowapi`

Add to `main.py`:
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/predict")
@limiter.limit("60/minute")
async def predict_ticket(request: Request, ticket: TicketRequest):
    ...
```

### Add Caching (Redis)
Install: `pip install redis aioredis`

Cache model predictions for similar tickets.

---

## Monitoring

### Health Checks
```bash
# Basic health
curl http://localhost:8000/health

# Expected response
{
  "status": "healthy",
  "models_loaded": true,
  "predictor_ready": true,
  "rag_engine_ready": true,
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

### Prometheus Metrics (Optional)
Install: `pip install prometheus-fastapi-instrumentator`

Add to `main.py`:
```python
from prometheus_fastapi_instrumentator import Instrumentator

Instrumentator().instrument(app).expose(app)
```

Metrics available at: `/metrics`

---

## Troubleshooting

### Issue: Models not downloading
**Solution:** Check internet connection and HuggingFace access
```bash
pip install --upgrade huggingface-hub
```

### Issue: Out of memory
**Solution:** Increase Docker/container memory
```bash
docker run --memory="4g" itsm-ai-api
```

### Issue: Slow predictions
**Solution:** 
1. Use fewer historical tickets (limit to 100)
2. Reduce KB_TOP_K in settings.py
3. Add caching for frequent queries

### Issue: Port already in use
**Solution:** Change port
```bash
uvicorn app.main:app --port 8001
```

---

## Security Best Practices

1. **Add Authentication**
```python
from fastapi.security import HTTPBearer
security = HTTPBearer()

@app.post("/predict")
async def predict_ticket(
    request: TicketRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    # Verify token
    ...
```

2. **Enable HTTPS** (Production)
```bash
uvicorn app.main:app \
  --ssl-keyfile=key.pem \
  --ssl-certfile=cert.pem
```

3. **Configure CORS** (Production)
Update `main.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Specific domain
    allow_credentials=True,
    allow_methods=["POST"],
    allow_headers=["*"],
)
```

4. **Add Request Validation**
- Input sanitization
- Max request size limits
- Rate limiting per user/IP

---

## Backup & Recovery

### Model Backup
Models auto-download from HuggingFace - no local backup needed.

### Configuration Backup
```bash
# Backup settings
cp config/settings.py config/settings.backup.py

# Version control
git add config/settings.py
git commit -m "Update configuration"
```

---

## Scaling Strategy

### Horizontal Scaling
- Deploy multiple API instances behind load balancer
- Use Kubernetes/ECS for auto-scaling
- Each instance loads models independently

### Vertical Scaling
- Increase CPU/memory for faster predictions
- Recommended: 2 CPU cores, 4GB RAM per instance

### Database Integration (Optional)
Store predictions in database for analytics:
```python
# After prediction
await db.predictions.insert_one({
    "ticket_id": ticket_id,
    "predictions": predictions,
    "timestamp": datetime.now()
})
```

---

## Cost Optimization

### Free Tier Deployment
- **Render**: 750 hours/month free
- **Railway**: $5 credit/month
- **Fly.io**: 3 free VMs
- **Heroku**: Free dyno (limited hours)

### Optimize Model Loading
Cache models in memory (already implemented on startup).

### Reduce Dependencies
Remove unused packages from `requirements.txt`.

---

## Support & Debugging

### Enable Debug Mode
```bash
uvicorn app.main:app --reload --log-level debug
```

### Check Model Versions
```bash
pip list | grep -E "scikit-learn|sentence-transformers"
```

### Test Individual Components
```python
# Test model loading
from utils.model_loader import ModelLoader
loader = ModelLoader()
models = loader.download_models()
print("Models loaded:", list(models.keys()))

# Test prediction
from utils.predictor import TicketPredictor
predictor = TicketPredictor(models)
result = predictor.predict_category("VPN issue", "Cannot connect")
print("Category:", result['category'])
```

---

**For hackathon demo, use local deployment (fastest setup):**
```bash
pip install -r requirements.txt
cd app
python main.py
```

**Access API at:** http://localhost:8000/docs

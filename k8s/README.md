# ☸️ Kubernetes Deployment Templates

This folder contains standalone Kubernetes manifest templates for deploying
NextDNS Optimized Analytics to a Kubernetes cluster — **without** Helm.

They also serve as the reference implementation that mirrors the Helm chart
maintained in [consultant-portal-infra](https://github.com/BondIT-ApS/consultant-portal-infra/tree/main/charts/nextdns-analytics).

---

## 📂 Folder Contents

| File | Purpose |
|------|---------|
| `migration-job.yaml` | One-off Job that runs Alembic migrations (`python manage_db.py upgrade`) |
| `backend-deployment.yaml` | Backend API Deployment (FastAPI / uvicorn) |
| `worker-deployment.yaml` | Worker Deployment (scheduler / log fetcher) |
| `frontend-deployment.yaml` | Frontend Deployment (React / nginx) |
| `frontend-configmap.yaml` | Nginx ConfigMap — proxies `/api/` to backend service |
| `services.yaml` | ClusterIP Services for backend and frontend |
| `ingress.yaml` | Ingress with TLS via cert-manager |
| `secrets-template.yaml` | Template for the required application Secret |

---

## 🧱 Recommended: Helm Chart (Production)

For production deployments the **Helm chart** in
[consultant-portal-infra](https://github.com/BondIT-ApS/consultant-portal-infra)
is the recommended approach. It handles:

- Environment-specific values (dev / prod)
- Automatic image version tracking via ArgoCD Image Updater
- Secrets management integration
- Pre-upgrade migration hook (runs `migration-job.yaml` automatically)
- HPA autoscaling

```bash
# Deploy with Helm (from consultant-portal-infra repo)
helm upgrade --install nextdns-analytics charts/nextdns-analytics \
  -f charts/nextdns-analytics/values.yaml \
  -f environments/dev/nextdns-analytics-values.yaml \
  --namespace nextdns-analytics --create-namespace
```

---

## 🚀 Quick Start — Standalone (Without Helm)

Use these manifests when you want full control, are troubleshooting, or are
deploying to a cluster without Helm/ArgoCD.

### 1. Prerequisites

- `kubectl` configured against your target cluster
- A namespace: `kubectl create namespace nextdns-analytics`
- A Secret with required environment variables (see `secrets-template.yaml`)

### 2. Create the Secret

Edit `secrets-template.yaml` with your real values, then apply it. Or create
the secret directly (never commit files containing real credentials):

```bash
kubectl create secret generic nextdns-analytics-backend-env \
  --namespace nextdns-analytics \
  --from-literal=POSTGRES_USER=nextdns \
  --from-literal=POSTGRES_PASSWORD=changeme \
  --from-literal=POSTGRES_DB=nextdns \
  --from-literal=POSTGRES_HOST=your-db-host \
  --from-literal=POSTGRES_PORT=5432 \
  --from-literal=PGSSLMODE=require \
  --from-literal=API_KEY=your-nextdns-api-key \
  --from-literal=PROFILE_IDS=profile1,profile2 \
  --from-literal=LOCAL_API_KEY=your-local-api-key \
  --from-literal=LOG_LEVEL=info \
  --from-literal=FETCH_INTERVAL=60 \
  --from-literal=FETCH_LIMIT=1000 \
  --from-literal=AUTH_ENABLED=true \
  --from-literal=AUTH_USERNAME=admin \
  --from-literal=AUTH_PASSWORD=changeme \
  --from-literal=AUTH_SECRET_KEY=your-secret-key \
  --from-literal=AUTH_SESSION_TIMEOUT=3600 \
  --from-literal=ALLOWED_ORIGINS=https://your-domain.example.com
```

### 3. Run the Database Migration

Always run the migration Job **before** deploying the application:

```bash
# Edit the image tag in migration-job.yaml first, then:
kubectl apply -f k8s/migration-job.yaml
kubectl -n nextdns-analytics wait --for=condition=complete \
  job/nextdns-migration-manual --timeout=300s
kubectl -n nextdns-analytics logs job/nextdns-migration-manual
kubectl delete -f k8s/migration-job.yaml  # clean up
```

### 4. Deploy the Application

```bash
# Apply in order (ConfigMap before Deployment, migration before app)
kubectl apply -f k8s/frontend-configmap.yaml
kubectl apply -f k8s/services.yaml
kubectl apply -f k8s/backend-deployment.yaml
kubectl apply -f k8s/worker-deployment.yaml
kubectl apply -f k8s/frontend-deployment.yaml
kubectl apply -f k8s/ingress.yaml

# Verify
kubectl -n nextdns-analytics get pods
kubectl -n nextdns-analytics get ingress
```

### 5. Tear Down

```bash
kubectl delete -f k8s/ingress.yaml
kubectl delete -f k8s/frontend-deployment.yaml
kubectl delete -f k8s/worker-deployment.yaml
kubectl delete -f k8s/backend-deployment.yaml
kubectl delete -f k8s/services.yaml
kubectl delete -f k8s/frontend-configmap.yaml
```

---

## ⚙️ Customisation Guide

These are the values you **must** change before applying any manifest:

| Placeholder | Description | Example |
|-------------|-------------|---------|
| `<IMAGE_TAG>` | Docker image tag to deploy | `26.2.5` |
| `<YOUR_DOMAIN>` | Public hostname for the Ingress | `nextdns.example.com` |
| `<TLS_SECRET_NAME>` | Name of the TLS secret (cert-manager creates this) | `nextdns-tls` |

All other values (namespace, service names, resource limits) match the Helm
chart defaults and can be left as-is for a standard deployment.

---

## 🔗 Related Resources

- **Helm Chart**: [`consultant-portal-infra/charts/nextdns-analytics`](https://github.com/BondIT-ApS/consultant-portal-infra/tree/main/charts/nextdns-analytics)
- **Docker Hub Backend**: [`maboni82/nextdns-optimized-analytics-backend`](https://hub.docker.com/r/maboni82/nextdns-optimized-analytics-backend)
- **Docker Hub Frontend**: [`maboni82/nextdns-optimized-analytics-frontend`](https://hub.docker.com/r/maboni82/nextdns-optimized-analytics-frontend)
- **Full Documentation**: [`docs/`](../docs/README.md)

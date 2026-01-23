# Capricorn - AI Memory

**Purpose:** Context reload for AI when working on Capricorn project. No humans read this.

---

## DEPLOYMENT ARCHITECTURE

Capricorn has **4 deployment targets**:

| Environment | Location | Branch | URL | Deploy Method |
|-------------|----------|--------|-----|---------------|
| **DEV** | Workstation | local | http://localhost:5001 | Manual (./scripts/run-dev.sh) |
| **QA** | vm-kubernetes-1 | develop | http://192.168.1.180:5001 | Auto (GitLab CI/CD) |
| **PROD-Local** | vm-www-1 | production | https://cap.gothamtechnologies.com | Manual button (GitLab) |
| **PROD-GCP** | Google Cloud | production | https://capricorn.gothamtechnologies.com | Manual button (interviews only) |

---

## PROD-LOCAL CONFIGURATION (vm-www-1 @ 192.168.1.184)

**Infrastructure:** Home lab production server (Phase 7 - January 2026)

**Purpose:** Primary production deployment, replacing expensive GCP hosting (~$400/year savings)

### VM Specifications
- **Host:** vm-www-1 @ 192.168.1.184
- **RAM:** 8 GB | **CPU:** 8 cores | **Disk:** 50 GB (mirrored ZFS)
- **OS:** Ubuntu 24.04 Desktop
- **Reverse Proxy:** Traefik v3 (SSL termination, auto Let's Encrypt)
- **Public URL:** https://cap.gothamtechnologies.com
- **Internal URL:** https://192.168.1.184 (direct IP access from LAN)

### Docker Architecture

**CRITICAL:** Capricorn uses a **multi-network setup** for security:

```
web network (172.18.0.0/16) - Public-facing
├── traefik (172.18.0.5) - MUST be on both networks!
├── capricorn-frontend (172.18.0.4)
└── capricorn-backend (172.18.0.3)

capricorn_capricorn-network (172.19.0.0/16) - Internal
├── traefik (172.19.0.6) - Bridges to above network
├── capricorn-frontend (172.19.0.5)
├── capricorn-backend (172.19.0.4)
├── postgres (172.19.0.3) - NOT exposed to web network
└── redis (172.19.0.2) - NOT exposed to web network
```

**Why:** Postgres and Redis are isolated from public network for security.

### Deployment Location
- **Directory:** `/opt/capricorn/` on vm-www-1
- **docker-compose.yml:** Production config with Traefik labels
- **Images:** Pulled from GitLab Container Registry
- **Database:** Persistent volume + init scripts

### Traefik Routing

**Hostname-based (external access):**
- `cap.gothamtechnologies.com` → frontend (port 80)
- `cap.gothamtechnologies.com/api` → backend (port 8000)

**IP-based (internal LAN access):**
- `192.168.1.184` → frontend
- `192.168.1.184/api` → backend

### SSL Certificates
- **Provider:** Let's Encrypt (automatic via Traefik)
- **Method:** HTTP-01 challenge
- **Auto-renewal:** Every 60 days
- **Certificates:** cap.gothamtechnologies.com

### DNS Configuration
- **DDNS:** bullpup.ddns.net (NoIP, router-managed)
- **Route53:** cap.gothamtechnologies.com → CNAME → bullpup.ddns.net
- **Public IP:** 108.6.178.182 (Verizon, dynamic)

### GitLab CI/CD Integration

**Pipeline Stage:** `deploy_prod` (production branch has TWO manual deployment buttons)

**Job 1: `deploy_prod_local`** (PRIMARY - use this one!)
- SSH to vm-www-1 @ 192.168.1.184
- Login to GitLab Container Registry
- Pull latest images (frontend, backend)
- Run `docker compose up -d` in `/opt/capricorn/`
- Prune old images
- **Result:** Live at https://cap.gothamtechnologies.com (~2 minutes)

**Job 2: `deploy_prod_gcp`** (BACKUP - interviews only!)
- Deploys to Google Cloud Platform
- **Result:** Live at https://capricorn.gothamtechnologies.com (~10-15 minutes)
- **Note:** Only use when interview scheduled to save costs

**Required Variables:**
- `SSH_PRIVATE_KEY` - For local deployment access
- `CI_REGISTRY_PASSWORD` - For image pulls
- `GCP_SERVICE_ACCOUNT_KEY` - For GCP deployment

### Security
- **Proxmox Firewall:** SSH from 192.168.1.0/24 only, HTTP/HTTPS from anywhere
- **Router Port Forwarding:** 80, 443 → 192.168.1.184 (NO SSH)
- **Database Isolation:** Postgres/Redis not on web network

---

## GCP CONFIGURATION (Interview Demos Only)

**Purpose:** Keep GCP deployment available for interviews, but don't use as primary

**URL:** https://capricorn.gothamtechnologies.com (different from local!)
**Cost:** ~$30-45/month when running
**Usage:** Manual deploy only when interview scheduled (see Job 2 above)

---

## COMMON PITFALLS

### Issue: HTTPS Timeout (Gateway timeout)
**Cause:** Traefik not on capricorn network
**Solution:** Traefik MUST join both `web` and `capricorn_capricorn-network`
**Check:** `docker network inspect capricorn_capricorn-network | grep traefik`

### Issue: Database relation errors
**Cause:** Missing init scripts
**Solution:** Ensure `./database/init` mounted to postgres container

### Issue: Can't access from internal LAN
**Cause:** NAT hairpinning not supported by router
**Solution:** Add to `/etc/hosts`: `192.168.1.184 cap.gothamtechnologies.com`

### Issue: HTTPS Mixed Content Errors (API calls blocked)
**Symptoms:** Page loads but all API calls fail, browser console shows "Mixed Content" errors
**Cause:** Frontend tried to call `http://hostname:5002` from HTTPS page (browser security blocks this)
**Root Problem:** `frontend/src/config/api.ts` hardcoded HTTP protocol
**Solution:** Updated api.ts to auto-detect protocol:
- HTTPS page → use `https://hostname/api` (Traefik proxy route)
- HTTP page → use `http://hostname:5002` (direct backend port)
**Fixed in:** Commit `c83fe2f` (Jan 22, 2026)
**Result:** Single image now works for ALL environments (DEV/QA/PROD-Local/GCP)

---

## FRONTEND API CONFIGURATION

**File:** `frontend/src/config/api.ts`

**How It Works:**

The frontend auto-detects the correct API endpoint based on how it's accessed:

```typescript
Priority 1: VITE_API_URL environment variable (build-time)
  - Used for GCP deployment (different LoadBalancer IPs)
  - Set during Docker build: VITE_API_URL=<gcp-backend-url>

Priority 2: Protocol auto-detection (runtime)
  - HTTPS: uses https://${hostname}/api (Traefik proxy)
  - HTTP: uses http://${hostname}:5002 (direct backend)
```

**Environment Detection Logic:**

| Environment | Protocol | Detected API URL | Routing |
|-------------|----------|------------------|---------|
| DEV | HTTP (localhost:5001) | `http://localhost:5002` | Direct to backend |
| QA | HTTP (192.168.1.180:5001) | `http://192.168.1.180:5002` | Direct to backend |
| PROD-Local | HTTPS (cap.gothamtechnologies.com) | `https://cap.gothamtechnologies.com/api` | Via Traefik |
| PROD-GCP | HTTPS | Uses `VITE_API_URL` build var | GKE Ingress |

**Key Design Decision (Jan 22, 2026):**
- Initially tried separate docker-compose files + environment variables
- **Problem:** Vite env vars are build-time, not runtime
- **Solution:** Protocol auto-detection in source code
- **Benefit:** Single Docker image works for ALL 4 environments
- **Maintenance:** Zero ongoing work, automatic for future deployments

**Critical Code:**
```typescript
if (window.location.protocol === 'https:') {
  // PROD-Local / GCP without VITE_API_URL
  return `${window.location.protocol}//${window.location.host}`;
} else {
  // DEV / QA
  return `http://${window.location.hostname}:5002`;
}
```

---

## PROJECT INFORMATION

- **GitLab:** http://gitlab.gothamtechnologies.com/production/capricorn
- **GitHub:** https://github.com/fiberoptix/capricorn
- **Container Registry:** gitlab.gothamtechnologies.com:5050/production/capricorn
- **Local Path:** /home/agamache/DevShare/cursor-projects/unified_ui_DEV_PROD_GCP/capricorn

---

## DEVELOPMENT WORKFLOW

1. **Feature Development:** Work on `develop` branch locally (DEV)
2. **Testing:** Push to `develop` → auto-deploys to QA (.180)
3. **Production:** Merge to `production` → GitLab shows TWO manual buttons:
   - **Click `deploy_prod_local`** → deploys to vm-www-1 (.184) ← USE THIS ONE!
   - **Click `deploy_prod_gcp`** → deploys to GCP ← ONLY for interviews!
4. **Result:** Live at https://cap.gothamtechnologies.com (local) or https://capricorn.gothamtechnologies.com (GCP)

---

**Last Updated:** January 22, 2026

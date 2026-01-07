# GCP Data Persistence Fix

**Problem:** Demo data disappears after pod restarts because storage was ephemeral  
**Solution:** Use PersistentVolumeClaims (PVCs) to create real persistent disks in GCP

---

## 🔧 What Was Changed

### Files Updated:
1. **postgres-pvc.yaml** (NEW) - 10GB persistent disk for PostgreSQL
2. **redis-pvc.yaml** (NEW) - 1GB persistent disk for Redis  
3. **postgres.yaml** - Changed from `emptyDir` to `persistentVolumeClaim`
4. **redis.yaml** - Added volume mount using PVC
5. **run-gcp.sh** - Apply PVCs before deploying pods

### Before (Ephemeral):
```yaml
volumes:
- name: postgres-data
  emptyDir: {}  # ❌ Data lost on pod restart
```

### After (Persistent):
```yaml
volumes:
- name: postgres-data
  persistentVolumeClaim:
    claimName: postgres-pvc  # ✅ Data persists across restarts
```

---

## 🚀 How to Apply the Fix

### Option 1: Update Existing Deployment (Recommended)

```bash
cd /home/agamache/projects/unified_ui_2025.DEV_PROD_GCP/capricorn

# Apply the PVCs first
kubectl apply -f cloud/kubernetes/postgres-pvc.yaml
kubectl apply -f cloud/kubernetes/redis-pvc.yaml

# Wait for PVCs to be bound
kubectl get pvc -n capricorn -w
# Press Ctrl+C when both show STATUS: Bound

# Update the deployments to use PVCs
kubectl apply -f cloud/kubernetes/postgres.yaml
kubectl apply -f cloud/kubernetes/redis.yaml

# Restart the pods to pick up new volumes
kubectl rollout restart deployment/postgres -n capricorn
kubectl rollout restart deployment/redis -n capricorn

# Wait for rollout to complete
kubectl rollout status deployment/postgres -n capricorn
kubectl rollout status deployment/redis -n capricorn
```

**⚠️ WARNING:** This will create NEW empty volumes. You'll need to re-import your Demo Data after this update.

---

### Option 2: Full Rebuild (Clean Slate)

```bash
cd /home/agamache/projects/unified_ui_2025.DEV_PROD_GCP/capricorn

# Tear down everything
./scripts/run-gcp.sh nuke

# Deploy fresh with persistent volumes
./scripts/run-gcp.sh start
```

**Note:** This deletes the entire cluster and starts fresh. You'll need to re-import Demo Data.

---

## ✅ Verify Data Persistence

### 1. Check PVCs are created:
```bash
kubectl get pvc -n capricorn
```

Expected output:
```
NAME           STATUS   VOLUME                                     CAPACITY   ACCESS MODES
postgres-pvc   Bound    pvc-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx   10Gi       RWO
redis-pvc      Bound    pvc-yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyyy   1Gi        RWO
```

### 2. Check pods are using PVCs:
```bash
kubectl describe pod -l app=postgres -n capricorn | grep -A 5 "Volumes:"
```

Should show `Type: PersistentVolumeClaim` instead of `EmptyDir`

### 3. Import Demo Data:
- Go to: http://<frontend-ip>
- Navigate to **DATA** tab
- Click **Import Data**
- Select: `/home/agamache/projects/unified_ui_2025.DEV_PROD_GCP/capricorn/demo_UserData/Capricorn_DEMO_Data.json`
- Click **Import**

### 4. Test Persistence:
```bash
# Restart postgres pod
kubectl rollout restart deployment/postgres -n capricorn

# Wait for it to come back up
kubectl wait --for=condition=ready pod -l app=postgres -n capricorn --timeout=120s

# Check if data is still there (should NOT revert to bootstrap)
# Access frontend and verify Demo Data is still present
```

---

## 💰 Cost Impact

**New Costs:**
- PostgreSQL PVC: 10GB x $0.17/GB/month = **~$1.70/month**
- Redis PVC: 1GB x $0.17/GB/month = **~$0.17/month**

**Total additional cost: ~$1.87/month**

**Note:** These are GCP standard persistent disk prices. Your data will now survive:
- ✅ Pod restarts
- ✅ Node maintenance
- ✅ Cluster scaling
- ✅ GKE Autopilot optimizations
- ✅ Long periods of inactivity

---

## 🔍 Troubleshooting

### PVC stuck in "Pending"
```bash
kubectl describe pvc postgres-pvc -n capricorn
# Look for events at the bottom
```

Common causes:
- Insufficient quota (check GCP quotas)
- Wrong storage class (should be `standard-rwo`)
- Region mismatch

### Pod won't start after PVC change
```bash
kubectl logs -l app=postgres -n capricorn
kubectl describe pod -l app=postgres -n capricorn
```

Common causes:
- PVC not bound yet (wait longer)
- Permission issues (check pod security context)
- Data directory initialization issue (may need to delete PVC and recreate)

### Need to start completely fresh
```bash
# Delete PVCs (THIS DELETES ALL DATA!)
kubectl delete pvc postgres-pvc redis-pvc -n capricorn

# Delete deployments
kubectl delete deployment postgres redis -n capricorn

# Recreate PVCs
kubectl apply -f cloud/kubernetes/postgres-pvc.yaml
kubectl apply -f cloud/kubernetes/redis-pvc.yaml

# Wait for binding
kubectl get pvc -n capricorn -w

# Redeploy
kubectl apply -f cloud/kubernetes/postgres.yaml
kubectl apply -f cloud/kubernetes/redis.yaml
```

---

## 📊 Storage Details

### PostgreSQL Disk (10GB)
- **Path:** `/var/lib/postgresql/data`
- **Type:** GCP Persistent Disk (standard-rwo)
- **Contains:** All database tables, indexes, transaction logs
- **Backup:** Consider taking periodic snapshots via GCP Console

### Redis Disk (1GB)
- **Path:** `/data`
- **Type:** GCP Persistent Disk (standard-rwo)
- **Contains:** AOF (Append-Only File) for Redis persistence
- **Note:** Redis is primarily a cache, less critical than PostgreSQL

---

## 🎯 Summary

After applying this fix, your Capricorn GCP deployment will:
- ✅ Retain Demo Data across pod restarts
- ✅ Survive GKE node maintenance and optimization
- ✅ Work reliably for production use
- ✅ Cost only ~$2/month extra for persistent storage

**The days of waking up to lost data are over!** 🎉


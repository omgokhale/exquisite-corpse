# Complete Your Deployment - Final Steps

Your app is 95% deployed! Backend is live and healthy, but needs data configuration.

## Current Status
- ✅ Frontend on Vercel: https://exquisite-corpse-iota.vercel.app
- ✅ Backend on Render: https://exquisite-corpse-backend-mubr.onrender.com
- ✅ Health check passing: `{"status":"healthy"}`
- ⚠️ Generation failing: "No top segments available"

## What Went Wrong?
The backend can't find your artwork segments. Possible causes:
1. Data archive not extracted yet on Render
2. Data extracted to wrong location (nested `/data/data/` issue)
3. Database paths point to your local machine (`/Users/omgokhale/...`)

## How to Fix - 3 Easy Steps

### Step 1: Access Render Shell

Go to your Render dashboard:
- https://dashboard.render.com/
- Click on "exquisite-corpse-backend-mubr"
- Click "Shell" tab (or SSH in)

### Step 2: Run Diagnostic

In the Render shell, run:

```bash
python scripts/diagnose_deployment.py
```

This will tell you exactly what's wrong and what to do.

### Step 3: Follow the Recommendations

The diagnostic script will tell you to run one of these:

**Scenario A: Data not extracted yet**
```bash
python scripts/download_data.py
# Wait 5-10 minutes for 2.2GB download
python scripts/fix_database_paths.py
```

**Scenario B: Nested directory issue**
```bash
python scripts/fix_nested_data.py
python scripts/fix_database_paths.py
```

**Scenario C: Just path issue**
```bash
python scripts/fix_database_paths.py
```

### Step 4: Verify It Works

After running the fixes, test the API:

```bash
curl -X POST https://exquisite-corpse-backend-mubr.onrender.com/api/generate
```

You should get a JSON response with image URLs, not an error!

Then visit your frontend:
- https://exquisite-corpse-iota.vercel.app
- Click "Create"
- You should see a composite image! 🎉

---

## Troubleshooting

### "No such file: download_data.py"

Your scripts aren't in the deployed code. Push them:

```bash
# On your local machine
cd /Users/omgokhale/Desktop/Coding/Triad
git add backend/scripts/diagnose_deployment.py
git add backend/scripts/fix_nested_data.py
git add backend/scripts/fix_database_paths.py
git commit -m "Add deployment fix scripts"
git push
```

Render will auto-redeploy. Wait 2-3 minutes, then try again.

### "Module 'gdown' not found"

The download script installs it automatically. But if it fails:

```bash
pip install gdown
python scripts/download_data.py
```

### "Permission denied" or "Read-only file system"

You might be trying to write to `/app` instead of `/data`.

Check your Render environment variables:
- `DATA_DIR` should be `/data` (not `/app/data`)
- `INDEXES_DIR` should be `/data/indexes` (not `/app/indexes`)

Go to Render dashboard → Settings → Environment → verify these are set correctly.

### Still not working?

Check the Render logs:
- Dashboard → Logs tab
- Look for Python errors
- Common issues:
  - Database file not found
  - Image files not found
  - FAISS index files not found

All three files (DB, images, indexes) should be in `/data/`, not `/app/`.

---

## Alternative: Upload Data Directly via Render Dashboard

If the Google Drive download is too slow or failing:

### Option 1: Use Render's File Upload (if available)

Some Render plans allow direct file uploads to persistent disks.

### Option 2: Use a faster host

Upload `data.tar.gz` to:
- Dropbox
- AWS S3
- Any direct download link

Then update `backend/scripts/download_data.py` line 16:
```python
url = "YOUR_DIRECT_DOWNLOAD_URL"
```

Push the change, let Render redeploy, then run the script.

### Option 3: Split the archive

If 2.2GB is too large:

```bash
# On your local machine
cd /Users/omgokhale/Desktop/Coding/Triad
tar -czf data_part1.tar.gz data/raw_images/
tar -czf data_part2.tar.gz data/normalized_images/
tar -czf data_part3.tar.gz data/segment_previews/
tar -czf data_part4.tar.gz data/artworks.db
tar -czf data_part5.tar.gz indexes/
```

Upload each separately, then extract on Render.

---

## Expected Results After Fixing

Once the paths are fixed:

**Generation endpoint should return:**
```json
{
  "id": 123,
  "image_url": "https://exquisite-corpse-backend-mubr.onrender.com/outputs/gen_123.png",
  "top_segment": { "artwork_id": 456, ... },
  "middle_segment": { "artwork_id": 789, ... },
  "bottom_segment": { "artwork_id": 101, ... },
  "scores": { "tm_score": 0.85, "mb_score": 0.78, ... }
}
```

**Frontend should show:**
- Composite image displayed
- Sources button works
- Download button works
- Zoom/pan works
- "Create" generates new images quickly (<100ms)

---

## Performance Check

After deployment is working, monitor:

**Response times:**
- First request (cold start): May be slow if Render sleeps the service
- Subsequent requests: Should be <100ms
- If consistently slow, may need to upgrade Render tier

**Memory usage:**
- CLIP model: ~2GB in memory
- Render Starter (512MB): Might be tight
- If service crashes, upgrade to higher tier

**Check in Render dashboard:**
- Metrics tab
- Look for memory spikes or crashes
- Upgrade to 1GB+ if needed

---

## When Everything Works

Once you see composites generating successfully:

1. **Test the full flow:**
   - Generate 10+ composites
   - Check variety (different artworks each time)
   - Verify sources modal works
   - Test download functionality
   - Try zoom/pan

2. **Monitor for issues:**
   - Check Render logs for errors
   - Watch for memory issues
   - Verify image loading speed

3. **Share your app!**
   - Frontend URL: https://exquisite-corpse-iota.vercel.app
   - Should work on mobile and desktop
   - All 430 artworks from Met Museum available

---

## Quick Reference

**Render Backend:** https://exquisite-corpse-backend-mubr.onrender.com
**Vercel Frontend:** https://exquisite-corpse-iota.vercel.app

**Health check:** `curl https://exquisite-corpse-backend-mubr.onrender.com/health`
**Test generation:** `curl -X POST https://exquisite-corpse-backend-mubr.onrender.com/api/generate`

**Render shell access:**
1. Dashboard → Your service → Shell tab

**Most likely fix you need:**
```bash
python scripts/diagnose_deployment.py
python scripts/fix_database_paths.py
```

That's it! 🚀

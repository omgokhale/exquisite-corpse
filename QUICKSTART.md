# Quick Deployment to Vercel + Railway

## Step 1: Push to GitHub

```bash
cd /Users/omgokhale/Desktop/Coding/Triad
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/exquisite-corpse.git
git push -u origin main
```

## Step 2: Deploy Backend to Railway

1. Go to https://railway.app
2. Sign up/login
3. Click "New Project" → "Deploy from GitHub repo"
4. Select your `exquisite-corpse` repository
5. Railway will auto-detect and deploy

**Configure Railway:**
- Go to your service → Settings → Environment Variables
- Add: `CORS_ORIGINS` = `https://your-app.vercel.app` (you'll update this after Step 3)
- Go to Settings → Volumes → Add Volume
  - Mount path: `/app/data`
  - This persists your database and images

6. Copy your Railway URL (e.g., `https://exquisite-corpse-production.up.railway.app`)

## Step 3: Deploy Frontend to Vercel

1. Go to https://vercel.com
2. Sign up/login
3. Click "Add New" → "Project"
4. Import your GitHub repository
5. Configure:
   - **Framework Preset**: Vite
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build` (auto-detected)
   - **Output Directory**: `dist` (auto-detected)
6. Add environment variable:
   - Key: `VITE_API_URL`
   - Value: Your Railway URL from Step 2 (e.g., `https://exquisite-corpse-production.up.railway.app`)
7. Click "Deploy"

## Step 4: Update CORS

1. Go back to Railway
2. Update the `CORS_ORIGINS` environment variable with your Vercel URL
3. Example: `http://localhost:3000,https://your-app.vercel.app`
4. Railway will automatically redeploy

## Step 5: Test

Visit your Vercel URL and click "Create"!

---

## Troubleshooting

**"Failed to generate composite"**
- Check Railway logs for errors
- Ensure data directory and database exist
- May need to run setup scripts on Railway

**CORS errors**
- Verify `CORS_ORIGINS` includes your Vercel URL
- Check that `VITE_API_URL` is set correctly in Vercel

**Images not loading**
- Ensure Railway volume is mounted at `/app/data`
- Check that artworks were ingested (run scripts)

---

## Running Setup Scripts on Railway

If your database is empty, you need to run the setup scripts:

1. Go to Railway → Your Service → Settings
2. Click "Deploy" → "Custom Start Command"
3. Temporarily change to: `bash -c "cd backend && python scripts/1_fetch_met_objects.py --count 50 && python scripts/2_normalize_images.py && python scripts/3_generate_segments.py && python scripts/4_extract_features.py && python scripts/5_build_indexes.py && uvicorn app.main:app --host 0.0.0.0 --port $PORT"`
4. After setup completes, change back to: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

Or use Railway CLI:
```bash
railway run python scripts/1_fetch_met_objects.py --count 50
railway run python scripts/2_normalize_images.py
# etc...
```

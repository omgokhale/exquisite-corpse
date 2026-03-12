# Railway Build Error Fix

## The Problem
Railway is confused because you have both `frontend/` and `backend/` in the same repository.

## Solution: Set Root Directory

### Option A: Via Railway Dashboard (Easiest)

1. Go to your Railway project
2. Click on your service
3. Go to **Settings** → **General**
4. Scroll to **Root Directory**
5. Set it to: `backend`
6. Click **Save**
7. Redeploy (Railway will auto-redeploy)

### Option B: Deploy Backend Separately

If that doesn't work, create a separate GitHub repo just for the backend:

```bash
# Create a new directory
mkdir exquisite-corpse-backend
cd exquisite-corpse-backend

# Copy backend files
cp -r /Users/omgokhale/Desktop/Coding/Triad/backend/* .
cp -r /Users/omgokhale/Desktop/Coding/Triad/data .
cp -r /Users/omgokhale/Desktop/Coding/Triad/indexes .

# Initialize git
git init
git add .
git commit -m "Backend for Railway"

# Create a new GitHub repo called "exquisite-corpse-backend"
git remote add origin https://github.com/YOUR_USERNAME/exquisite-corpse-backend.git
git push -u origin main
```

Then deploy this separate repo to Railway.

## Additional Fixes

I've also created:
- `backend/nixpacks.toml` - Explicit build configuration
- `backend/runtime.txt` - Specifies Python version
- Updated `backend/railway.toml` - Better configuration

## If Still Failing

### Check Railway Logs

1. Go to your Railway service
2. Click **Deployments**
3. Click the failed deployment
4. Check the **Build Logs**
5. Copy the error message

### Common Errors & Fixes

**Error: "No Python version specified"**
→ Make sure `runtime.txt` exists in backend folder

**Error: "requirements.txt not found"**
→ Make sure Root Directory is set to `backend`

**Error: "Module 'app' not found"**
→ Check that all your Python files are in the backend folder

**Error: "Out of memory"**
→ Your free tier might not have enough RAM for CLIP model
→ Upgrade to Hobby plan ($5/month) for more memory

## Alternative: Deploy Without Data First

To test if Railway works at all, you can deploy without the heavy data:

1. In Railway Settings → Root Directory: `backend`
2. Let it deploy
3. It will fail when generating (no data), but you'll confirm the build works
4. Then add a volume and upload your data

## Need More Help?

Tell me:
1. What does the Railway build log say? (copy the error)
2. Did you set the Root Directory to `backend`?
3. What builder is Railway trying to use? (check the logs)

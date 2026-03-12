# Deployment Guide

This application consists of two parts:
1. **Frontend** (React + Vite) - Deploy to Vercel
2. **Backend** (FastAPI + Python) - Deploy to Railway, Render, or similar

## Part 1: Deploy Backend (Railway Recommended)

The backend has heavy dependencies (2GB CLIP model, FAISS indexes, SQLite, images) and needs persistent storage, so it cannot run on Vercel serverless functions.

### Option A: Deploy to Railway (Recommended)

1. **Create a Railway account** at https://railway.app

2. **Install Railway CLI** (optional but helpful):
   ```bash
   npm install -g @railway/cli
   ```

3. **Prepare the backend**:
   ```bash
   cd backend
   ```

4. **Create a `railway.toml` file** in the `backend` directory:
   ```toml
   [build]
   builder = "NIXPACKS"

   [deploy]
   startCommand = "uvicorn app.main:app --host 0.0.0.0 --port $PORT"

   [env]
   PYTHON_VERSION = "3.9"
   ```

5. **Create a `Procfile`** in the `backend` directory:
   ```
   web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```

6. **Push to GitHub**:
   - Create a new repository on GitHub
   - Push your entire project (including backend and data folders)

7. **Deploy on Railway**:
   - Go to https://railway.app/dashboard
   - Click "New Project" → "Deploy from GitHub repo"
   - Select your repository
   - Railway will auto-detect Python and deploy
   - Add a volume for persistent storage:
     - Go to your service → Variables
     - Mount volume at `/app/data` for images and database

8. **Get your backend URL**:
   - Railway will provide a URL like `https://your-app.railway.app`
   - Copy this URL for the frontend configuration

### Option B: Deploy to Render

1. Go to https://render.com
2. Create a new "Web Service"
3. Connect your GitHub repository
4. Configure:
   - **Root Directory**: `backend`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Add a persistent disk for `/app/data`

---

## Part 2: Deploy Frontend to Vercel

### Prerequisites
- Backend deployed and URL obtained
- Vercel account at https://vercel.com

### Steps

1. **Install Vercel CLI** (optional):
   ```bash
   npm install -g vercel
   ```

2. **Configure environment variables**:

   Create a `.env.production` file in the `frontend` directory:
   ```
   VITE_API_URL=https://your-backend.railway.app
   ```

   Replace `https://your-backend.railway.app` with your actual backend URL.

3. **Deploy via Vercel Dashboard** (easiest):

   a. Go to https://vercel.com/dashboard

   b. Click "Add New" → "Project"

   c. Import your GitHub repository

   d. Configure the project:
      - **Framework Preset**: Vite
      - **Root Directory**: `frontend`
      - **Build Command**: `npm run build`
      - **Output Directory**: `dist`

   e. Add environment variable:
      - Go to Settings → Environment Variables
      - Add `VITE_API_URL` = your backend URL

   f. Click "Deploy"

4. **Deploy via CLI** (alternative):
   ```bash
   cd frontend
   vercel --prod
   ```

   When prompted:
   - Set up new project: Yes
   - Link to existing project: No (first time)
   - Project name: exquisite-corpse
   - Directory: ./

   Then add the environment variable:
   ```bash
   vercel env add VITE_API_URL production
   # Paste your backend URL when prompted
   ```

---

## Part 3: Configure CORS on Backend

Update your backend to allow requests from your Vercel frontend URL.

Edit `backend/app/main.py`:

```python
from fastapi.middleware.cors import CORSMiddleware

# Add your Vercel URL here
origins = [
    "http://localhost:3000",
    "https://your-app.vercel.app",  # Add your Vercel URL
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

Redeploy the backend after this change.

---

## Verification

1. Visit your Vercel URL (e.g., `https://your-app.vercel.app`)
2. Click "Create" button
3. Verify that composites generate correctly
4. Check browser console for any CORS or API errors

---

## Troubleshooting

### Frontend can't reach backend
- Check that `VITE_API_URL` environment variable is set correctly in Vercel
- Verify CORS is configured on backend
- Check backend logs on Railway/Render

### Images not loading
- Ensure backend is serving static files from `/outputs`
- Check that data directory is persisted on Railway/Render
- Verify image URLs in API responses

### Backend out of memory
- Railway/Render free tiers have memory limits
- CLIP model uses ~2GB RAM
- Upgrade to a paid plan if needed

---

## Local Development

For local development, the setup remains the same:

**Terminal 1 - Backend**:
```bash
cd backend
source venv/bin/activate
python -m uvicorn app.main:app --reload
```

**Terminal 2 - Frontend**:
```bash
cd frontend
npm run dev
```

The Vite proxy will handle API requests locally.

---

## Notes

- **Database**: SQLite works for prototypes but consider PostgreSQL for production
- **Images**: Current setup stores images on filesystem. For production, consider object storage (S3, Cloudflare R2)
- **FAISS Indexes**: Ensure indexes are rebuilt on backend after deployment if data changes
- **Costs**: Railway free tier should work initially. Monitor usage and upgrade if needed.

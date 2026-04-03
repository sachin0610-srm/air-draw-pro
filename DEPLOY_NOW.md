# 🚀 Deployment Instructions - Railway + Vercel

## Prerequisites
- [x] Code ready
- [ ] GitHub account
- [ ] Railway account
- [ ] Vercel account

---

## Part 1: Push to GitHub (5 minutes)

### Step 1: Create GitHub Repository

1. Go to https://github.com/new
2. Repository name: `airdraw-pro-ai`
3. Description: `AI-powered air drawing with hand gesture recognition`
4. Public repository
5. **DO NOT** check "Add README" (we already have one)
6. Click **"Create repository"**

### Step 2: Push Your Code

Open your terminal and run:

```bash
cd "C:\Users\sachi\OneDrive\Desktop\Air Visual\airdraw"

# Initialize git
git init

# Add all files
git add .

# First commit
git commit -m "🎨 Initial release: AirDraw Pro AI"

# Add remote (replace YOUR-USERNAME with your GitHub username)
git remote add origin https://github.com/YOUR-USERNAME/airdraw-pro-ai.git

# Push to GitHub
git branch -M main
git push -u origin main
```

✅ Your code is now on GitHub!

---

## Part 2: Deploy Backend to Railway (3 minutes)

### Step 1: Create Railway Account

1. Go to https://railway.app
2. Click **"Login"**
3. Sign in with **GitHub**
4. Authorize Railway

### Step 2: Deploy Your API

1. Click **"New Project"**
2. Select **"Deploy from GitHub repo"**
3. Choose **"airdraw-pro-ai"**
4. Railway automatically:
   - Detects Python
   - Reads `Procfile`
   - Installs from `requirements.txt`
   - Starts uvicorn server
5. Wait 2-3 minutes for build...

### Step 3: Get Your API URL

1. Click on your deployed service
2. Go to **"Settings"** tab
3. Scroll to **"Domains"**
4. Click **"Generate Domain"**
5. Copy the URL (example: `https://airdraw-production.up.railway.app`)

✅ Your API is live!

### Step 4: Test Your API

Visit: `https://YOUR-APP.up.railway.app/health`

You should see:
```json
{
  "status": "ok",
  "service": "airdraw-api",
  "timestamp": 1234567890
}
```

---

## Part 3: Deploy Frontend to Vercel (2 minutes)

### Step 1: Create Vercel Account

1. Go to https://vercel.com
2. Click **"Sign Up"**
3. Sign up with **GitHub**
4. Authorize Vercel

### Step 2: Deploy Frontend

1. Click **"Add New..."** → **"Project"**
2. Import **"airdraw-pro-ai"** repository
3. Framework Preset: **Other**
4. Root Directory: `./` (leave as is)
5. Click **"Deploy"**
6. Wait 1-2 minutes...

✅ Your frontend is live!

Your URL will be: `https://airdraw-pro-ai.vercel.app`

---

## Part 4: Connect Frontend to Backend (1 minute)

### Update API URL in Frontend

1. Go back to your code
2. Open `index.html`
3. Find this line (around line 690):
   ```javascript
   const API_BASE = 'http://localhost:8000';
   ```

4. Change it to your Railway URL:
   ```javascript
   const API_BASE = 'https://YOUR-APP.up.railway.app';
   ```

5. Save the file

6. Push the update:
   ```bash
   git add index.html
   git commit -m "🔗 Connect frontend to Railway backend"
   git push
   ```

Vercel will **automatically redeploy** in 30 seconds!

---

## 🎉 YOU'RE LIVE!

### Your URLs:
- **Frontend:** `https://airdraw-pro-ai.vercel.app`
- **Backend API:** `https://YOUR-APP.up.railway.app`
- **API Docs:** `https://YOUR-APP.up.railway.app/docs`

### Share with the world:
```
🎨 AirDraw Pro AI is now live!

✨ Draw with AI-powered hand tracking
🌐 Try it: https://airdraw-pro-ai.vercel.app
🔗 GitHub: https://github.com/YOUR-USERNAME/airdraw-pro-ai

Built with Python, FastAPI, MediaPipe, and OpenCV!
```

---

## Troubleshooting

### Backend not deploying?
- Check Railway logs for errors
- Verify `requirements.txt` has all dependencies
- Make sure `Procfile` exists

### Frontend not connecting to backend?
- Check browser console for CORS errors
- Verify API URL is correct in `index.html`
- Test API health endpoint directly

### Need help?
- Railway Discord: https://discord.gg/railway
- Vercel Discord: https://vercel.com/discord

---

## Next Steps

1. ✅ Add custom domain (optional)
2. ✅ Set up monitoring
3. ✅ Share on social media
4. ✅ Add to your portfolio

---

**Estimated total time: 15 minutes** ⏱️

**Cost: $0/month** (Free tier) 💰

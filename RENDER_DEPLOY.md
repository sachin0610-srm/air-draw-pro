# 🚀 Deploy to Render - Step by Step Guide

## ✅ Why Render?
- Better free tier for Python apps
- More stable than Railway free tier
- No sleeping issues
- Great for FastAPI/OpenCV projects

---

## 📋 Step-by-Step Instructions

### Step 1: First, Undo Railway Commit (if you want)

```bash
git reset --hard HEAD~1
git push --force
```

### Step 2: Create Render Account

1. Go to **https://render.com**
2. Click **"Get Started"**
3. Sign up with **GitHub**
4. Authorize Render to access your repositories

---

### Step 3: Create New Web Service

1. Click **"New +"** button (top right)
2. Select **"Web Service"**
3. Click **"Connect a repository"**
4. Find and select **"precious-insight"** (or your repo name)
5. Click **"Connect"**

---

### Step 4: Configure Your Service

Fill in these settings:

**Basic Settings:**
- **Name:** `airdraw-api` (or any name you like)
- **Region:** Choose closest to you (e.g., Oregon, Frankfurt)
- **Branch:** `main`
- **Root Directory:** Leave blank
- **Runtime:** `Python 3`

**Build & Deploy:**
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `uvicorn api_server_light:app --host 0.0.0.0 --port $PORT`

**Plan:**
- Select **"Free"** plan (0$/month)

---

### Step 5: Environment Variables (Optional)

If you need any:
- Click **"Advanced"**
- Add environment variables
- For now, you can skip this

---

### Step 6: Deploy!

1. Click **"Create Web Service"** button
2. Wait 3-5 minutes for deployment...
3. Watch the logs for success ✅

You'll see:
```
==> Building...
==> Installing dependencies...
==> Starting server...
✅ Your service is live
```

---

### Step 7: Get Your URL

Once deployed, you'll see your URL at the top:

```
https://airdraw-api.onrender.com
```

**Test it immediately:**
```
https://airdraw-api.onrender.com/health
```

Should return:
```json
{
  "status": "ok",
  "service": "airdraw-api",
  "timestamp": 1234567890
}
```

---

### Step 8: Update Frontend

Update `index.html` with your new Render URL:

```javascript
const API_BASE = 'https://airdraw-api.onrender.com';
```

Then push:
```bash
git add index.html
git commit -m "🔗 Connect to Render backend"
git push
```

---

## 🎯 Important Notes for Render Free Tier

### Cold Starts
- Free tier spins down after 15 minutes of inactivity
- First request after sleep takes ~30 seconds
- Subsequent requests are instant

### Keep-Alive (Optional)
Use a service like **UptimeRobot** to ping every 10 minutes:
1. Go to https://uptimerobot.com
2. Add monitor: `https://airdraw-api.onrender.com/health`
3. Check interval: 10 minutes

### Memory Limits
- Free tier: 512MB RAM
- Our lightweight API uses ~200MB
- Should be stable ✅

---

## 🐛 Troubleshooting

### Build Failed?
- Check logs in Render dashboard
- Verify `requirements.txt` is correct
- Make sure Python version is compatible

### 502/503 Errors?
- Wait 30 seconds (cold start)
- Check if service is "Suspended" in dashboard
- Free tier auto-suspends if no requests

### CORS Errors?
- Our API already has CORS enabled
- Should work fine

---

## 📊 Monitor Your Deployment

**Render Dashboard:**
- **Logs:** Real-time application logs
- **Metrics:** CPU, Memory, Request count
- **Events:** Deploy history

**Check Health:**
```bash
curl https://YOUR-URL.onrender.com/health
```

**API Docs:**
```
https://YOUR-URL.onrender.com/docs
```

---

## 🎉 Once Deployed

Your stack will be:
- ✅ Backend: Render (Free)
- ✅ Frontend: Vercel (Free)
- ✅ Total cost: $0/month

**Render is more stable than Railway for free tier!**

---

## 🔄 Comparison: Railway vs Render

| Feature | Railway Free | Render Free |
|---------|-------------|------------|
| RAM | 512MB | 512MB |
| Sleep | After 15min | After 15min |
| Build time | Faster | Slower |
| Stability | ⚠️ Can crash | ✅ More stable |
| Python/OpenCV | ⚠️ Issues | ✅ Works well |
| Cold start | 5-10s | 20-30s |
| **Best for** | Node.js | **Python** ⭐ |

---

**Ready to deploy? Follow the steps above!** 🚀

Need help at any step? Just ask!

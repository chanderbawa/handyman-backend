# HandyMan Backend - Free Deployment Guide

Complete guide to deploy the HandyMan backend API to free hosting platforms.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Platform Options](#platform-options)
- [Render (Recommended)](#render-deployment)
- [Railway](#railway-deployment)
- [Fly.io](#flyio-deployment)
- [Database Setup](#database-setup)
- [Environment Variables](#environment-variables)
- [Post-Deployment](#post-deployment)

## Prerequisites

Before deploying, ensure you have:

- ✅ GitHub account (for code repository)
- ✅ Git installed locally
- ✅ Code pushed to GitHub repository
- ✅ Environment variables ready
- ✅ Database provider account (if separate)

## Platform Options

### Platform Comparison

| Platform | Free Tier | Database | Build Time | Ease of Use | Best For |
|----------|-----------|----------|------------|-------------|----------|
| **Render** | 750 hrs/mo | PostgreSQL included | ~5 min | ⭐⭐⭐⭐⭐ | Production-ready |
| **Railway** | $5 credit/mo | PostgreSQL included | ~3 min | ⭐⭐⭐⭐ | Quick deploys |
| **Fly.io** | 3 VMs free | Separate provider | ~4 min | ⭐⭐⭐ | Advanced users |

## Render Deployment

### Step 1: Prepare Repository

```bash
cd handyman-backend
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/handyman-backend.git
git push -u origin main
```

### Step 2: Create Render Account

1. Go to [render.com](https://render.com)
2. Sign up with GitHub
3. Authorize Render to access your repositories

### Step 3: Create Web Service

1. Click **"New +"** → **"Web Service"**
2. Connect your `handyman-backend` repository
3. Configure the service:

   ```
   Name: handyman-backend
   Region: Choose closest to your users
   Branch: main
   Runtime: Python 3
   Build Command: pip install -r requirements.txt
   Start Command: uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```

### Step 4: Create PostgreSQL Database

1. Click **"New +"** → **"PostgreSQL"**
2. Configure:
   ```
   Name: handyman-db
   Database: handyman_db
   User: handyman_user
   Region: Same as web service
   ```
3. Click **"Create Database"**
4. Wait for provisioning (~2 minutes)

### Step 5: Enable PostGIS Extension

1. Go to your database → **"Connect"**
2. Copy the **External Connection String**
3. Use a PostgreSQL client (like TablePlus or psql):

   ```bash
   psql "postgresql://handyman_user:password@host/handyman_db"
   ```

4. Run:
   ```sql
   CREATE EXTENSION postgis;
   \q
   ```

### Step 6: Configure Environment Variables

In your web service, go to **"Environment"** tab and add:

```env
# Database (copy Internal Database URL from your Render PostgreSQL)
DATABASE_URL=postgresql://handyman_user:password@internal-host/handyman_db

# Security
SECRET_KEY=your-super-secret-key-change-this-in-production-min-32-chars

# OpenAI (if using AI features)
OPENAI_API_KEY=sk-your-openai-api-key

# App Config
APP_ENV=production
DEBUG=False
ALLOWED_HOSTS=your-app.onrender.com

# CORS (your mobile app domain or * for testing)
CORS_ORIGINS=*
```

### Step 7: Run Database Migrations

After first deployment, go to **"Shell"** tab and run:

```bash
alembic upgrade head
```

### Step 8: Access Your API

Your API will be available at:
```
https://handyman-backend.onrender.com
```

Test it:
```bash
curl https://handyman-backend.onrender.com/health
```

---

## Railway Deployment

### Step 1: Create Railway Account

1. Go to [railway.app](https://railway.app)
2. Sign up with GitHub

### Step 2: Create New Project

```bash
# Install Railway CLI
npm i -g @railway/cli

# Login
railway login

# Initialize project
cd handyman-backend
railway init

# Link to GitHub
railway link
```

### Step 3: Add PostgreSQL Database

1. In Railway dashboard, click **"New"** → **"Database"** → **"PostgreSQL"**
2. Enable PostGIS:
   - Click on PostgreSQL service
   - Go to **"Connect"** → **"psql"**
   - Run: `CREATE EXTENSION postgis;`

### Step 4: Configure Service

Create `railway.json`:

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "uvicorn app.main:app --host 0.0.0.0 --port $PORT",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

### Step 5: Add Environment Variables

In Railway dashboard → **Variables**:

```env
DATABASE_URL=${{Postgres.DATABASE_URL}}
SECRET_KEY=your-secret-key-here
OPENAI_API_KEY=sk-your-key
APP_ENV=production
DEBUG=False
PORT=8000
```

### Step 6: Deploy

```bash
railway up
```

Or push to GitHub (if connected):
```bash
git push origin main
```

### Step 7: Generate Domain

1. Go to **Settings** → **Networking**
2. Click **"Generate Domain"**
3. Your API: `https://handyman-backend-production.up.railway.app`

---

## Fly.io Deployment

### Step 1: Install Fly CLI

```bash
# macOS
brew install flyctl

# Linux
curl -L https://fly.io/install.sh | sh

# Windows
iwr https://fly.io/install.ps1 -useb | iex
```

### Step 2: Sign Up and Login

```bash
flyctl auth signup
# or
flyctl auth login
```

### Step 3: Initialize Fly App

```bash
cd handyman-backend
flyctl launch

# Answer prompts:
# App name: handyman-backend
# Region: Choose closest
# PostgreSQL: Yes
# Redis: No (optional)
```

### Step 4: Configure fly.toml

Edit `fly.toml`:

```toml
app = "handyman-backend"
primary_region = "sjc"

[build]
  builder = "paketobuildpacks/builder:base"

[env]
  PORT = "8000"
  APP_ENV = "production"

[http_service]
  internal_port = 8000
  force_https = true
  auto_stop_machines = true
  auto_start_machines = true
  min_machines_running = 0
  
  [[http_service.checks]]
    grace_period = "10s"
    interval = "30s"
    method = "GET"
    timeout = "5s"
    path = "/health"

[[services]]
  protocol = "tcp"
  internal_port = 8000

  [[services.ports]]
    port = 80
    handlers = ["http"]
  
  [[services.ports]]
    port = 443
    handlers = ["tls", "http"]
```

### Step 5: Set Environment Variables

```bash
flyctl secrets set SECRET_KEY=your-secret-key
flyctl secrets set OPENAI_API_KEY=sk-your-key
flyctl secrets set DATABASE_URL=$(flyctl postgres attach --app your-postgres-app)
```

### Step 6: Enable PostGIS

```bash
flyctl postgres connect -a handyman-backend-db
CREATE EXTENSION postgis;
\q
```

### Step 7: Deploy

```bash
flyctl deploy
```

### Step 8: Open App

```bash
flyctl open
```

Your API: `https://handyman-backend.fly.dev`

---

## Database Setup

### Option 1: Free PostgreSQL Providers

#### Supabase (Recommended)

1. Go to [supabase.com](https://supabase.com)
2. Create project
3. Enable PostGIS:
   - Go to **SQL Editor**
   - Run: `CREATE EXTENSION postgis;`
4. Get connection string from **Settings** → **Database**

#### Neon

1. Go to [neon.tech](https://neon.tech)
2. Create project
3. Create database: `handyman_db`
4. Enable PostGIS in SQL Editor
5. Copy connection string

#### ElephantSQL

1. Go to [elephantsql.com](https://elephantsql.com)
2. Create instance (Tiny Turtle - Free)
3. Enable PostGIS
4. Copy URL

### Option 2: Platform-Provided Database

Most platforms provide PostgreSQL:
- **Render**: Built-in PostgreSQL
- **Railway**: Add PostgreSQL service
- **Fly.io**: `flyctl postgres create`

---

## Environment Variables

### Required Variables

```env
# Database
DATABASE_URL=postgresql://user:pass@host:5432/dbname

# Security
SECRET_KEY=your-super-secret-key-at-least-32-characters-long

# AI Features (optional)
OPENAI_API_KEY=sk-your-openai-api-key

# Application
APP_ENV=production
DEBUG=False

# CORS
CORS_ORIGINS=*
```

### Optional Variables

```env
# Redis (for caching)
REDIS_URL=redis://user:pass@host:6379

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=app-password

# Storage (for file uploads)
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
AWS_S3_BUCKET=handyman-uploads
```

### Generating SECRET_KEY

```python
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## Post-Deployment

### 1. Run Database Migrations

```bash
# Render: Use Shell tab
alembic upgrade head

# Railway/Fly: Use CLI
railway run alembic upgrade head
# or
flyctl ssh console -C "alembic upgrade head"
```

### 2. Create Initial Data

```bash
# Create admin user
python scripts/create_admin.py
```

### 3. Test API Endpoints

```bash
# Health check
curl https://your-app.com/health

# API docs
open https://your-app.com/docs

# Register test user
curl -X POST https://your-app.com/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"TestPass123!","full_name":"Test User","phone":"+1234567890"}'
```

### 4. Monitor Application

- **Render**: Built-in logs and metrics
- **Railway**: Logs tab in dashboard
- **Fly.io**: `flyctl logs`

### 5. Set Up CI/CD (Optional)

All platforms auto-deploy on git push when connected to GitHub:

1. Push to main branch
2. Automatic build and deploy
3. Zero downtime deployment

---

## Troubleshooting

### Build Failures

**Issue**: Build times out or fails

**Solution**:
```bash
# Reduce dependencies in requirements.txt
# Or increase build timeout in platform settings
```

### Database Connection Failed

**Issue**: Can't connect to database

**Solution**:
1. Check `DATABASE_URL` format
2. Verify PostGIS extension: `SELECT PostGIS_version();`
3. Check firewall/IP whitelist settings

### Cold Starts

**Issue**: First request after inactivity is slow

**Solution**:
- **Render**: Upgrade to paid plan
- **Railway**: Stays warm
- **Fly.io**: Set `min_machines_running = 1`

### CORS Errors

**Issue**: Mobile app can't access API

**Solution**:
```python
# In app/main.py
allow_origins=["*"]  # Development
# or
allow_origins=["https://your-mobile-app.com"]  # Production
```

---

## Cost Optimization

### Staying Within Free Tier

1. **Render**: 750 hours/month free
   - Use for staging/development
   - Upgrade to paid for production

2. **Railway**: $5 credit/month
   - Monitor usage in dashboard
   - Optimize resource usage

3. **Fly.io**: 3 shared VMs free
   - Use auto-stop machines
   - Share database across apps

### Upgrade Paths

When you need to scale:

- **Render**: $7/month starter → $25/month standard
- **Railway**: Pay as you go after free credit
- **Fly.io**: Pay per resource usage

---

## Security Checklist

Before going to production:

- [ ] Change `SECRET_KEY` to strong random value
- [ ] Set `DEBUG=False`
- [ ] Configure specific `CORS_ORIGINS`
- [ ] Enable HTTPS (automatic on all platforms)
- [ ] Set up database backups
- [ ] Use environment variables for all secrets
- [ ] Enable rate limiting
- [ ] Set up monitoring and alerts
- [ ] Review database security settings

---

## Next Steps

1. ✅ Deploy backend API
2. ✅ Test all endpoints
3. ✅ Configure mobile app with API URL
4. ✅ Deploy mobile app (see MOBILE_DEPLOYMENT.md)
5. ✅ Set up monitoring
6. ✅ Configure custom domain (optional)

---

## Support

For platform-specific issues:
- **Render**: https://render.com/docs
- **Railway**: https://docs.railway.app
- **Fly.io**: https://fly.io/docs

For application issues:
- Check logs in platform dashboard
- Review API docs at `/docs` endpoint
- Verify environment variables are set correctly

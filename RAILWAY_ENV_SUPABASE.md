# Environment Variables Template for Railway

## Required Environment Variables

```bash
# Database (Supabase PostgreSQL)
DATABASE_URL=postgresql://postgres.[project-ref]:[password]@aws-0-ap-northeast-1.pooler.supabase.com:5432/postgres

# Supabase API (Optional - for direct API access)
SUPABASE_URL=https://[project-ref].supabase.co
SUPABASE_KEY=[your-anon-key]

# Security
SECRET_KEY=schbc-bbms-production-secret-key-2026-change-this-in-production-env
DEBUG=False
```

## How to Set in Railway

### Option 1: Railway CLI
```bash
railway variables set DATABASE_URL="postgresql://..."
railway variables set SUPABASE_URL="https://..."
railway variables set SUPABASE_KEY="..."
railway variables set SECRET_KEY="..."
railway variables set DEBUG="False"
```

### Option 2: Railway Dashboard
1. Go to Railway Dashboard
2. Select your project (outstanding-courage)
3. Go to Variables tab
4. Add each variable manually

## Supabase Connection String Format

**Session Mode** (recommended for serverless):
```
postgresql://postgres.[project-ref]:[password]@aws-0-ap-northeast-1.pooler.supabase.com:5432/postgres
```

**Transaction Mode** (for long-running connections):
```
postgresql://postgres.[project-ref]:[password]@aws-0-ap-northeast-1.pooler.supabase.com:6543/postgres
```

## Getting Supabase Credentials

1. Go to Supabase Dashboard: https://supabase.com/dashboard
2. Select your project
3. Go to **Settings** → **Database**
4. Copy **Connection String** (Session mode)
5. Go to **Settings** → **API**
6. Copy **Project URL** and **anon/public key**

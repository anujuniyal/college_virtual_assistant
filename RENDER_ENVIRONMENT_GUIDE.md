# Render Environment Variables Guide

## 🔍 Common Issue: DATABASE_URL Not Found

### **Root Cause**
The confusion comes from **how Render handles environment variables** vs local development.

### **How Render Works**
1. **Render does NOT read `.env.render` files** - these are only for local testing
2. **Render uses `render.yaml` environment variables** or dashboard settings
3. **The application was trying to load `.env.render` on Render servers** (where it doesn't exist)

### **Environment Variable Loading Logic**

```python
# ✅ CORRECT: Detect if running on Render
is_render_deployment = os.environ.get('RENDER') == 'true' or os.path.exists('/etc/render')

if not is_render_deployment:
    # Load .env.render ONLY for local development/testing
    load_dotenv('.env.render')
else:
    # Use Render's environment variables from render.yaml
    print("🚀 Running on Render - using environment variables from render.yaml")
```

### **Configuration Priority**

#### **On Render:**
1. **render.yaml** `envVars` (highest priority)
2. **Render Dashboard** environment variables
3. **Render built-in variables** (PORT, RENDER, etc.)

#### **Local Development:**
1. **.env.render** (for testing Render-like environment)
2. **.env.production** (for local production testing)
3. **.env** (base development)

### **Database URL Resolution**

#### **Render Deployment:**
```yaml
# render.yaml
envVars:
  - key: DATABASE_URL
    value: postgresql://postgres:password@host:5432/dbname
```

#### **Local Development:**
```bash
# .env.render
DATABASE_URL=postgresql://postgres:password@host:5432/dbname
```

### **Debug Information**

The application now prints clear debug information:

```
🔍 DEBUG: Environment variables:
   Platform: Render
   FLASK_ENV: production
   DATABASE_URL: postgresql://postgres:...
   POSTGRESQL_URL: NOT_SET
   Final Database URI: postgresql://postgres:...?sslmode=require&connect_timeout=10&application_name=edubot
```

### **Common Fixes**

1. **DATABASE_URL not found on Render:**
   - ✅ Ensure DATABASE_URL is set in `render.yaml`
   - ✅ Check Render dashboard environment variables
   - ❌ Don't rely on `.env.render` file

2. **Configuration not loading:**
   - ✅ Use `render.yaml` for Render environment variables
   - ✅ Use `.env.render` only for local testing
   - ✅ Add platform detection logic

3. **Authentication failures:**
   - ✅ Verify DATABASE_URL is correctly set
   - ✅ Check database connection logs
   - ✅ Ensure Supabase allows Render IPs

### **Testing Locally**

To test Render configuration locally:

```bash
# Set RENDER environment variable
export RENDER=true

# Run the application
python app.py
```

This will simulate Render environment loading.

### **Key Takeaways**

1. **🚫 `.env.render` files are NOT deployed to Render**
2. **✅ Use `render.yaml` for Render environment variables**
3. **🔍 Add platform detection to avoid confusion**
4. **📝 Use clear logging to debug configuration issues**

### **Render Environment Variables**

Render automatically provides these:
- `PORT` - Application port
- `RENDER` - Set to "true" on Render
- `RENDER_SERVICE_NAME` - Service name
- `RENDER_SERVICE_TYPE` - Service type

Use these to detect and configure your application correctly for Render deployment.

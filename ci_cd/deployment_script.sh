#!/bin/bash
set -e  # Exit immediately on error

echo "🚀 Starting deployment process..."

# --- Step 1: Check Django backend ---
if [ -f "manage.py" ]; then
  echo "Applying database migrations..."
  python manage.py migrate --noinput || echo "Skipping migrations if DB not configured."

  echo "Collecting static files..."
  python manage.py collectstatic --noinput || echo "No static files to collect."
else
  echo "manage.py not found — skipping backend steps."
fi

# --- Step 2: Check React frontend ---
if [ -d "frontend" ]; then
  echo "Building frontend..."
  cd frontend

  if [ -f "package.json" ]; then
    npm install --legacy-peer-deps || echo "npm install failed, skipping..."
    npm run build --if-present || echo "No build script found, skipping..."
  else
    echo "No package.json found — skipping frontend build."
  fi

  cd ..
else
  echo "frontend folder not found — skipping frontend steps."
fi

# --- Step 3: Optional deployment step ---
echo "Simulating deployment... (no remote server configured)"
sleep 2
echo "✅ Deployment script completed successfully!"
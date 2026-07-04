#!/usr/bin/env bash
# exit on error
set -o errexit

echo "📦 Installing dependencies..."
pip install -r requirements.txt

echo "🔄 Running migrations..."
python manage.py migrate

echo "🎨 Collecting static files..."
python manage.py collectstatic --no-input

# Optional: Seed database if requested via env var
if [ "$SEED_DB" = "True" ]; then
    echo "🌱 Seeding demo data..."
    python manage.py flush --no-input
    python manage.py seed_data
fi

echo "✅ Build complete!"

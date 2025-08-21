#!/bin/bash

# Скрипт для деплоя на PythonAnywhere

echo "🚀 Starting deployment to PythonAnywhere..."

# 1. Archive the project
echo "📦 Archiving project..."
git archive --format=tar HEAD | gzip > deploy.tar.gz

# 2. Upload to PythonAnywhere (you'll need to do this manually or via API)
echo "📤 Upload archive to PythonAnywhere:"
echo "   - Go to: https://www.pythonanywhere.com/user/maxb0t/files/home/maxb0t/"
echo "   - Upload deploy.tar.gz"

# 3. Extract commands for manual execution
echo ""
echo "📝 Manual steps on PythonAnywhere:"
echo "   mkdir -p ~/foodmind_backend"
echo "   tar -xzf deploy.tar.gz -C ~/foodmind_backend/"
echo "   cd ~/foodmind_backend"
echo "   python -m venv ~/.virtualenvs/foodmind_backend"
echo "   source ~/.virtualenvs/foodmind_backend/bin/activate"
echo "   pip install -r requirements.txt"
echo "   python manage.py migrate"
echo "   python manage.py collectstatic --noinput"
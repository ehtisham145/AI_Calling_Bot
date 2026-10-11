#!/bin/bash
# Run this ON THE VPS to deploy the latest pushed code. One-time setup (clone,
# venv, .env, first `pm2 start`) is in README.md - this script is for every
# update after that.
set -e

cd "$(dirname "$0")"

echo "==> Pulling latest code..."
git pull

echo "==> Installing/updating dependencies..."
source venv/bin/activate
pip install -r requirements.txt
deactivate

echo "==> Restarting via PM2..."
pm2 restart ai-calling-bot

echo "==> Recent logs:"
pm2 logs ai-calling-bot --lines 20 --nostream

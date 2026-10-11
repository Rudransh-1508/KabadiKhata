api: uvicorn api.app:app --port 3000
# Without a TELEGRAM_BOT_TOKEN the bot idles instead of exiting, which would stop every other process
bot: sh -c 'if [ -n "$TELEGRAM_BOT_TOKEN" ] && [ "$TELEGRAM_BOT_TOKEN" != "your-telegram-bot-token" ]; then KK_USE_MOCK=0 exec python -m bot.telegram_bot; else echo "TELEGRAM_BOT_TOKEN not set in .env: bot not started"; exec tail -f /dev/null; fi'
web: uvicorn web.server:app --port 8600
console: KK_USE_MOCK=0 streamlit run console/app.py --server.headless true --server.port 8501

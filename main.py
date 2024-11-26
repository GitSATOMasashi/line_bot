from fastapi import FastAPI, Request, HTTPException
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import os
import httpx

app = FastAPI()

# 環境変数から設定を読み込み
LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET')
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
DIFY_API_KEY = os.getenv('DIFY_API_KEY')

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

@app.post("/callback")
async def callback(request: Request):
    signature = request.headers.get('X-Line-Signature', '')
    body = await request.body()
    body_text = body.decode('utf-8')

    try:
        handler.handle(body_text, signature)
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
async def handle_message(event):
    # Dify APIにリクエスト
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.dify.ai/v1/chat-messages",
            headers={
                'Authorization': f'Bearer {DIFY_API_KEY}',
                'Content-Type': 'application/json'
            },
            json={
                "inputs": {},
                "query": event.message.text,
                "response_mode": "blocking",
                "user": event.source.user_id
            }
        )
        dify_response = response.json()
    
    # LINEに応答を返信
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=dify_response["answer"])
    )

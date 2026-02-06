#!/usr/bin/env python3
"""
Telegram Bot - 完整版
整合 Nebula API 實現 AI 對話、股價查詢、持股分析
"""

import os
import sys
import logging
import asyncio
import httpx
from datetime import datetime
from typing import Optional
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

# 設定日誌
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# 環境變數
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
NEBULA_API_KEY = os.getenv("NEBULA_API_KEY", "")  # 選用
NEBULA_API_URL = os.getenv("NEBULA_API_URL", "https://api.nebula.gg")

# 驗證環境變數
if not BOT_TOKEN:
    logger.error("❌ 錯誤: 未設定 TELEGRAM_BOT_TOKEN")
    sys.exit(1)

if not CHAT_ID:
    logger.error("❌ 錯誤: 未設定 TELEGRAM_CHAT_ID")
    sys.exit(1)

logger.info("🤖 Telegram Bot 啟動中...")
logger.info(f"✅ Bot Token: {BOT_TOKEN[:20]}...")
logger.info(f"✅ 授權使用者: {CHAT_ID}")

# HTTP 客戶端
http_client = httpx.AsyncClient(timeout=30.0)


# ==================== Nebula API 整合 ====================

async def call_nebula_api(message: str) -> str:
    """
    呼叫 Nebula API 進行 AI 對話
    
    Args:
        message: 使用者訊息
        
    Returns:
        AI 回應內容
    """
    if not NEBULA_API_KEY:
        return "⚠️ 尚未設定 Nebula API Key，無法使用 AI 對話功能。\n\n請在 Render 環境變數中設定 NEBULA_API_KEY。"
    
    try:
        response = await http_client.post(
            f"{NEBULA_API_URL}/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {NEBULA_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "messages": [
                    {
                        "role": "user",
                        "content": message
                    }
                ],
                "stream": False
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            return data.get("choices", [{}])[0].get("message", {}).get("content", "無法取得回應")
        else:
            logger.error(f"Nebula API 錯誤: {response.status_code} - {response.text}")
            return f"❌ API 呼叫失敗 (HTTP {response.status_code})"
            
    except Exception as e:
        logger.error(f"Nebula API 異常: {e}")
        return f"❌ 發生錯誤: {str(e)}"


# ==================== 股價查詢功能 ====================

async def get_stock_price(stock_code: str) -> str:
    """
    查詢股票即時價格
    
    Args:
        stock_code: 股票代碼（如: 2330.TW）
        
    Returns:
        股價資訊
    """
    try:
        # 使用 Yahoo Finance API
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{stock_code}"
        response = await http_client.get(url)
        
        if response.status_code == 200:
            data = response.json()
            result = data.get("chart", {}).get("result", [{}])[0]
            meta = result.get("meta", {})
            
            price = meta.get("regularMarketPrice", "N/A")
            prev_close = meta.get("previousClose", "N/A")
            change = price - prev_close if price != "N/A" and prev_close != "N/A" else 0
            change_percent = (change / prev_close * 100) if prev_close != "N/A" and prev_close != 0 else 0
            
            symbol = meta.get("symbol", stock_code)
            currency = meta.get("currency", "TWD")
            
            # 格式化輸出
            change_emoji = "🔴" if change < 0 else "🟢" if change > 0 else "⚪"
            
            return f"""
📊 **{symbol}** 即時資訊

💰 目前價格: {price} {currency}
📉 昨日收盤: {prev_close} {currency}
{change_emoji} 漲跌: {change:+.2f} ({change_percent:+.2f}%)
🕐 更新時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        else:
            return f"❌ 無法取得 {stock_code} 的股價資訊（HTTP {response.status_code}）"
            
    except Exception as e:
        logger.error(f"股價查詢錯誤: {e}")
        return f"❌ 查詢失敗: {str(e)}"


# ==================== 指令處理器 ====================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """處理 /start 指令"""
    user_id = str(update.effective_user.id)
    
    # 權限檢查
    if user_id != CHAT_ID:
        await update.message.reply_text("❌ 抱歉，你沒有使用此 Bot 的權限。")
        return
    
    welcome_message = """
👋 歡迎使用 Alice AI 助理！

🤖 **我能做什麼？**

📊 **股價查詢**
• /stock 2330.TW - 查詢台積電股價
• /stock AAPL - 查詢蘋果股價
• /stock ^TWII - 查詢台灣加權指數

💬 **AI 對話**
• 直接輸入任何問題，我會用 AI 回答
• 例如: "台積電今天表現如何？"
• 例如: "幫我分析美股趨勢"

📈 **持股管理** (即將推出)
• /portfolio - 查看持股資訊
• /report - 查看報告推送時間

❓ **其他指令**
• /help - 顯示使用說明
• /ping - 測試 Bot 狀態

💡 **提示**: 你可以直接問我任何問題！
"""
    
    await update.message.reply_text(welcome_message)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """處理 /help 指令"""
    user_id = str(update.effective_user.id)
    
    if user_id != CHAT_ID:
        await update.message.reply_text("❌ 抱歉，你沒有使用此 Bot 的權限。")
        return
    
    help_text = """
📚 **使用說明**

**基本指令**
/start - 顯示歡迎訊息
/help - 顯示此說明
/ping - 測試 Bot 狀態

**股價查詢**
/stock <代碼> - 查詢股票即時價格

支援的股票代碼格式:
• 台股: 2330.TW (台積電)
• 美股: AAPL (蘋果)
• 指數: ^TWII (台灣加權), ^DJI (道瓊)

範例:
/stock 2330.TW
/stock AAPL
/stock ^TWII

**AI 對話**
直接輸入訊息即可與 AI 對話:
• "台積電今天表現如何？"
• "美股趨勢分析"
• "幫我解釋什麼是 ETF"

**持股管理** (開發中)
/portfolio - 查看持股明細
/report - 查看報告推送設定

**自動推送** (計畫中)
• 每日 06:30 - 台美財經日報
• 每日 07:00 - 持股損益更新
• 週六 07:00 - 每週投資週報

有問題嗎？直接問我就對了！😊
"""
    
    await update.message.reply_text(help_text)


async def ping_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """處理 /ping 指令"""
    user_id = str(update.effective_user.id)
    
    if user_id != CHAT_ID:
        await update.message.reply_text("❌ 抱歉，你沒有使用此 Bot 的權限。")
        return
    
    uptime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    status_message = f"""
🟢 **Bot 狀態: 正常運行中**

⏰ 當前時間: {uptime}
🤖 服務: Telegram Bot
🔗 連接: Nebula API {'✅' if NEBULA_API_KEY else '⚠️ 未設定'}
📡 環境: Render.com Background Worker

✅ 所有系統正常！
"""
    
    await update.message.reply_text(status_message)


async def stock_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """處理 /stock 指令"""
    user_id = str(update.effective_user.id)
    
    if user_id != CHAT_ID:
        await update.message.reply_text("❌ 抱歉，你沒有使用此 Bot 的權限。")
        return
    
    # 檢查參數
    if not context.args:
        await update.message.reply_text(
            "❌ 請提供股票代碼\n\n"
            "使用方式: /stock <代碼>\n"
            "範例:\n"
            "  /stock 2330.TW (台積電)\n"
            "  /stock AAPL (蘋果)\n"
            "  /stock ^TWII (台灣加權指數)"
        )
        return
    
    stock_code = context.args[0].upper()
    
    # 發送「查詢中」訊息
    status_msg = await update.message.reply_text(f"🔍 正在查詢 {stock_code} 的股價...")
    
    # 查詢股價
    result = await get_stock_price(stock_code)
    
    # 更新訊息
    await status_msg.edit_text(result)


async def portfolio_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """處理 /portfolio 指令"""
    user_id = str(update.effective_user.id)
    
    if user_id != CHAT_ID:
        await update.message.reply_text("❌ 抱歉，你沒有使用此 Bot 的權限。")
        return
    
    await update.message.reply_text(
        "📊 **持股管理功能**\n\n"
        "⚠️ 此功能正在開發中...\n\n"
        "未來功能:\n"
        "• 即時持股損益\n"
        "• 個股成本分析\n"
        "• 報酬率統計\n"
        "• 風險評估\n\n"
        "敬請期待！"
    )


async def report_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """處理 /report 指令"""
    user_id = str(update.effective_user.id)
    
    if user_id != CHAT_ID:
        await update.message.reply_text("❌ 抱歉，你沒有使用此 Bot 的權限。")
        return
    
    await update.message.reply_text(
        "📨 **自動報告推送時間表**\n\n"
        "⚠️ 推送功能尚未啟用\n\n"
        "計畫推送時間:\n"
        "• 每日 06:30 - 台美財經日報\n"
        "• 每日 07:00 - 持股損益更新\n"
        "• 週六 07:00 - 每週投資週報\n\n"
        "敬請期待！"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """處理一般訊息（AI 對話）"""
    user_id = str(update.effective_user.id)
    message_text = update.message.text
    
    # 權限檢查
    if user_id != CHAT_ID:
        await update.message.reply_text("❌ 抱歉，你沒有使用此 Bot 的權限。")
        return
    
    logger.info(f"收到訊息: {message_text} (用戶: {user_id})")
    
    # 發送「思考中」訊息
    status_msg = await update.message.reply_text("🤔 正在思考...")
    
    # 呼叫 Nebula API
    response = await call_nebula_api(message_text)
    
    # 更新訊息
    await status_msg.edit_text(response)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """處理錯誤"""
    logger.error(f"發生錯誤: {context.error}")
    
    if isinstance(update, Update) and update.effective_message:
        await update.effective_message.reply_text(
            f"❌ 發生錯誤: {str(context.error)}\n\n"
            "請稍後再試，或使用 /help 查看使用說明。"
        )


def main():
    """主程式"""
    try:
        # 建立 Application
        application = Application.builder().token(BOT_TOKEN).build()
        
        # 註冊指令處理器
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("ping", ping_command))
        application.add_handler(CommandHandler("stock", stock_command))
        application.add_handler(CommandHandler("portfolio", portfolio_command))
        application.add_handler(CommandHandler("report", report_command))
        
        # 註冊訊息處理器（AI 對話）
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        # 註冊錯誤處理器
        application.add_error_handler(error_handler)
        
        logger.info("🚀 Bot 啟動成功！正在監聽訊息...")
        
        # 使用 polling 模式（適合 Background Worker）
        application.run_polling(allowed_updates=Update.ALL_TYPES)
        
    except Exception as e:
        logger.error(f"❌ Bot 啟動失敗: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

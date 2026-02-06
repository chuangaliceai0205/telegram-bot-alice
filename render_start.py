#!/usr/bin/env python3
"""
Render.com 專用的 Telegram Bot 啟動腳本
簡化版本，適合雲端部署
"""

import os
import sys
import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# 日誌設定
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# 從環境變數讀取設定
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

if not BOT_TOKEN:
    logger.error("❌ 未設定 TELEGRAM_BOT_TOKEN 環境變數")
    sys.exit(1)

# ==================== Bot 指令處理 ====================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """處理 /start 指令"""
    welcome_message = """🎉 *歡迎使用 Alice AI Bot！*

我是你的 AI 助手，可以協助你：

📊 *主要功能*
• 查詢持股資訊
• 接收每日財經報告
• 搜尋市場資訊
• 即時問答

💬 *使用方式*
直接發送訊息給我，或使用以下指令：

/start - 顯示此訊息
/help - 查看詳細說明
/portfolio - 查看持股
/report - 最新報告
/ping - 測試連線

現在就試試看吧！"""
    
    await update.message.reply_text(welcome_message, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """處理 /help 指令"""
    help_text = """📖 *使用說明*

*可用指令：*
/start - 開始使用
/help - 查看說明
/portfolio - 查看持股狀況
/report - 查看最新報告
/ping - 測試 Bot 狀態

*直接對話：*
你可以直接發送訊息給我，例如：
• "台積電今天股價"
• "顯示我的持股"
• "美股表現如何"

*自動通知：*
我會在以下時間自動推送報告：
• 每天 06:30 - 台美財經日報
• 每天 07:00 - 持股損益更新
• 每週六 07:00 - 週報

有問題隨時問我！"""
    
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def ping_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """處理 /ping 指令"""
    await update.message.reply_text("🟢 Bot 正常運行中！")

async def portfolio_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """處理 /portfolio 指令"""
    response = """📊 *持股資訊*

此功能需要與 Nebula 系統整合。
目前可以接收自動推送的持股報告。

每日 07:00 會自動更新持股損益。"""
    
    await update.message.reply_text(response, parse_mode='Markdown')

async def report_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """處理 /report 指令"""
    response = """📰 *報告查詢*

自動報告推送時間：
• 06:30 - 每日台美財經日報
• 07:00 - 持股損益更新
• 週六 07:00 - 週報

最新報告會自動推送到此聊天室。"""
    
    await update.message.reply_text(response, parse_mode='Markdown')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """處理一般文字訊息"""
    user_message = update.message.text
    user_id = update.message.from_user.id
    
    # 檢查是否為授權使用者
    if CHAT_ID and str(user_id) != CHAT_ID:
        await update.message.reply_text("⚠️ 你沒有使用此 Bot 的權限。")
        return
    
    logger.info(f"收到訊息: {user_message} (用戶: {user_id})")
    
    # 簡單回應
    response = f"收到你的訊息：「{user_message}」\n\n此功能正在開發中，目前支援：\n• /help - 查看說明\n• /portfolio - 持股資訊\n• /report - 報告查詢"
    
    await update.message.reply_text(response)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """錯誤處理"""
    logger.error(f"更新 {update} 發生錯誤: {context.error}")

# ==================== 主程式 ====================

def main():
    """啟動 Bot"""
    logger.info("🤖 Telegram Bot 啟動中...")
    logger.info(f"✅ Bot Token: {BOT_TOKEN[:20]}...")
    if CHAT_ID:
        logger.info(f"✅ 授權使用者: {CHAT_ID}")
    
    # 建立 Application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # 註冊指令處理器
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("ping", ping_command))
    application.add_handler(CommandHandler("portfolio", portfolio_command))
    application.add_handler(CommandHandler("report", report_command))
    
    # 註冊訊息處理器
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # 註冊錯誤處理器
    application.add_error_handler(error_handler)
    
    # 啟動 Bot (Long Polling)
    logger.info("✅ Bot 已啟動，開始監聽訊息...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()

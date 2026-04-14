"""
Brawl Stars Telegram Bot
Supports Friend Requests and Spectate/Viewer functionality
"""
import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
from config import TELEGRAM_BOT_TOKEN, MAX_SPECTATORS, FRIEND_REQUEST_COUNT
from brawl_client import send_friend_requests, send_spectators, encode_tag
from server import start_health_server

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    welcome_text = """
🎮 *Brawl Stars Bot*

Welcome! This bot can send friend requests and spectators to Brawl Stars players.

*Available Commands:*

🔹 `/friend [tag]` - Send 30 friend requests
   Example: `/friend #ABC123`

🔹 `/spectate [tag] [count]` - Send spectators (max 200)
   Example: `/spectate #ABC123 50`

🔹 `/help` - Show all commands

*Quick Actions:* Use the buttons below 👇
"""
    keyboard = [
        [
            InlineKeyboardButton("📩 Send Friend Requests", callback_data="action_friend"),
            InlineKeyboardButton("👁️ Send Spectators", callback_data="action_spectate"),
        ],
        [InlineKeyboardButton("❓ Help", callback_data="action_help")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        welcome_text,
        parse_mode='Markdown',
        reply_markup=reply_markup
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /help is issued."""
    help_text = """
📚 *Help - Brawl Stars Bot*

*Commands:*

🔹 `/start` - Start the bot
🔹 `/friend #[tag]` - Send 30 friend requests to player
🔹 `/friend #[tag] [count]` - Send custom number of friend requests
🔹 `/spectate #[tag] [count]` - Send spectators (1-200)
🔹 `/ping` - Check if bot is online

*Examples:*
`/friend #ABC123` - Sends 30 friend requests
`/friend #ABC123 50` - Sends 50 friend requests
`/spectate #ABC123 100` - Sends 100 spectators

*Tips:*
• Player tags start with #
• Max spectators: 200
• Each request opens a new connection
"""
    await update.message.reply_text(help_text, parse_mode='Markdown')


async def ping_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check if bot is online."""
    await update.message.reply_text("✅ Bot is online!")


async def friend_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /friend command."""
    args = context.args

    if not args or len(args) == 0:
        await update.message.reply_text(
            "❌ Usage: `/friend #[tag] [count]`\n"
            "Example: `/friend #ABC123` or `/friend #ABC123 50`",
            parse_mode='Markdown'
        )
        return

    tag = args[0].upper()
    if not tag.startswith('#'):
        tag = '#' + tag

    count = FRIEND_REQUEST_COUNT
    if len(args) > 1:
        try:
            count = int(args[1])
            if count < 1 or count > 100:
                await update.message.reply_text("❌ Count must be between 1 and 100")
                return
        except ValueError:
            await update.message.reply_text("❌ Invalid count. Use a number between 1 and 100.")
            return

    # Validate tag
    try:
        high, low = encode_tag(tag)
    except (ValueError, KeyError):
        await update.message.reply_text("❌ Invalid player tag. Make sure it contains only valid characters (0289PYLQGRJCUV)")
        return

    status_msg = await update.message.reply_text(f"📤 Sending {count} friend requests to {tag}...")

    # Run in thread pool to not block
    loop = asyncio.get_event_loop()
    success, result = await loop.run_in_executor(None, send_friend_requests, tag, count)

    await status_msg.edit_text(result)


async def spectate_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /spectate command."""
    args = context.args

    if not args or len(args) < 2:
        await update.message.reply_text(
            "❌ Usage: `/spectate #[tag] [count]`\n"
            "Example: `/spectate #ABC123 50`",
            parse_mode='Markdown'
        )
        return

    tag = args[0].upper()
    if not tag.startswith('#'):
        tag = '#' + tag

    try:
        count = int(args[1])
        if count < 1 or count > MAX_SPECTATORS:
            await update.message.reply_text(f"❌ Count must be between 1 and {MAX_SPECTATORS}")
            return
    except ValueError:
        await update.message.reply_text("❌ Invalid count. Use a number between 1 and 200.")
        return

    # Validate tag
    try:
        high, low = encode_tag(tag)
    except (ValueError, KeyError):
        await update.message.reply_text("❌ Invalid player tag. Make sure it contains only valid characters.")
        return

    status_msg = await update.message.reply_text(f"📤 Sending {count} spectators to {tag}...")

    # Run in thread pool
    loop = asyncio.get_event_loop()
    success, result = await loop.run_in_executor(None, send_spectators, tag, count)

    await status_msg.edit_text(result)


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button callbacks."""
    query = update.callback_query
    await query.answer()

    if query.data == "action_friend":
        await query.edit_message_text(
            "📩 *Send Friend Requests*\n\n"
            "Use: `/friend #[tag]` or `/friend #[tag] [count]`\n\n"
            "Example: `/friend #ABC123`",
            parse_mode='Markdown'
        )
    elif query.data == "action_spectate":
        await query.edit_message_text(
            "👁️ *Send Spectators*\n\n"
            "Use: `/spectate #[tag] [count]`\n\n"
            "Example: `/spectate #ABC123 50`",
            parse_mode='Markdown'
        )
    elif query.data == "action_help":
        await help_command(update.callback_query, context)


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Log errors."""
    logger.error(f"Update {update} caused error {context.error}")


def main():
    """Start the bot."""
    # Start health check server for Render.com
    start_health_server()
    print("Health check server started on port 10000")

    # Create the Application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("ping", ping_command))
    application.add_handler(CommandHandler("friend", friend_command))
    application.add_handler(CommandHandler("spectate", spectate_command))
    application.add_handler(CallbackQueryHandler(button_callback))

    # Add error handler
    application.add_error_handler(error_handler)

    # Start the Bot
    print("🤖 Brawl Stars Bot starting...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()

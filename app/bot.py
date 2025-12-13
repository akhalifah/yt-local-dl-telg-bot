import os
import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes
)

from config import Config
from utils import is_valid_youtube_url, download_video

# Setup logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=getattr(logging, Config.LOG_LEVEL.upper()),
)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    await update.message.reply_text(Config.BOT_START_MESSAGE)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming messages."""
    message_text = update.message.text
    chat_id = update.effective_chat.id

    # Check if message contains a YouTube link
    if is_valid_youtube_url(message_text):
        try:
            # Send processing message
            processing_msg = await update.message.reply_text(Config.BOT_PROCESSING_MESSAGE)

            logger.info(f"Starting download for: {message_text}")

            # Download the video/playlist
            # Note: This is a blocking call. For production use with many users, 
            # consider running in a separate thread/executor.
            download_video(message_text)

            # Delete the processing message
            try:
                await context.bot.delete_message(chat_id=chat_id, message_id=processing_msg.message_id)
                await update.message.reply_text(Config.BOT_SUCCESS_MESSAGE)
            except:
                pass

        except Exception as e:
            logger.error(f"Error processing YouTube link: {e}")
            await update.message.reply_text(Config.BOT_ERROR_MESSAGE)
    else:
        await update.message.reply_text("Please send a valid YouTube link.")

async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Log errors caused by updates."""
    logger.error(f"Update {update} caused error: {context.error}")

def main():
    """Start the bot."""
    try:
        Config.validate()
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        raise
    
    application = ApplicationBuilder().token(Config.BOT_TOKEN).build()

    # Register command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_error_handler(error)

    # Start the Bot
    logger.info("Starting bot...")
    application.run_polling()

if __name__ == '__main__':
    main()
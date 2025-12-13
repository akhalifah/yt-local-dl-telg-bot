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
import yt_dlp
from config import Config
from utils import get_yt_dlp_options, is_valid_youtube_url, sanitize_filename

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

            # Configure yt-dlp options
            ydl_opts = get_yt_dlp_options()
            
            logger.info(f"Downloading with options: {ydl_opts}")

            # Download the video
            download_success = False
            file_path = None
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(message_text, download=True)
                
                # Get the actual file path
                if info and 'entries' in info:
                    # Playlist case - get first entry
                    first_entry = info['entries'][0]
                    file_path = os.path.join(
                        Config.DOWNLOAD_DIR,
                        sanitize_filename(first_entry.get('title', 'video')) + '.mp4'
                    )
                else:
                    # Single video case
                    file_path = os.path.join(
                        Config.DOWNLOAD_DIR,
                        sanitize_filename(info.get('title', 'video')) + '.mp4'
                    )

            # # Send the downloaded file
            # if file_path and os.path.exists(file_path):
            #     file_size = os.path.getsize(file_path)
                
            #     # Check file size limit
            #     if Config.MAX_FILE_SIZE > 0 and file_size > Config.MAX_FILE_SIZE:
            #         await update.message.reply_text(
            #             f"File size ({file_size} bytes) exceeds maximum limit ({Config.MAX_FILE_SIZE} bytes)"
            #         )
            #     else:
            #         # Send the video file
            #         with open(file_path, 'rb') as video:
            #             await context.bot.send_video(
            #                 chat_id=chat_id, 
            #                 video=video, 
            #                 supports_streaming=True
            #             )
                    
            #         # Delete the file after sending (optional)
            #         os.remove(file_path)
            #         logger.info(f"Successfully sent and deleted file: {file_path}")
                    
            #     download_success = True
            # else:
            #     await update.message.reply_text("Download failed. Please try again.")

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

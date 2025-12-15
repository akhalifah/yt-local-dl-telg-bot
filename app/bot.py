import os
import logging
import time
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes
)
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton

from config import Config
from utils import is_valid_youtube_url, download_video, get_video_info
from download_manager import get_download_manager, CancelledError
from telegram_downloader import download_telegram_video, get_video_info as get_telegram_video_info
from auth_manager import AuthManager

# Setup logging
# Setup logging
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(Config.LOG_DIR, Config.LOG_FILE))
    ]
)
logger = logging.getLogger(__name__)

# Initialize download manager
download_manager = None
auth_manager = None


def check_auth(func):
    """Decorator to check if user is authorized."""
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        if auth_manager.is_auth_enabled() and not auth_manager.is_authorized(user_id):
            await update.message.reply_text(
                Config.BOT_AUTH_RESTRICTED,
                parse_mode='Markdown'
            )
            return
        return await func(update, context, *args, **kwargs)
    return wrapper


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    if auth_manager.is_auth_enabled():
        user_id = update.effective_user.id
        if not auth_manager.is_authorized(user_id):
            await update.message.reply_text(
                Config.BOT_AUTH_RESTRICTED,
                parse_mode='Markdown'
            )
            return

    await update.message.reply_text(Config.BOT_START_MESSAGE)


async def cancel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle download cancellation callback."""
    query = update.callback_query
    await query.answer()  # Acknowledge callback
    
    data = query.data
    if not data.startswith("cancel_"):
        return
        
    try:
        task_id = int(data.split("_")[1])
        if download_manager.cancel_task(task_id):
            await query.edit_message_text(f"🛑 Cancelling download (Task {task_id})...")
        else:
            await query.edit_message_text("❌ Task not found or already completed.")
    except Exception as e:
        logger.error(f"Error processing cancel callback: {e}")
        await query.edit_message_text("❌ Error processing cancellation.")


async def auth_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle authentication command."""
    if not auth_manager.is_auth_enabled():
        await update.message.reply_text(Config.BOT_AUTH_NOT_ENABLED)
        return

    user_id = update.effective_user.id
    if auth_manager.is_authorized(user_id):
        await update.message.reply_text(Config.BOT_AUTH_ALREADY_Authorized)
        return

    if not context.args:
        await update.message.reply_text(Config.BOT_AUTH_USAGE, parse_mode='Markdown')
        return

    password = context.args[0]
    if auth_manager.authorize(user_id, password):
        await update.message.reply_text(Config.BOT_AUTH_SUCCESS)
        logger.info(f"User {user_id} authorized via command.")
    else:
        await update.message.reply_text(Config.BOT_AUTH_FAILED)
        logger.warning(f"Failed auth attempt by {user_id}")


@check_auth
async def queue_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show current download queue status."""
    status = download_manager.get_queue_status()
    
    message = (
        f"📊 **Download Queue Status**\n\n"
        f"Active downloads: {status['active']}/{status['max']}\n"
        f"Waiting in queue: {status['waiting']}\n"
        f"Total queued: {status['total']}"
    )
    
    await update.message.reply_text(message, parse_mode='Markdown')


@check_auth
async def handle_youtube_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle YouTube link downloads with concurrent support."""
    message_text = update.message.text
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    
    try:
        # Send initial processing message
        processing_msg = await update.message.reply_text("🔎 Processing link...")

        # Get video/playlist info first (run in executor to avoid blocking)
        import asyncio
        loop = asyncio.get_event_loop()
        video_info = await loop.run_in_executor(None, get_video_info, message_text)
        
        # Create display name
        if video_info:
            if video_info['type'] == 'playlist':
                display_name = f"📋 {video_info['title']} ({video_info['video_count']} videos)"
            else:
                display_name = f"🎥 {video_info['title']}"
        else:
            # Fallback to truncated URL if info fetch fails
            display_name = message_text if len(message_text) <= 50 else message_text[:47] + "..."
        
        # Get queue status before queueing
        queue_status_before = download_manager.get_queue_status()
        
        # Notify user if they need to wait
        if queue_status_before['active'] >= queue_status_before['max']:
            position = queue_status_before['total'] + 1
            total = position
            queue_msg = Config.BOT_QUEUE_MESSAGE.format(position=position, total=total)
            await update.message.reply_text(queue_msg, disable_notification=True)
        
        logger.info(f"Queueing YouTube download for user {user_id}: {message_text}")
        
        # Progress tracking
        last_update_time = [0]  # Use list to allow modification in nested function
        progress_message_id = [None] # Store message ID for editing
        task_id_container = [None] # Store task ID for cancel button

        async def edit_progress_msg(chat_id, message_id, text, task_id=None):
            try:
                reply_markup = None
                if task_id:
                     reply_markup = InlineKeyboardMarkup([
                        [InlineKeyboardButton("🛑 Cancel", callback_data=f"cancel_{task_id}")]
                    ])
                
                await context.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=message_id,
                    text=text,
                    parse_mode='Markdown',
                    reply_markup=reply_markup,
                    disable_web_page_preview=True
                )
            except Exception as e:
                # Changes to message content are often ignored if content hasn't changed
                pass
        
        def progress_hook(d):
            """Progress hook for yt-dlp - logs progress to console"""
            if not Config.ENABLE_PROGRESS_NOTIFICATIONS:
                return
            
            if d['status'] == 'downloading':
                # Check for cancellation
                if task_id_container[0]:
                    task = download_manager.get_task(task_id_container[0])
                    if task and task.cancelled:
                        raise CancelledError("Download cancelled")
                
                current_time = time.time()
                
                # Throttle updates based on PROGRESS_UPDATE_INTERVAL
                if current_time - last_update_time[0] < Config.PROGRESS_UPDATE_INTERVAL:
                    return
                
                last_update_time[0] = current_time
                
                # Extract progress information
                percent = d.get('_percent_str', 'N/A').strip()
                speed = d.get('_speed_str', 'N/A').strip()
                eta = d.get('_eta_str', 'N/A').strip()
                
                # Log progress
                logger.debug(f"Download progress for user {user_id}: {percent} | Speed: {speed} | ETA: {eta}")
                
                # Send progress to user if message ID is available
                if progress_message_id[0] and Config.ENABLE_PROGRESS_NOTIFICATIONS:
                    progress_text = (
                        f"📥 **Downloading...**\n"
                        f"{display_name}\n\n"
                        f"📊 Progress: {percent}\n"
                        f"🚀 Speed: {speed}\n"
                        f"⏳ ETA: {eta}"
                    )
                    
                    # Schedule async edit in the main loop
                    asyncio.run_coroutine_threadsafe(
                        edit_progress_msg(chat_id, progress_message_id[0], progress_text, task_id_container[0]),
                        loop
                    )
        
        # Create download function wrapper
        def download_func():
            download_video(message_text, progress_hook=progress_hook)
        
        # Helper to delete processing message
        try:
            await processing_msg.delete()
        except:
            pass  # Ignore if already deleted or fails

        # Send download start notification (silent) with title
        status = download_manager.get_queue_status()
        start_msg = f"🎬 Starting download...\n{display_name}\n📊 Queue: {status['active'] + 1}/{status['max']} active"
        
        # Create async task for download and completion notification
        async def download_and_notify():
            try:
                # Queue and execute download
                task_id, future = await download_manager.submit_download(
                    download_func=download_func,
                    task_type='youtube',
                    url=message_text,
                    user_id=user_id,
                    chat_id=chat_id
                )
                task_id_container[0] = task_id
                
                # Add cancel button
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("🛑 Cancel", callback_data=f"cancel_{task_id}")]
                ])
                
                # Send start message with cancel button
                start_msg_obj = await context.bot.send_message(
                    chat_id=chat_id,
                    text=start_msg,
                    reply_markup=keyboard,
                    disable_notification=True
                )
                progress_message_id[0] = start_msg_obj.message_id
                
                # Wait for download completion
                await future
                
                # Send completion notification (silent) with title
                complete_msg = f"✅ Download complete!\n{display_name}"
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=complete_msg,
                    disable_notification=True
                )
            except CancelledError:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=f"❌ Download cancelled.\n{display_name}",
                    disable_notification=True
                )
            except Exception as e:
                logger.error(f"Error in download task: {e}")
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=Config.BOT_ERROR_MESSAGE,
                    disable_notification=True
                )
        
        # Start download task without waiting (fire-and-forget)
        asyncio.create_task(download_and_notify())
        
    except Exception as e:
        logger.error(f"Error processing YouTube link: {e}")
        await update.message.reply_text(Config.BOT_ERROR_MESSAGE)


@check_auth
async def handle_telegram_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle Telegram video downloads with concurrent support."""
    if not Config.AUTO_DOWNLOAD_TELEGRAM_VIDEOS:
        return
    
    video = update.message.video
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    
    try:
        # Check video size first
        if video.file_size > Config.TELEGRAM_VIDEO_MAX_SIZE:
            await update.message.reply_text(Config.BOT_TELEGRAM_VIDEO_TOO_LARGE)
            return
        
        # Get queue status before queueing
        queue_status_before = download_manager.get_queue_status()
        
        # Notify user if they need to wait
        if queue_status_before['active'] >= queue_status_before['max']:
            position = queue_status_before['total'] + 1
            total = position
            queue_msg = Config.BOT_QUEUE_MESSAGE.format(position=position, total=total)
            await update.message.reply_text(queue_msg, disable_notification=True)
        
        video_info = get_video_info(video)
        logger.info(f"Queueing Telegram video download for user {user_id}: {video_info}")
        
        # Create download function wrapper
        async def download_func_async():
            await download_telegram_video(video, context)
        
        def download_func():
            # Run async function in sync context
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(download_func_async())
            finally:
                loop.close()
        
        # Queue status
        status = download_manager.get_queue_status()
        video_size_mb = video.file_size / (1024 * 1024)
        start_msg = f"📥 Telegram video queued...\n📹 Size: {video_size_mb:.1f}MB\n📊 Queue: {status['active'] + 1}/{status['max']} active"
        
        # Progress tracking (for Telegram videos, mainly for cancel button)
        progress_message_id = [None] # Store message ID for editing
        task_id_container = [None] # Store task ID for cancel button
        
        # Create async task for download and completion notification
        async def download_and_notify():
            try:
                # Queue and execute download
                task_id, future = await download_manager.submit_download(
                    download_func=download_func,
                    task_type='telegram',
                    url=video.file_id,
                    user_id=user_id,
                    chat_id=chat_id
                )
                task_id_container[0] = task_id
                
                # Add cancel button
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("🛑 Cancel", callback_data=f"cancel_{task_id}")]
                ])
                
                # Send start message with cancel button
                start_msg_obj = await context.bot.send_message(
                    chat_id=chat_id,
                    text=start_msg,
                    reply_markup=keyboard,
                    disable_notification=True
                )
                progress_message_id[0] = start_msg_obj.message_id
                
                # Wait for download completion
                await future
                
                # Send completion notification (silent) with video info
                complete_msg = f"✅ Download complete!\n📹 Telegram video ({video_size_mb:.1f}MB)"
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=complete_msg,
                    disable_notification=True
                )
            except CancelledError:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=f"❌ Download cancelled.\n📹 Telegram video ({video_size_mb:.1f}MB)",
                    disable_notification=True
                )
            except Exception as e:
                logger.error(f"Error in Telegram video download task: {e}")
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=Config.BOT_ERROR_MESSAGE,
                    disable_notification=True
                )
        
        # Start download task without waiting (fire-and-forget)
        asyncio.create_task(download_and_notify())
        
    except ValueError as e:
        # Size limit error already handled above, but catch any other ValueError
        logger.error(f"Error processing Telegram video: {e}")
        await update.message.reply_text(str(e))
        logger.error(f"Error processing Telegram video: {e}")
        await update.message.reply_text(Config.BOT_ERROR_MESSAGE)


@check_auth
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming text messages (YouTube links)."""
    message_text = update.message.text
    
    # Check if message contains a YouTube link
    if is_valid_youtube_url(message_text):
        await handle_youtube_link(update, context)
    else:
        await update.message.reply_text("Please send a valid YouTube link or video.")


async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Log errors caused by updates."""
    logger.error(f"Update {update} caused error: {context.error}")


def main():
    """Start the bot."""
    global download_manager
    
    try:
        Config.validate()
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        raise
    
    # Initialize download manager
    download_manager = get_download_manager(max_concurrent=Config.MAX_CONCURRENT_DOWNLOADS)
    logger.info(f"Download manager initialized with max_concurrent={Config.MAX_CONCURRENT_DOWNLOADS}")
    
    # Initialize auth manager
    global auth_manager
    auth_manager = AuthManager()
    if auth_manager.is_auth_enabled():
        logger.info("Authentication enabled.")
    else:
        logger.info("Authentication disabled (no password set).")
    
    application = ApplicationBuilder().token(Config.BOT_TOKEN).build()

    # Register command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("queue", queue_status))
    application.add_handler(CommandHandler("auth", auth_command))
    application.add_handler(CallbackQueryHandler(cancel_callback))
    
    # Register message handlers
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.VIDEO, handle_telegram_video))
    
    # Register error handler
    application.add_error_handler(error)

    # Start the Bot
    logger.info("Starting bot...")
    application.run_polling()

if __name__ == '__main__':
    main()
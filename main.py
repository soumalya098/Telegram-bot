import os
from telegram import Update, InputFile, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from PIL import Image, ImageEnhance
import yt_dlp

# Replace with your bot token
BOT_TOKEN = "7719841823:AAH1nHOCsrrzM7BdpQVAJfkUxuKKYJQeRUA"

# Temporary directories for images and videos
TEMP_IMAGES_DIR = "temp_images"
TEMP_VIDEOS_DIR = "temp_videos"
os.makedirs(TEMP_IMAGES_DIR, exist_ok=True)
os.makedirs(TEMP_VIDEOS_DIR, exist_ok=True)

# Dictionary to store the latest image sent by each user
user_images = {}

# ---------------- /start Command ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a welcome image with a button when the user uses /start."""
    image_path = "welcome_image.jpeg"  # Place your welcome image here

    button = [[InlineKeyboardButton("𝐎ᴡɴᴇʀ", url="https://t.me/sarkar_shaabh")]]
    reply_markup = InlineKeyboardMarkup(button)

    if os.path.exists(image_path):
        with open(image_path, "rb") as image:
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=InputFile(image),
                caption="𝐖ᴇʟᴄᴏᴍᴇ , ᴛʜᴀɴᴋ ʏᴏᴜ ғᴏʀ ᴜsɪɴɢ ᴍᴇ , ʜᴏᴘᴇ ʏᴏᴜ ᴡɪʟʟ ғɪɴᴅ ᴍᴇ ᴜsᴇғᴜʟ ᴛᴏ ʏᴏᴜᴠ, ғᴏʀ ᴀɴʏ ɪssᴜᴇ ᴄᴏɴᴛᴀᴄᴛ ᴍʏ ᴏᴡɴᴇʀ",
                reply_markup=reply_markup
            )
    else:
        await update.message.reply_text("Welcome! The welcome image is missing, but you can still visit the channel using the button below.",
                                        reply_markup=reply_markup)

# ---------------- Image Handling and /upscale Command ----------------
async def receive_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Store the image sent by the user."""
    user_id = update.effective_user.id
    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)
    
    image_path = f"{TEMP_IMAGES_DIR}/{user_id}_original.jpg"
    await file.download_to_drive(image_path)
    user_images[user_id] = image_path

    await update.message.reply_text("Image received! Send /upscale to get an upscaled version of your image.")

async def upscale_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Upscale the last image sent by the user."""
    user_id = update.effective_user.id

    if user_id not in user_images or not os.path.exists(user_images[user_id]):
        await update.message.reply_text("No image found! Send an image first.")
        return
    
    input_path = user_images[user_id]
    output_path = f"{TEMP_IMAGES_DIR}/{user_id}_upscaled.jpg"

    try:
        # Open the image and upscale (resize and enhance)
        with Image.open(input_path) as img:
            upscaled_img = img.resize((img.width * 2, img.height * 2), Image.LANCZOS)
            enhancer = ImageEnhance.Sharpness(upscaled_img)
            upscaled_img = enhancer.enhance(2.0)
            upscaled_img.save(output_path, "JPEG")
        
        # Send the upscaled image
        with open(output_path, "rb") as image:
            await context.bot.send_photo(
                chat_id=update.effective_chat.id, 
                photo=InputFile(image), 
                caption="Here is your upscaled image!"
            )
    except Exception as e:
        await update.message.reply_text(f"Error processing the image: {str(e)}")

# ---------------- Social Media Video Handling ----------------
async def download_video(url: str, save_path: str):
    """Download a video from a given URL using yt_dlp."""
    ydl_opts = {
        "outtmpl": save_path,
        "format": "bestvideo+bestaudio/best",  
        "quiet": True,                        
        "noplaylist": True,                   
        "merge_output_format": "mp4"          
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return True
    except Exception as e:
        print(f"Error downloading video: {str(e)}")
        return False

async def handle_video_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Download and send a video from a social media link."""
    user_id = update.effective_user.id
    link = update.message.text.strip()

    if not link.startswith(("http://", "https://")):
        await update.message.reply_text("Please send a valid video link!")
        return

    await update.message.reply_text("Fetching the video... Please wait!")
    
    video_path = os.path.join(TEMP_VIDEOS_DIR, f"{user_id}_video.mp4")
    success = await download_video(link, video_path)

    if success and os.path.exists(video_path):
        try:
            with open(video_path, "rb") as video:
                await context.bot.send_video(chat_id=update.effective_chat.id, video=InputFile(video), caption="Here's your video!")
        except Exception as e:
            await update.message.reply_text(f"Error sending video: {str(e)}")
        finally:
            os.remove(video_path)  # Clean up after sending
    else:
        await update.message.reply_text("Failed to fetch the video. Please check the link and try again.")

# ---------------- Main Function ----------------
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Handlers
    app.add_handler(CommandHandler("start", start))  # Start command
    app.add_handler(MessageHandler(filters.PHOTO, receive_image))  # Handle image uploads
    app.add_handler(CommandHandler("upscale", upscale_image))  # Upscale images
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_video_link))  # Handle social media video links

    print("Bot is running... Press Ctrl+C to stop.")
    app.run_polling()

# ---------------- Run the Bot ----------------
if __name__ == "__main__":
    main()

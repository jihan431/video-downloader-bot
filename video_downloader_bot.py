"""
📸 Instagram & Facebook Video Downloader Bot - Telegram
Download video dari Instagram dan Facebook

Kirim link video, bot akan otomatis download dan kirim video-nya!
"""

import telebot
import yt_dlp
import os
import re
import uuid
from datetime import datetime

# ============ KONFIGURASI ============
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN tidak ditemukan! Set di environment variable.")
DOWNLOAD_DIR = "downloads"
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB (Telegram limit)

# =====================================

bot = telebot.TeleBot(BOT_TOKEN)

# Buat folder download jika belum ada
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Platform yang didukung
SUPPORTED_PLATFORMS = {
    'instagram': {
        'pattern': r'(instagram\.com|instagr\.am)',
        'emoji': '📸',
        'name': 'Instagram'
    },
    'facebook': {
        'pattern': r'(facebook\.com|fb\.watch|fb\.com)',
        'emoji': '📘',
        'name': 'Facebook'
    }
}

def detect_platform(url):
    """Deteksi platform dari URL"""
    for platform, info in SUPPORTED_PLATFORMS.items():
        if re.search(info['pattern'], url, re.IGNORECASE):
            return platform, info
    return None, None

def extract_url(text):
    """Extract URL dari text"""
    url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
    match = re.search(url_pattern, text)
    return match.group(0) if match else None

def download_video(url, chat_id):
    """Download video menggunakan yt-dlp"""
    filename = f"{chat_id}_{uuid.uuid4().hex[:8]}"
    output_path = os.path.join(DOWNLOAD_DIR, filename)
    
    ydl_opts = {
        'format': 'best[filesize<50M]/best',
        'outtmpl': f'{output_path}.%(ext)s',
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
        'socket_timeout': 30,
        'retries': 5,
        'merge_output_format': 'mp4',
        'geo_bypass': True,
        'geo_bypass_country': 'ID',
        'extractor_args': {
            'tiktok': {
                'api_hostname': 'api22-normal-c-useast2a.tiktokv.com',
            }
        },
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 13; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7',
            'Referer': 'https://www.tiktok.com/',
        }
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            
            # Cari file yang didownload
            ext = info.get('ext', 'mp4')
            downloaded_file = f"{output_path}.{ext}"
            
            # Cek apakah file ada
            if not os.path.exists(downloaded_file):
                # Coba cari dengan pattern
                for f in os.listdir(DOWNLOAD_DIR):
                    if f.startswith(f"{chat_id}_"):
                        downloaded_file = os.path.join(DOWNLOAD_DIR, f)
                        break
            
            return {
                'success': True,
                'file_path': downloaded_file,
                'title': info.get('title', 'Video')[:100],
                'duration': info.get('duration', 0),
                'uploader': info.get('uploader', info.get('channel', 'Unknown')),
            }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def cleanup_all_downloads():
    """Hapus semua file di folder downloads"""
    count = 0
    try:
        for f in os.listdir(DOWNLOAD_DIR):
            file_path = os.path.join(DOWNLOAD_DIR, f)
            if os.path.isfile(file_path):
                os.remove(file_path)
                count += 1
    except:
        pass
    return count

def cleanup_file(file_path):
    """Hapus file setelah dikirim"""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except:
        pass


@bot.message_handler(commands=['start'])
def cmd_start(message):
    """Handle /start command dengan menu"""
    text = "📸 *Instagram & Facebook Video Downloader*\n\n"
    text += "Selamat datang! Saya bisa download video dari Instagram dan Facebook.\n\n"
    text += "📌 *Cara Pakai:*\n"
    text += "_Kirim link video, saya akan download dan kirimkan!_\n\n"
    text += "📱 *Platform:*\n"
    text += "• 📸 Instagram (Reels, Post, Stories)\n"
    text += "• 📘 Facebook (Video, Reels)\n\n"
    text += "💡 Ketik /help untuk bantuan"
    
    # Inline keyboard menu
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        telebot.types.InlineKeyboardButton("📱 Platform", callback_data="platforms"),
        telebot.types.InlineKeyboardButton("❓ Bantuan", callback_data="help"),
        telebot.types.InlineKeyboardButton("ℹ️ About", callback_data="about")
    )
    
    bot.send_message(message.chat.id, text, parse_mode='Markdown', reply_markup=markup)

@bot.message_handler(commands=['help'])
def cmd_help(message):
    """Handle /help command"""
    text = "❓ *Bantuan*\n\n"
    text += "*Commands:*\n"
    text += "• /start - Menu utama\n"
    text += "• /help - Bantuan\n"
    text += "• /platforms - Platform yang didukung\n"
    text += "• /about - Tentang bot\n"
    text += "• /clear - Bersihkan cache\n\n"
    text += "*Cara Download:*\n"
    text += "1. Buka Instagram/Facebook\n"
    text += "2. Copy link video\n"
    text += "3. Kirim link ke bot\n"
    text += "4. Tunggu video dikirim!\n\n"
    text += "⚠️ _Maksimal ukuran file: 50MB_"
    
    bot.reply_to(message, text, parse_mode='Markdown')

@bot.message_handler(commands=['platforms'])
def cmd_platforms(message):
    """Handle /platforms command"""
    text = "📱 *Platform yang Didukung*\n\n"
    text += "📸 *Instagram*\n"
    text += "   • Reels\n"
    text += "   • Post video\n"
    text += "   • Stories (public)\n\n"
    text += "📘 *Facebook*\n"
    text += "   • Video post\n"
    text += "   • Reels\n"
    text += "   • fb.watch links"
    
    bot.reply_to(message, text, parse_mode='Markdown')

@bot.message_handler(commands=['about'])
def cmd_about(message):
    """Handle /about command"""
    text = "ℹ️ *About Bot*\n\n"
    text += "📸 *Instagram & Facebook Video Downloader*\n"
    text += "━━━━━━━━━━━━━━━\n\n"
    text += "Bot ini membantu kamu download video dari Instagram dan Facebook dengan mudah.\n\n"
    text += "🔧 *Tech:* Python + yt-dlp\n"
    text += "📦 *Max Size:* 50MB\n"
    text += f"📅 *Date:* {datetime.now().strftime('%Y')}\n\n"
    text += "Made with ❤️"
    
    bot.reply_to(message, text, parse_mode='Markdown')

@bot.message_handler(commands=['clear'])
def cmd_clear(message):
    """Handle /clear command - bersihkan cache downloads"""
    count = cleanup_all_downloads()
    bot.reply_to(message, f"🗑️ Cache dibersihkan!\n\n📁 {count} file dihapus.")

# Callback query handler untuk inline keyboard
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    """Handle inline keyboard callbacks"""
    if call.data == "platforms":
        text = "📱 *Platform yang Didukung*\n\n"
        text += "📸 Instagram • 📘 Facebook"
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, text, parse_mode='Markdown')
    
    elif call.data == "help":
        text = "❓ *Quick Help*\n\n"
        text += "Kirim link video dari Instagram/Facebook, bot akan otomatis download!"
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, text, parse_mode='Markdown')
    
    elif call.data == "about":
        text = "📸 IG & FB Downloader\n\nDownload video dengan mudah!"
        bot.answer_callback_query(call.id, text, show_alert=True)

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    """Handle semua pesan - cari URL dan download"""
    text = message.text
    
    # Cari URL dalam pesan
    url = extract_url(text)
    
    if not url:
        bot.reply_to(
            message, 
            "❌ Tidak ada link yang valid.\n\n"
            "Kirim link dari Instagram atau Facebook."
        )
        return
    
    # Deteksi platform
    platform, info = detect_platform(url)
    
    if not platform:
        bot.reply_to(
            message,
            "❌ Platform tidak didukung.\n\n"
            "Kirim link dari:\n"
            "• Instagram\n"
            "• Facebook"
        )
        return
    
    emoji = info['emoji']
    platform_name = info['name']
    
    # Kirim status downloading
    status_msg = bot.reply_to(
        message,
        f"{emoji} *Downloading dari {platform_name}...*\n\n"
        f"⏳ Mohon tunggu...",
        parse_mode='Markdown'
    )
    
    # Download video
    result = download_video(url, message.chat.id)
    
    if not result['success']:
        error_msg = result['error']
        # Simplify error message
        if 'Sign in' in error_msg or 'login' in error_msg.lower():
            error_msg = "Video privat atau memerlukan login"
        elif 'not available' in error_msg.lower():
            error_msg = "Video tidak tersedia"
        elif 'Unsupported URL' in error_msg:
            error_msg = "Link tidak valid atau video tidak ditemukan"
        else:
            error_msg = error_msg[:100]
        
        # Escape Markdown special characters
        for char in ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']:
            error_msg = error_msg.replace(char, f'\\{char}')
            
        bot.edit_message_text(
            f"❌ *Gagal download\\!*\n\n"
            f"Error: {error_msg}\n\n"
            f"_Pastikan link valid dan video bisa diakses publik\\._",
            message.chat.id,
            status_msg.message_id,
            parse_mode='MarkdownV2'
        )
        return
    
    file_path = result['file_path']
    
    # Cek file ada
    if not os.path.exists(file_path):
        bot.edit_message_text(
            "❌ *File tidak ditemukan setelah download.*",
            message.chat.id,
            status_msg.message_id,
            parse_mode='Markdown'
        )
        return
    
    file_size = os.path.getsize(file_path)
    
    # Cek ukuran file
    if file_size > MAX_FILE_SIZE:
        bot.edit_message_text(
            f"❌ *File terlalu besar!*\n\n"
            f"Ukuran: {file_size / (1024*1024):.1f} MB\n"
            f"Maksimal: 50 MB",
            message.chat.id,
            status_msg.message_id,
            parse_mode='Markdown'
        )
        cleanup_file(file_path)
        return
    
    # Update status
    bot.edit_message_text(
        f"📤 *Mengirim video...*\n\n"
        f"📁 {file_size / (1024*1024):.1f} MB",
        message.chat.id,
        status_msg.message_id,
        parse_mode='Markdown'
    )
    
    # Kirim video
    try:
        with open(file_path, 'rb') as video_file:
            caption = f"{emoji} *{result['title']}*\n"
            caption += f"👤 {result['uploader']}"
            
            bot.send_video(
                message.chat.id,
                video_file,
                caption=caption,
                parse_mode='Markdown',
                supports_streaming=True
            )
        
        # Hapus status message
        bot.delete_message(message.chat.id, status_msg.message_id)
        
    except Exception as e:
        # Jika gagal kirim sebagai video, coba sebagai dokumen
        try:
            with open(file_path, 'rb') as doc_file:
                bot.send_document(
                    message.chat.id,
                    doc_file,
                    caption=f"{emoji} {result['title']}"
                )
            bot.delete_message(message.chat.id, status_msg.message_id)
        except Exception as e2:
            bot.edit_message_text(
                f"❌ *Gagal mengirim!*\n\nError: {str(e2)[:50]}",
                message.chat.id,
                status_msg.message_id,
                parse_mode='Markdown'
            )
    
    # Cleanup
    cleanup_file(file_path)

def main():
    """Main function"""
    print("=" * 45)
    print("📸 Instagram & Facebook Video Downloader")
    print("=" * 45)
    print("📱 Supported: Instagram, Facebook")
    print("=" * 45)
    print("✅ Bot running... Press Ctrl+C to stop")
    print()
    
    bot.infinity_polling()

if __name__ == '__main__':
    main()

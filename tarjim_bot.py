import os
import anthropic
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)

TELEGRAM_TOKEN = "8651997587:AAGdXhtZ0IAsQgRFhkkve_XMiAutC03K2RE"
ANTHROPIC_API_KEY = "sk-ant-api03-SZD_P4XuY_WDWaf3d3wRcjARGPZuY0Gk3qHNW7y1SSeUGZFnXo5oeOOLqGO321Bs7stJ82OOiR-tiP6S552hWg-OqGlwQAA"

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

LANGUAGES = {
    "ar": "🇸🇦 العربية",
    "en": "🇬🇧 English",
    "ru": "🇷🇺 Русский",
    "fr": "🇫🇷 Français",
    "de": "🇩🇪 Deutsch",
    "es": "🇪🇸 Español",
    "it": "🇮🇹 Italiano",
    "tr": "🇹🇷 Türkçe",
    "zh": "🇨🇳 中文",
    "ja": "🇯🇵 日本語",
    "ko": "🇰🇷 한국어",
    "hi": "🇮🇳 हिन्दी",
    "pt": "🇧🇷 Português",
    "fa": "🇮🇷 فارسی",
    "ur": "🇵🇰 اردو",
    "nl": "🇳🇱 Nederlands",
    "pl": "🇵🇱 Polski",
    "sv": "🇸🇪 Svenska",
    "uk": "🇺🇦 Українська",
}

user_states = {}

def get_lang_keyboard(prefix="tgt"):
    keyboard = []
    langs = list(LANGUAGES.items())
    for i in range(0, len(langs), 2):
        row = []
        for code, name in langs[i:i+2]:
            row.append(InlineKeyboardButton(name, callback_data=f"{prefix}:{code}"))
        keyboard.append(row)
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = f"🌍 *أهلاً {user.first_name}\\! في TarjimAI*\n\nأنا مترجمك الذكي\\.\n\n*كيف تستخدمني:*\n1️⃣ أرسل لي أي نص\n2️⃣ اختر اللغة المصدر\n3️⃣ اختر اللغة الهدف\n4️⃣ استلم الترجمة فوراً ✨\n\n*أدعم ١٩ لغة\\!* 🚀"
    await update.message.reply_text(text, parse_mode="MarkdownV2")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    user_states[user_id] = {"text": text, "step": "choose_source"}
    await update.message.reply_text(
        f"📝 النص: {text[:100]}\n\n🔤 اختر لغة النص الأصلي:",
        reply_markup=get_lang_keyboard("src")
    )

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data
    if user_id not in user_states:
        await query.edit_message_text("⚠️ انتهت الجلسة، أرسل النص من جديد.")
        return
    state = user_states[user_id]
    if data.startswith("src:"):
        lang_code = data.split(":")[1]
        state["source"] = lang_code
        src_name = LANGUAGES.get(lang_code, lang_code)
        await query.edit_message_text(
            f"✅ المصدر: {src_name}\n\n🎯 الآن اختر اللغة المطلوبة:",
            reply_markup=get_lang_keyboard("tgt")
        )
    elif data.startswith("tgt:"):
        lang_code = data.split(":")[1]
        state["target"] = lang_code
        src_name = LANGUAGES.get(state["source"], state["source"])
        tgt_name = LANGUAGES.get(lang_code, lang_code)
        await query.edit_message_text(f"⏳ جاري الترجمة...\n\n{src_name} ← {tgt_name}")
        try:
            prompt = f"ترجم من {src_name} إلى {tgt_name} بشكل طبيعي وعامي. أعطِ الترجمة فقط:\n\n{state['text']}"
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )
            translation = response.content[0].text.strip()
            await query.edit_message_text(f"✨ الترجمة جاهزة!\n\nمن: {src_name}\nإلى: {tgt_name}\n\n📝 الأصل:\n{state['text']}\n\n🌍 الترجمة:\n{translation}\n\n_TarjimAI 🤖_")
        except Exception as e:
            await query.edit_message_text("❌ حدث خطأ، حاول مجدداً.")
        if user_id in user_states:
            del user_states[user_id]

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(handle_callback))
    print("✅ TarjimAI Bot يشتغل...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()

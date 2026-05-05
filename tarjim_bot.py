import os
import anthropic
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

LANGUAGES = {
    "ar": "العربية", "en": "English", "ru": "Русский",
    "fr": "Français", "de": "Deutsch", "es": "Español",
    "it": "Italiano", "tr": "Türkçe", "zh": "中文",
    "ja": "日本語", "ko": "한국어", "hi": "हिन्दी",
    "pt": "Português", "fa": "فارسی", "ur": "اردو",
}

user_states = {}

def get_keyboard(prefix):
    keyboard = []
    items = list(LANGUAGES.items())
    for i in range(0, len(items), 2):
        row = []
        for code, name in items[i:i+2]:
            row.append(InlineKeyboardButton(name, callback_data=f"{prefix}:{code}"))
        keyboard.append(row)
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("مرحبا! انا TarjimAI مترجمك الذكي.\n\nارسل اي نص وانا اترجمه لك!")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    user_states[user_id] = {"text": text}
    await update.message.reply_text(f"النص: {text[:80]}\n\nاختر لغة النص الاصلي:", reply_markup=get_keyboard("src"))

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data
    if user_id not in user_states:
        await query.edit_message_text("ارسل النص من جديد.")
        return
    state = user_states[user_id]
    if data.startswith("src:"):
        lang_code = data.split(":")[1]
        state["source"] = lang_code
        src_name = LANGUAGES.get(lang_code, lang_code)
        await query.edit_message_text(f"المصدر: {src_name}\n\nاختر اللغة المطلوبة:", reply_markup=get_keyboard("tgt"))
    elif data.startswith("tgt:"):
        lang_code = data.split(":")[1]
        state["target"] = lang_code
        src_name = LANGUAGES.get(state["source"], state["source"])
        tgt_name = LANGUAGES.get(lang_code, lang_code)
        await query.edit_message_text(f"جاري الترجمة...")
        try:
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1000,
                messages=[{"role": "user", "content": f"ترجم من {src_name} الى {tgt_name} بشكل طبيعي وعامي. اعط الترجمة فقط:\n\n{state['text']}"}]
            )
            translation = response.content[0].text.strip()
            await query.edit_message_text(f"من: {src_name} ➡️ {tgt_name}\n\nالاصل:\n{state['text']}\n\nالترجمة:\n{translation}")
        except Exception as e:
            await query.edit_message_text(f"حدث خطأ: {str(e)}")
        if user_id in user_states:
            del user_states[user_id]

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(handle_callback))
    print("TarjimAI Bot يشتغل...")
    app.run_polling(drop_pending_updates=True)

if name == "__main__":
    main()

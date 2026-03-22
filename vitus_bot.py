import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    ConversationHandler, filters, ContextTypes
)
 
# Konfiguration
BOT_TOKEN = "8744474198:AAFeUfDZB_A3O07FR2I-YIcKOuOChPoIgO0"
OWNER_CHAT_ID = 8612546855
 
# Gesprächs-Schritte
NAME, SERVICE, BESCHREIBUNG, FOTOS, TELEFON = range(5)
 
SERVICES = [
    "Kleinreparatur",
    "Grossreparatur",
    "Reinigung",
    "Naeharbeit",
]
 
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
 
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "Willkommen bei VITUS Camper-Service!\n\n"
        "Um eine Serviceanfrage zu stellen, gehen Sie bitte wie folgt vor:\n\n"
        "1. Geben Sie Ihren Namen ein\n"
        "2. Wahlen Sie einen oder mehrere Services aus - klicken Sie die Antworten einfach nacheinander an\n"
        "3. Beschreiben Sie das Problem\n"
        "4. Schicken Sie Fotos der Schaden\n"
        "5. Teilen Sie uns Ihre Telefonnummer mit\n\n"
        "Wie ist Ihr Name?",
        reply_markup=ReplyKeyboardRemove()
    )
    return NAME
 
async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()
    context.user_data["name"] = name
    context.user_data["username"] = f"@{update.message.from_user.username}" if update.message.from_user.username else "(kein Username)"
    context.user_data["services"] = []
 
    keyboard = [[KeyboardButton(s)] for s in SERVICES]
    keyboard.append([KeyboardButton("Weiter")])
 
    await update.message.reply_text(
        f"Guten Tag, {name}!\n\n"
        "Welchen Service benotigen Sie?\n"
        "Klicken Sie die gewunschten Services einfach nacheinander an.\n"
        "Wenn Sie fertig sind, drucken Sie auf Weiter.\n"
        "Sie konnen mehrere Services auswahlen.",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )
    return SERVICE
 
async def get_service(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
 
    if text == "Weiter":
        selected = context.user_data.get("services", [])
        if not selected:
            await update.message.reply_text("Bitte wahlen Sie mindestens einen Service aus.")
            return SERVICE
 
        await update.message.reply_text(
            f"Ausgewahlt: {', '.join(selected)}\n\n"
            "Bitte beschreiben Sie das Problem so genau wie moglich.",
            reply_markup=ReplyKeyboardRemove()
        )
        return BESCHREIBUNG
 
    if text in SERVICES:
        services = context.user_data.get("services", [])
        if text in services:
            services.remove(text)
            msg = f"{text} entfernt."
        else:
            services.append(text)
            msg = f"{text} hinzugefugt."
        context.user_data["services"] = services
        current = ", ".join(services) if services else "Noch nichts ausgewahlt"
        await update.message.reply_text(
            f"{msg}\n\nAktuell ausgewahlt: {current}\n\nWeitere Services auswahlen oder Weiter drucken."
        )
        return SERVICE
 
    await update.message.reply_text("Bitte wahlen Sie einen Service aus der Liste oder drucken Sie Weiter.")
    return SERVICE
 
async def get_beschreibung(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["beschreibung"] = update.message.text.strip()
    context.user_data["fotos"] = []
 
    await update.message.reply_text(
        "Bitte schicken Sie uns Fotos der Schaden.\n\n"
        "Schicken Sie alle Fotos nacheinander. Wenn Sie fertig sind, drucken Sie auf Fertig.",
        reply_markup=ReplyKeyboardMarkup([[KeyboardButton("Fertig")]], resize_keyboard=True)
    )
    return FOTOS
 
async def get_fotos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.photo:
        foto = update.message.photo[-1]
        context.user_data["fotos"].append(foto.file_id)
        anzahl = len(context.user_data["fotos"])
        await update.message.reply_text(
            f"Foto {anzahl} erhalten. Weitere Fotos schicken oder Fertig drucken."
        )
        return FOTOS
 
    if update.message.text and "Fertig" in update.message.text:
        keyboard = [[KeyboardButton("Telefonnummer teilen", request_contact=True)]]
        await update.message.reply_text(
            "Bitte teilen Sie uns Ihre Telefonnummer mit, damit wir Sie fur das Angebot erreichen konnen.\n\n"
            "Drucken Sie den Knopf unten um Ihre Nummer automatisch zu teilen,\n"
            "oder geben Sie sie manuell ein.",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
        )
        return TELEFON
 
    await update.message.reply_text("Bitte schicken Sie Fotos oder drucken Sie Fertig.")
    return FOTOS
 
async def get_telefon(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.contact:
        telefon = update.message.contact.phone_number
    else:
        telefon = update.message.text.strip()
    context.user_data["telefon"] = telefon
    await abschliessen(update, context)
    return ConversationHandler.END
 
async def abschliessen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name         = context.user_data.get("name", "Unbekannt")
    username     = context.user_data.get("username", "")
    telefon      = context.user_data.get("telefon", "Nicht angegeben")
    services     = context.user_data.get("services", [])
    beschreibung = context.user_data.get("beschreibung", "")
    fotos        = context.user_data.get("fotos", [])
 
    await update.message.reply_text(
        f"Vielen Dank, {name}!\n\n"
        "Wir haben Ihre Anfrage erhalten und werden die Fotos analysieren.\n"
        "Sie erhalten so schnell wie moglich ein individuelles Angebot von uns.\n\n"
        "Ihr VITUS Camper-Service Team",
        reply_markup=ReplyKeyboardRemove()
    )
 
    services_text = ", ".join(services) if services else "Keine Angabe"
    zusammenfassung = (
        f"Neue Anfrage\n\n"
        f"Name: {name}\n"
        f"Telegram: {username}\n"
        f"Telefon: {telefon}\n"
        f"Services: {services_text}\n\n"
        f"Beschreibung:\n{beschreibung}\n\n"
        f"Fotos: {len(fotos)} Stueck"
    )
 
    await context.bot.send_message(chat_id=OWNER_CHAT_ID, text=zusammenfassung)
 
    for file_id in fotos:
        await context.bot.send_photo(chat_id=OWNER_CHAT_ID, photo=file_id)
 
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Anfrage abgebrochen. Tippen Sie /start um neu zu beginnen.",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END
 
def main():
    app = Application.builder().token(BOT_TOKEN).build()
 
    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            NAME:         [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            SERVICE:      [MessageHandler(filters.TEXT & ~filters.COMMAND, get_service)],
            BESCHREIBUNG: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_beschreibung)],
            FOTOS: [
                MessageHandler(filters.PHOTO, get_fotos),
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_fotos),
            ],
            TELEFON: [
                MessageHandler(filters.CONTACT, get_telefon),
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_telefon),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
 
    app.add_handler(conv)
    print("VITUS Bot laeuft...")
    app.run_polling()
 
if __name__ == "__main__":
    main()
 

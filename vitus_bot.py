import logging
import asyncio
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    ConversationHandler, filters, ContextTypes
)
 
# ── Konfiguration ──────────────────────────────────────────
BOT_TOKEN = "8744474198:AAFeUfDZB_A3O07FR2I-YIcKOuOChPoIgO0"
OWNER_CHAT_ID = 8612546855  # Ihre Chat-ID
 
# ── Gesprächs-Schritte ─────────────────────────────────────
NAME, TELEFON, SERVICE, BESCHREIBUNG, FOTOS = range(5)
 
SERVICES = [
    "🔧 Kleinreparatur",
    "🏗️ Großreparatur",
    "✨ Reinigung",
    "🧵 Näharbeit",
]
 
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
 
# ── /start ─────────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "👋 Willkommen bei *VITUS Camper-Service*!\n\n"
        "Ich helfe Ihnen dabei, eine Serviceanfrage zu stellen.\n\n"
        "Wie ist Ihr Name?",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove()
    )
    return NAME
 
# ── Schritt 1: Name ────────────────────────────────────────
async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()
    context.user_data["name"] = name
    context.user_data["username"] = f"@{update.message.from_user.username}" if update.message.from_user.username else "(kein Username)"
    context.user_data["services"] = []
 
    keyboard = [[KeyboardButton("📱 Telefonnummer teilen", request_contact=True)]]
    await update.message.reply_text(
        f"Schön, *{name}*! 😊\n\n"
        "Bitte teilen Sie uns Ihre *Telefonnummer* mit damit wir Sie kontaktieren können.\n\n"
        "Tippen Sie auf den Knopf unten oder tippen Sie Ihre Nummer manuell ein:",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    )
    return TELEFON
 
# ── Schritt 2: Telefonnummer ───────────────────────────────
async def get_telefon(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.contact:
        context.user_data["telefon"] = update.message.contact.phone_number
    else:
        context.user_data["telefon"] = update.message.text.strip()
 
    keyboard = [[KeyboardButton(s)] for s in SERVICES]
    keyboard.append([KeyboardButton("✅ Weiter")])
 
    await update.message.reply_text(
        "✅ Danke!\n\n"
        "Welchen Service benötigen Sie?\n"
        "Sie können *mehrere auswählen* – tippen Sie auf einen Service und dann auf ✅ Weiter.",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )
    return SERVICE
 
# ── Schritt 2: Service auswählen ───────────────────────────
async def get_service(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
 
    if text == "✅ Weiter":
        selected = context.user_data.get("services", [])
        if not selected:
            await update.message.reply_text(
                "⚠️ Bitte wählen Sie mindestens einen Service aus.",
            )
            return SERVICE
 
        await update.message.reply_text(
            f"✅ Ausgewählt: *{', '.join(selected)}*\n\n"
            "Bitte beschreiben Sie das Problem so genau wie möglich.",
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardRemove()
        )
        return BESCHREIBUNG
 
    # Service hinzufügen oder entfernen
    if text in SERVICES:
        services = context.user_data.get("services", [])
        if text in services:
            services.remove(text)
            msg = f"❌ *{text}* entfernt."
        else:
            services.append(text)
            msg = f"✅ *{text}* hinzugefügt."
        context.user_data["services"] = services
 
        current = ", ".join(services) if services else "Noch nichts ausgewählt"
        await update.message.reply_text(
            f"{msg}\n\nAktuell ausgewählt: *{current}*\n\nWeitere Services tippen oder ✅ Weiter drücken.",
            parse_mode="Markdown"
        )
        return SERVICE
 
    await update.message.reply_text("Bitte wählen Sie einen Service aus der Liste oder tippen Sie ✅ Weiter.")
    return SERVICE
 
# ── Schritt 3: Problembeschreibung ────────────────────────
async def get_beschreibung(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["beschreibung"] = update.message.text.strip()
    context.user_data["fotos"] = []
 
    await update.message.reply_text(
        "📸 Bitte schicken Sie uns ein paar *Fotos der Schäden*.\n\n"
        "Wenn Sie fertig sind, tippen Sie *Fertig*.",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup([[KeyboardButton("✅ Fertig")]], resize_keyboard=True)
    )
    return FOTOS
 
# ── Schritt 4: Fotos empfangen ────────────────────────────
async def get_fotos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.photo:
        # Höchste Auflösung nehmen
        foto = update.message.photo[-1]
        context.user_data["fotos"].append(foto.file_id)
        anzahl = len(context.user_data["fotos"])
        await update.message.reply_text(
            f"✅ Foto {anzahl} erhalten! Weitere Fotos schicken oder ✅ Fertig tippen."
        )
        return FOTOS
 
    if update.message.text and "Fertig" in update.message.text:
        await abschliessen(update, context)
        return ConversationHandler.END
 
    await update.message.reply_text("Bitte schicken Sie Fotos oder tippen Sie ✅ Fertig.")
    return FOTOS
 
# ── Anfrage abschließen & an Besitzer senden ──────────────
async def abschliessen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name        = context.user_data.get("name", "Unbekannt")
    username    = context.user_data.get("username", "")
    telefon     = context.user_data.get("telefon", "Nicht angegeben")
    services    = context.user_data.get("services", [])
    beschreibung = context.user_data.get("beschreibung", "")
    fotos       = context.user_data.get("fotos", [])
 
    # Danke-Nachricht an Kunden
    await update.message.reply_text(
        f"🙏 Vielen Dank, *{name}*!\n\n"
        "Wir haben Ihre Anfrage erhalten und werden die Fotos analysieren.\n"
        "Sie erhalten *so schnell wie möglich* ein individuelles Angebot von uns.\n\n"
        "Ihr VITUS Camper-Service Team 🚐",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove()
    )
 
    # Zusammenfassung an Besitzer
    services_text = "\n".join(f"  • {s}" for s in services) if services else "  • Keine Angabe"
    telefon     = context.user_data.get("telefon", "Keine Angabe")
    zusammenfassung = (
        f"🚐 *Neue Anfrage – Wohnwagen von {name}*\n\n"
        f"👤 Kunde: *{name}* ({username})\n"
        f"📱 Telefon: *{telefon}*\n"
        f"📱 Telefon: *{telefon}*\n"
        f"🔧 Services:\n{services_text}\n\n"
        f"📝 Beschreibung:\n_{beschreibung}_\n\n"
        f"📸 Fotos: {len(fotos)} Stück"
    )
 
    await context.bot.send_message(
        chat_id=OWNER_CHAT_ID,
        text=zusammenfassung,
        parse_mode="Markdown"
    )
 
    # Fotos an Besitzer weiterleiten
    for file_id in fotos:
        await context.bot.send_photo(chat_id=OWNER_CHAT_ID, photo=file_id)
 
# ── Abbrechen ─────────────────────────────────────────────
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Anfrage abgebrochen. Tippen Sie /start um neu zu beginnen.",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END
 
# ── Bot starten ───────────────────────────────────────────
def main():
    app = Application.builder().token(BOT_TOKEN).build()
 
    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            NAME:         [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            TELEFON:      [MessageHandler(filters.CONTACT | filters.TEXT & ~filters.COMMAND, get_telefon)],
            TELEFON:      [
                MessageHandler(filters.CONTACT, get_telefon),
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_telefon),
            ],
            SERVICE:      [MessageHandler(filters.TEXT & ~filters.COMMAND, get_service)],
            BESCHREIBUNG: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_beschreibung)],
            FOTOS:        [
                MessageHandler(filters.PHOTO, get_fotos),
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_fotos),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
 
    app.add_handler(conv)
    print("✅ VITUS Bot läuft...")
    app.run_polling()
 
if __name__ == "__main__":
    main()

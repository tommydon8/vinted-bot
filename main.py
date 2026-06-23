"""
Vinted Price Bot — monitora Vinted e avvisa su Telegram quando trova
articoli tra 1 e 10 euro dei brand preferiti dell'utente.
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

import database as db
from vinted_api import search_items, search_brands
from config import TELEGRAM_BOT_TOKEN, BASE_URL, PRICE_MIN, PRICE_MAX, POLL_INTERVAL

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ── ConversationHandler states ────────────────────────────────────────────────
WAITING_BRAND_NAME = 0
CHOOSING_BRAND = 1

# ── Testi riutilizzabili ──────────────────────────────────────────────────────
HELP_TEXT = (
    "👋 *Benvenuto nel Vinted Price Bot!*\n\n"
    f"Ti avviso su Telegram ogni volta che trovo un articolo dei tuoi brand "
    f"preferiti a meno di *{PRICE_MAX:.0f}€* su Vinted 🛍\n\n"
    "📋 *Comandi disponibili:*\n"
    "• /aggiungi — Aggiungi un brand da monitorare\n"
    "• /rimuovi — Rimuovi un brand\n"
    "• /marche — Vedi i tuoi brand salvati\n"
    "• /cerca — Cerca subito (senza aspettare)\n"
    "• /reset — Dimentica gli articoli già visti\n"
    "• /aiuto — Mostra questo messaggio\n\n"
    "💡 _Aggiungi almeno un brand per iniziare!_"
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _register(update: Update) -> None:
    u = update.effective_user
    db.upsert_user(u.id, u.username, u.first_name)


async def _send_item(bot, user_id: int, item: dict) -> None:
    price = item.get("price", {})
    amount = price.get("amount", "?")
    currency = price.get("currency_code", "EUR")
    brand = item.get("brand_title", "")
    size = item.get("size_title", "") or "—"
    title = item.get("title", "Articolo senza titolo")
    condition = item.get("status", "")
    item_id = item.get("id", "")
    url = f"{BASE_URL}/items/{item_id}"

    caption = (
        f"🛍 *Nuovo articolo trovato!*\n\n"
        f"*{title}*\n"
        f"💶 *{amount} {currency}*\n"
        f"👟 Brand: {brand}\n"
        f"📏 Taglia: {size}\n"
        f"🏷 Condizione: {condition}"
    )

    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("🛒 Vedi su Vinted", url=url)
    ]])

    photos = item.get("photos", [])
    photo_url = photos[0].get("url") if photos else None

    try:
        if photo_url:
            await bot.send_photo(
                user_id,
                photo=photo_url,
                caption=caption,
                parse_mode="Markdown",
                reply_markup=keyboard,
            )
        else:
            await bot.send_message(
                user_id,
                f"{caption}\n\n🔗 {url}",
                parse_mode="Markdown",
                reply_markup=keyboard,
            )
    except Exception as e:
        logger.warning(f"Impossibile inviare articolo {item_id} a {user_id}: {e}")


async def _scan_for_user(bot, user_id: int, announce_empty: bool = False) -> int:
    brands = db.get_user_brands(user_id)
    if not brands:
        return 0

    brand_ids = [bid for _, bid in brands]
    try:
        items = search_items(brand_ids)
    except PermissionError:
        await bot.send_message(
            user_id,
            "❌ Il cookie di Vinted è scaduto. Chiedi all'amministratore del bot di aggiornarlo.",
        )
        return 0
    except Exception as e:
        logger.error(f"Errore API per user {user_id}: {e}")
        return 0

    count = 0
    for item in items:
        item_id = item.get("id")
        if item_id and not db.is_seen(user_id, item_id):
            db.mark_seen(user_id, item_id)
            await _send_item(bot, user_id, item)
            count += 1

    if count == 0 and announce_empty:
        await bot.send_message(
            user_id,
            "😔 Nessun nuovo articolo trovato in questo momento.\nRicontrollerò automaticamente ogni minuto!",
        )
    return count


# ── Command handlers ──────────────────────────────────────────────────────────

async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    _register(update)
    await update.message.reply_text(HELP_TEXT, parse_mode="Markdown")


async def cmd_aiuto(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(HELP_TEXT, parse_mode="Markdown")


async def cmd_marche(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    _register(update)
    brands = db.get_user_brands(update.effective_user.id)
    if not brands:
        await update.message.reply_text(
            "Non hai ancora aggiunto brand.\nUsa /aggiungi per iniziare!"
        )
        return
    lines = "\n".join(f"• {name}" for name, _ in brands)
    await update.message.reply_text(
        f"👟 *I tuoi brand monitorati:*\n\n{lines}\n\n"
        f"💶 Range prezzo: {PRICE_MIN:.0f}€ – {PRICE_MAX:.0f}€",
        parse_mode="Markdown",
    )


async def cmd_cerca(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    _register(update)
    user_id = update.effective_user.id
    if not db.get_user_brands(user_id):
        await update.message.reply_text(
            "Non hai brand salvati.\nUsa /aggiungi per aggiungerne uno!"
        )
        return
    await update.message.reply_text("🔍 Ricerca in corso...")
    await _scan_for_user(ctx.bot, user_id, announce_empty=True)


async def cmd_reset(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    _register(update)
    db.reset_seen(update.effective_user.id)
    await update.message.reply_text(
        "✅ Fatto! La prossima ricerca ti mostrerà tutti gli articoli, "
        "anche quelli già visti in precedenza."
    )


# ── Aggiungi brand (ConversationHandler) ─────────────────────────────────────

async def cmd_aggiungi_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    _register(update)
    await update.message.reply_text(
        "🔍 Scrivi il nome del brand che vuoi aggiungere:\n"
        "_(es. Nike, Zara, Adidas, H&M...)_\n\n"
        "Digita /annulla per tornare al menu.",
        parse_mode="Markdown",
    )
    return WAITING_BRAND_NAME


async def aggiungi_receive_name(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.message.text.strip()
    await update.message.reply_text(f'🔎 Cerco "{query}" su Vinted...')

    try:
        results = search_brands(query)
    except Exception as e:
        await update.message.reply_text(f"❌ Errore nella ricerca: {e}\nRiprova più tardi.")
        return ConversationHandler.END

    if not results:
        await update.message.reply_text(
            f'😕 Nessun brand trovato per "{query}".\n'
            "Prova con un nome diverso, oppure /annulla."
        )
        return WAITING_BRAND_NAME

    # Salva i risultati in memoria temporanea per evitare il limite 64-byte dei callback
    ctx.user_data["brand_results"] = results[:8]

    keyboard = [
        [InlineKeyboardButton(b["title"], callback_data=f"add|{i}")]
        for i, b in enumerate(results[:8])
    ]
    keyboard.append([InlineKeyboardButton("❌ Annulla", callback_data="add|cancel")])

    await update.message.reply_text(
        f'Ho trovato questi brand per "{query}".\nQuale vuoi aggiungere? 👇',
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return CHOOSING_BRAND


async def aggiungi_choose_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    data = query.data  # "add|0" oppure "add|cancel"
    _, value = data.split("|", 1)

    if value == "cancel":
        await query.edit_message_text("❌ Operazione annullata.")
        return ConversationHandler.END

    idx = int(value)
    results = ctx.user_data.get("brand_results", [])
    if idx >= len(results):
        await query.edit_message_text("❌ Selezione non valida. Riprova con /aggiungi.")
        return ConversationHandler.END

    brand = results[idx]
    user_id = query.from_user.id
    added = db.add_brand(user_id, brand["title"], brand["id"])

    if added:
        await query.edit_message_text(
            f"✅ *{brand['title']}* aggiunto!\n\n"
            "Da ora ti avviserò quando trovo articoli di questo brand tra "
            f"{PRICE_MIN:.0f}€ e {PRICE_MAX:.0f}€ 🎉",
            parse_mode="Markdown",
        )
    else:
        await query.edit_message_text(
            f"ℹ️ Hai già *{brand['title']}* tra i tuoi brand monitorati.",
            parse_mode="Markdown",
        )
    return ConversationHandler.END


async def cmd_annulla(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("❌ Operazione annullata.")
    return ConversationHandler.END


# ── Rimuovi brand ─────────────────────────────────────────────────────────────

async def cmd_rimuovi(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    _register(update)
    user_id = update.effective_user.id
    brands = db.get_user_brands(user_id)

    if not brands:
        await update.message.reply_text(
            "Non hai brand salvati da rimuovere.\nUsa /aggiungi per aggiungerne uno!"
        )
        return

    keyboard = [
        [InlineKeyboardButton(f"🗑 {name}", callback_data=f"rm|{bid}|{name}")]
        for name, bid in brands
    ]
    keyboard.append([InlineKeyboardButton("❌ Annulla", callback_data="rm|cancel|")])

    await update.message.reply_text(
        "Quale brand vuoi rimuovere? 👇",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def rimuovi_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    parts = query.data.split("|", 2)
    _, value, name = parts

    if value == "cancel":
        await query.edit_message_text("❌ Operazione annullata.")
        return

    db.remove_brand(query.from_user.id, int(value))
    await query.edit_message_text(
        f"✅ Brand *{name}* rimosso con successo.", parse_mode="Markdown"
    )


# ── Background polling job ────────────────────────────────────────────────────

async def job_poll_vinted(ctx: ContextTypes.DEFAULT_TYPE) -> None:
    user_ids = db.get_all_active_user_ids()
    if not user_ids:
        return
    logger.info(f"Polling Vinted per {len(user_ids)} utente/i...")
    for user_id in user_ids:
        await _scan_for_user(ctx.bot, user_id)


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    if not TELEGRAM_BOT_TOKEN:
        raise SystemExit("❌ TELEGRAM_BOT_TOKEN non configurato nel file .env")

    db.init_db()

    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # ConversationHandler per aggiungere brand
    add_brand_conv = ConversationHandler(
        entry_points=[CommandHandler("aggiungi", cmd_aggiungi_start)],
        states={
            WAITING_BRAND_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, aggiungi_receive_name)
            ],
            CHOOSING_BRAND: [
                CallbackQueryHandler(aggiungi_choose_callback, pattern=r"^add\|")
            ],
        },
        fallbacks=[CommandHandler("annulla", cmd_annulla)],
    )

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("aiuto", cmd_aiuto))
    app.add_handler(CommandHandler("marche", cmd_marche))
    app.add_handler(CommandHandler("cerca", cmd_cerca))
    app.add_handler(CommandHandler("reset", cmd_reset))
    app.add_handler(add_brand_conv)
    app.add_handler(CommandHandler("rimuovi", cmd_rimuovi))
    app.add_handler(CallbackQueryHandler(rimuovi_callback, pattern=r"^rm\|"))

    # Polling automatico Vinted
    app.job_queue.run_repeating(job_poll_vinted, interval=POLL_INTERVAL, first=15)

    logger.info(f"Bot avviato — polling ogni {POLL_INTERVAL}s")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()

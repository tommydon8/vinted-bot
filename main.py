"""
Vinted Price Bot — trova articoli sotto i 10€ su richiesta.
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
from vinted_api import search_items_by_brand_name
from config import TELEGRAM_BOT_TOKEN, BASE_URL, PRICE_MIN, PRICE_MAX, POLL_INTERVAL

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

WAITING_BRAND_NAME = 0
WAITING_PRICE = 2

HELP_TEXT = (
    "👋 *Benvenuto nel Vinted Price Bot!*\n\n"
    f"Trova articoli dei tuoi brand preferiti sotto i *{PRICE_MAX:.0f}€* su Vinted 🛍\n\n"
    "📋 *Comandi disponibili:*\n"
    "• /aggiungi — Scegli il brand da cercare (sostituisce quello attuale)\n"
    "• /altri — Ricevi altri 20 articoli del brand attuale\n"
    "• /prezzo — Imposta il prezzo massimo (es. 5.50)\n"
    "• /marche — Vedi il brand e il prezzo attuale\n"
    "• /reset — Dimentica gli articoli già visti\n"
    "• /aiuto — Mostra questo messaggio\n\n"
    "💡 _Puoi avere un solo brand alla volta — /aggiungi lo sostituisce._"
)


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
        f"🛍 *Articolo trovato!*\n\n"
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
                user_id, photo=photo_url, caption=caption,
                parse_mode="Markdown", reply_markup=keyboard,
            )
        else:
            await bot.send_message(
                user_id, f"{caption}\n\n🔗 {url}",
                parse_mode="Markdown", reply_markup=keyboard,
            )
    except Exception as e:
        logger.warning(f"Impossibile inviare articolo {item_id} a {user_id}: {e}")


async def _fetch_and_send(bot, user_id: int) -> int:
    """Cerca articoli per tutti i brand dell'utente e ne manda al massimo 20."""
    brands = db.get_user_brands(user_id)
    if not brands:
        return 0

    count = 0
    for brand_name, _ in brands:
        if count >= 20:
            break
        try:
            price_max = db.get_max_price(user_id)
        items = search_items_by_brand_name(brand_name, price_max)
        except PermissionError:
            await bot.send_message(user_id, "❌ Errore di autenticazione con Vinted. Riprova più tardi.")
            return 0
        except Exception as e:
            logger.error(f"Errore API per user {user_id}, brand {brand_name}: {e}")
            continue

        for item in items:
            if count >= 20:
                break
            item_id = item.get("id")
            if item_id and not db.is_seen(user_id, item_id):
                db.mark_seen(user_id, item_id)
                await _send_item(bot, user_id, item)
                count += 1

    return count


# ── Comandi ───────────────────────────────────────────────────────────────────

async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    _register(update)
    await update.message.reply_text(HELP_TEXT, parse_mode="Markdown")


async def cmd_aiuto(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(HELP_TEXT, parse_mode="Markdown")


async def cmd_marche(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    _register(update)
    user_id = update.effective_user.id
    brands = db.get_user_brands(user_id)
    price_max = db.get_max_price(user_id)
    if not brands:
        await update.message.reply_text("Non hai ancora scelto un brand.\nUsa /aggiungi per iniziare!")
        return
    brand_name = brands[0][0]
    await update.message.reply_text(
        f"👟 *Brand attuale:* {brand_name}\n"
        f"💶 Range prezzo: {PRICE_MIN:.0f}€ – {price_max:.2f}€\n\n"
        f"Usa /aggiungi per cambiare brand.\n"
        f"Usa /prezzo per cambiare il prezzo massimo.",
        parse_mode="Markdown",
    )


async def cmd_prezzo_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    _register(update)
    user_id = update.effective_user.id
    price_max = db.get_max_price(user_id)
    await update.message.reply_text(
        f"💶 Prezzo massimo attuale: *{price_max:.2f}€*\n\n"
        f"Scrivi il nuovo prezzo massimo (minimo 1€):\n"
        f"_(es. 5, 7.50, 1.19...)_\n\n"
        f"Digita /annulla per tornare al menu.",
        parse_mode="Markdown",
    )
    return WAITING_PRICE


async def cmd_prezzo_receive(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip().replace(",", ".")
    try:
        price = float(text)
        if price < 1:
            raise ValueError
    except ValueError:
        await update.message.reply_text(
            "❌ Prezzo non valido. Inserisci un numero maggiore o uguale a 1 (es. 5, 7.50)."
        )
        return WAITING_PRICE

    user_id = update.effective_user.id
    db.set_max_price(user_id, price)
    await update.message.reply_text(
        f"✅ Prezzo massimo impostato a *{price:.2f}€*!\n\n"
        f"Usa /altri per cercare articoli con il nuovo range.",
        parse_mode="Markdown",
    )
    return ConversationHandler.END


async def cmd_piu(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Manda altri 20 articoli dei brand salvati."""
    _register(update)
    user_id = update.effective_user.id
    if not db.get_user_brands(user_id):
        await update.message.reply_text("Non hai brand salvati.\nUsa /aggiungi per aggiungerne uno!")
        return
    await update.message.reply_text("🔍 Cerco altri articoli...")
    count = await _fetch_and_send(ctx.bot, user_id)
    if count == 0:
        await update.message.reply_text(
            "😔 Nessun nuovo articolo trovato al momento.\n"
            "Riprova più tardi oppure usa /reset per rivedere quelli già mostrati."
        )


async def cmd_reset(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    _register(update)
    db.reset_seen(update.effective_user.id)
    await update.message.reply_text("✅ Fatto! Ora con /+ rivedrai tutti gli articoli dall'inizio.")


# ── Aggiungi brand ────────────────────────────────────────────────────────────

async def cmd_aggiungi_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    _register(update)
    await update.message.reply_text(
        "✏️ Scrivi il nome del brand che vuoi cercare:\n"
        "_(es. Nike, Ralph Lauren, Zara, Adidas...)_\n\n"
        "Digita /annulla per tornare al menu.",
        parse_mode="Markdown",
    )
    return WAITING_BRAND_NAME


async def aggiungi_receive_name(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    brand_name = update.message.text.strip()
    if not brand_name:
        await update.message.reply_text("Nome non valido, riprova.")
        return WAITING_BRAND_NAME

    user_id = update.effective_user.id
    added = db.add_brand(user_id, brand_name, 0)

    if added:
        await update.message.reply_text(
            f"✅ *{brand_name}* aggiunto!\n\n🔍 Cerco i primi 20 articoli...",
            parse_mode="Markdown",
        )
    else:
        await update.message.reply_text(
            f"ℹ️ Hai già *{brand_name}* salvato.\n\n🔍 Cerco 20 articoli...",
            parse_mode="Markdown",
        )

    count = await _fetch_and_send(update.get_bot(), user_id)
    if count == 0:
        await update.message.reply_text(
            "😔 Nessun articolo trovato al momento.\nRiprova con /+ più tardi."
        )

    return ConversationHandler.END


async def cmd_annulla(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("❌ Operazione annullata.")
    return ConversationHandler.END




# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    if not TELEGRAM_BOT_TOKEN:
        raise SystemExit("❌ TELEGRAM_BOT_TOKEN non configurato nel file .env")

    db.init_db()

    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    add_brand_conv = ConversationHandler(
        entry_points=[CommandHandler("aggiungi", cmd_aggiungi_start)],
        states={
            WAITING_BRAND_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, aggiungi_receive_name)
            ],
        },
        fallbacks=[CommandHandler("annulla", cmd_annulla)],
    )

    prezzo_conv = ConversationHandler(
        entry_points=[CommandHandler("prezzo", cmd_prezzo_start)],
        states={
            WAITING_PRICE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, cmd_prezzo_receive)
            ],
        },
        fallbacks=[CommandHandler("annulla", cmd_annulla)],
    )

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("aiuto", cmd_aiuto))
    app.add_handler(CommandHandler("marche", cmd_marche))
    app.add_handler(CommandHandler("altri", cmd_piu))
    app.add_handler(CommandHandler("reset", cmd_reset))
    app.add_handler(add_brand_conv)
    app.add_handler(prezzo_conv)

    logger.info("Bot avviato — modalità manuale")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()

import os
import anthropic
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# ── Configuration ──────────────────────────────────────────
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

# ── Prompt système de l'agent IA Script Factory ───────────────
SYSTEM_PROMPT = """Tu es AI Agent Script, un agent spécialisé dans la création de scripts vidéo pour les réseaux sociaux.

Ton rôle : analyser la structure narrative d'un script ou d'une transcription vidéo virale, puis le réadapter à la niche suivante :
- Vente de produits digitaux (MRR / Master Resell Rights)
- Développement personnel appliqué à l'entrepreneuriat digital
- Personal branding pour créateurs de contenu

Quand tu reçois une transcription ou un texte, tu dois :
1. Identifier le HOOK (les 3-5 premières secondes qui accrochent)
2. Identifier le DÉVELOPPEMENT (la valeur/l'argumentation centrale)
3. Identifier le CTA (l'appel à l'action final)

Puis générer un script complet réadapté avec :
- HOOK : accroche puissante adaptée à la niche MRR/personal brand
- DÉVELOPPEMENT : contenu de valeur réadapté (2-4 points clés)
- CTA : appel à l'action clair (suivre, acheter, télécharger, commenter)

Format de réponse :
🎬 HOOK :
[ton hook réadapté]

📌 DÉVELOPPEMENT :
[tes points clés réadaptés]

📣 CTA :
[ton appel à l'action]

---
💡 NOTE STRATÉGIQUE : [une observation sur pourquoi ce format fonctionne dans ta niche]

Réponds toujours en français, peu importe la langue du texte d'entrée."""

# ── Mémoire des conversations ───────────────────────────────
conversation_history = {}

# ── Client Anthropic ────────────────────────────────────────
client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

# ── Commande /start ─────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Salut ! Je suis Script Factory.\n\n"
        "Envoie-moi une transcription ou un texte de vidéo virale et je te génère un script réadapté à ta niche MRR / personal brand.\n\n"
        "Tu peux aussi me donner des instructions spécifiques sur le ton ou le format que tu veux."
    )

# ── Commande /reset ─────────────────────────────────────────
async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    conversation_history[user_id] = []
    await update.message.reply_text("🔄 Conversation remise à zéro.")

# ── Traitement des messages ─────────────────────────────────
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user_message = update.message.text

    if user_id not in conversation_history:
        conversation_history[user_id] = []

    conversation_history[user_id].append({
        "role": "user",
        "content": user_message
    })

    await update.message.reply_text("⏳ Je génère ton script...")

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            system=SYSTEM_PROMPT,
            messages=conversation_history[user_id]
        )

        assistant_message = response.content[0].text

        conversation_history[user_id].append({
            "role": "assistant",
            "content": assistant_message
        })

        # Découpe si le message est trop long pour Telegram (limite 4096 chars)
        if len(assistant_message) > 4096:
            for i in range(0, len(assistant_message), 4096):
                await update.message.reply_text(assistant_message[i:i+4096])
        else:
            await update.message.reply_text(assistant_message)

    except Exception as e:
        await update.message.reply_text(f"❌ Erreur : {str(e)}")

# ── Lancement du bot ────────────────────────────────────────
if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("✅ Script Factory bot démarré...")
    app.run_polling()
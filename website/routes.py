from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session, current_app, abort
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask_login import login_user, logout_user, login_required, current_user
from .database import db
from .forms import RegisterForm
from .models import User
from .models import Review
import requests
import os
from dotenv import load_dotenv

load_dotenv()

routes = Blueprint('routes', __name__)

# HOME
@routes.route('/')
def index():
    user_logged_in = current_user.is_authenticated
    return render_template('index.html', user_logged_in=user_logged_in)

# ABOUT
@routes.route('/about')
def about():
    return render_template('about.html')


# ADMIN ROUTES
@routes.route("/admin/reviews")
@login_required
def manage_reviews():
    if not current_user.is_admin:
        flash("Alleen admins hebben toegang tot deze pagina", "danger")
        return redirect(url_for("routes.dashboard"))
    
    reviews = Review.query.order_by(Review.date_posted.desc()).all()
    return render_template("admin/manage_reviews.html", reviews=reviews)

@routes.route("/admin/review/delete/<int:review_id>", methods=["POST"])
@login_required
def delete_review_admin(review_id):
    if not current_user.is_admin:
        abort(403)
    
    review = Review.query.get_or_404(review_id)
    db.session.delete(review)
    db.session.commit()
    flash("Review succesvol verwijderd", "success")
    return redirect(url_for("routes.manage_reviews"))

@routes.route("/admin/review/edit/<int:review_id>", methods=["GET", "POST"])
@login_required
def edit_review_admin(review_id):
    if not current_user.is_admin:
        abort(403)
    
    review = Review.query.get_or_404(review_id)
    
    if request.method == "POST":
        review.content = request.form.get("content")
        review.rating = int(request.form.get("rating", 0))
        db.session.commit()
        flash("Review succesvol bijgewerkt", "success")
        return redirect(url_for("routes.manage_reviews"))
    
    return render_template("admin/edit_review.html", review=review)


# LOGIN
@routes.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            login_user(user)
            flash("Succesvol ingelogd!", "success")
            return redirect(url_for("routes.dashboard"))
        else:
            flash("Ongeldige inloggegevens", "danger")

    return render_template("login.html")

# REGISTER
@routes.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user:
            flash('Email al geregistreerd.', 'danger')
            return redirect(url_for('routes.register'))

        new_user = User(
            username=form.username.data,
            email=form.email.data,
        )
        new_user.set_password(form.password.data)
        db.session.add(new_user)
        db.session.commit()

        login_user(new_user)

        flash('Account aangemaakt!', 'success')
        return redirect(url_for('routes.dashboard'))

    return render_template("register.html", form=form)

# DASHBOARD
@routes.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html", email=current_user.email)

# LOGOUT
@routes.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Je bent uitgelogd.", "info")
    return redirect(url_for("routes.login"))

# TERMS
@routes.route('/terms')
def terms():
    return render_template('terms.html')

# PROFIEL
@routes.route('/profile')
@login_required
def profile():
    return render_template('profile.html', user=current_user)

# SETTINGS
@routes.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'POST':
        flash('Instellingen zijn bijgewerkt.', 'success')
        return redirect(url_for('routes.settings'))
    return render_template('settings.html')

@routes.route('/delete_account', methods=['POST'])
@login_required
def delete_account():
    user = current_user

    db.session.delete(user)
    db.session.commit()


    logout_user()

    flash('Je account is succesvol verwijderd.', 'success')
    return redirect(url_for('routes.index')) 

# STEAM API
all_reviews = {}

@routes.route("/games")
def games():
    query = request.args.get("query", "").lower()
    games = [
        {"id": "1174180", "name": "Red Dead Redemption 2", "image": "https://cdn.cloudflare.steamstatic.com/steam/apps/1174180/header.jpg"},
        {"id": "990080", "name": "Hogwarts Legacy", "image": "https://cdn.cloudflare.steamstatic.com/steam/apps/990080/header.jpg"},
        {"id": "1086940", "name": "Baldur's Gate 3", "image": "https://cdn.cloudflare.steamstatic.com/steam/apps/1086940/header.jpg"},
        {"id": "377160", "name": "Fallout 4", "image": "https://cdn.cloudflare.steamstatic.com/steam/apps/377160/header.jpg"},
        {"id": "582010", "name": "Monster Hunter: World", "image": "https://cdn.cloudflare.steamstatic.com/steam/apps/582010/header.jpg"},
        {"id": "1091500", "name": "Cyberpunk 2077", "image": "https://cdn.cloudflare.steamstatic.com/steam/apps/1091500/header.jpg"},
        {"id": "1716740", "name": "Starfield", "image": "https://cdn.cloudflare.steamstatic.com/steam/apps/1716740/header.jpg"},
        {"id": "72850", "name": "The Elder Scrolls V: Skyrim", "image": "https://cdn.cloudflare.steamstatic.com/steam/apps/72850/header.jpg"},
        {"id": "413150", "name": "Stardew Valley", "image": "https://cdn.cloudflare.steamstatic.com/steam/apps/413150/header.jpg"},
        {"id": "1245620", "name": "Elden Ring", "image": "https://cdn.cloudflare.steamstatic.com/steam/apps/1245620/header.jpg"},
        {"id": "49520", "name": "Borderlands 2", "image": "https://cdn.cloudflare.steamstatic.com/steam/apps/49520/header.jpg"},
        {"id": "1332010", "name": "Stray", "image": "https://cdn.cloudflare.steamstatic.com/steam/apps/1332010/header.jpg"},
        {"id": "292030", "name": "The Witcher 3: Wild Hunt", "image": "https://cdn.cloudflare.steamstatic.com/steam/apps/292030/header.jpg"},
        {"id": "782330", "name": "DOOM Eternal", "image": "https://cdn.cloudflare.steamstatic.com/steam/apps/782330/header.jpg"},
        {"id": "412020", "name": "Metro Exodus", "image": "https://cdn.cloudflare.steamstatic.com/steam/apps/412020/header.jpg"},
        {"id": "870780", "name": "Control", "image": "https://cdn.cloudflare.steamstatic.com/steam/apps/870780/header.jpg"},
        {"id": "435150", "name": "Divinity: Original Sin 2", "image": "https://cdn.cloudflare.steamstatic.com/steam/apps/435150/header.jpg"},
        {"id": "504230", "name": "Celeste", "image": "https://cdn.cloudflare.steamstatic.com/steam/apps/504230/header.jpg"},
        {"id": "374320", "name": "Dark Souls III", "image": "https://cdn.cloudflare.steamstatic.com/steam/apps/374320/header.jpg"},
        {"id": "814380", "name": "Sekiro: Shadows Die Twice", "image": "https://cdn.cloudflare.steamstatic.com/steam/apps/814380/header.jpg"},
        {"id": "367520", "name": "Hollow Knight", "image": "https://cdn.cloudflare.steamstatic.com/steam/apps/367520/header.jpg"},
        {"id": "1057090", "name": "Ori and the Will of the Wisps", "image": "https://cdn.cloudflare.steamstatic.com/steam/apps/1057090/header.jpg"},
        {"id": "252950", "name": "Rocket League", "image": "https://cdn.cloudflare.steamstatic.com/steam/apps/252950/header.jpg"},
        {"id": "1190460", "name": "Death Stranding", "image": "https://cdn.cloudflare.steamstatic.com/steam/apps/1190460/header.jpg"},
    ]
    if query:
        games = [game for game in games if query in game["name"].lower()]

    return render_template("games.html", games=games)

@routes.route("/games/<game_id>/review", methods=["POST"])
@login_required
def add_review(game_id):
    review_text = request.form.get("review", "").strip()
    if not review_text:
        flash("Review mag niet leeg zijn.", "warning")
        return redirect(url_for("routes.game_detail", game_id=game_id))

    review = {"username": current_user.username, "review": review_text}
    if game_id not in all_reviews:
        all_reviews[game_id] = []
    all_reviews[game_id].append(review)
    flash("Review toegevoegd!", "success")
    return redirect(url_for("routes.game_detail", game_id=game_id))

@routes.route("/games/<game_id>/edit/<username>", methods=["GET", "POST"])
@login_required
def edit_review(game_id, username):
    if current_user.username != username and not current_user.is_admin:
        flash("Je mag alleen je eigen reviews bewerken.", "danger")
        return redirect(url_for("routes.game_detail", game_id=game_id))

    game_reviews = all_reviews.get(game_id, [])
    for review in game_reviews:
        if review["username"] == username:
            if request.method == "POST":
                review["review"] = request.form["review"]
                flash("Review bijgewerkt!", "success")
                return redirect(url_for("routes.game_detail", game_id=game_id))
            
            return render_template("edit_review.html", game_id=game_id, review_text=review["review"])
    flash("Review niet gevonden.", "warning")
    return redirect(url_for("routes.game_detail", game_id=game_id))

@routes.route("/games/<game_id>/delete/<username>", methods=["POST"])
@login_required
def delete_review(game_id, username):
    if current_user.username != username  and not current_user.is_admin:
        flash("Je mag alleen je eigen reviews verwijderen.", "danger")
        return redirect(url_for("routes.game_detail", game_id=game_id))

    game_reviews = all_reviews.get(game_id, [])
    all_reviews[game_id] = [r for r in game_reviews if r["username"] != username]
    flash("Review verwijderd!", "success")
    return redirect(url_for("routes.game_detail", game_id=game_id))

@routes.route("/games/<game_id>")
def game_detail(game_id):

    steam_game = {
        "1174180": "Red Dead Redemption 2",
        "990080": "Hogwarts Legacy",
        "1086940": "Baldur's Gate 3",
        "377160": "Fallout 4",
        "582010": "Monster Hunter: World",
        "1091500": "Cyberpunk 2077",
        "1716740": "Starfield",
        "72850": "The Elder Scrolls V: Skyrim",
        "413150": "Stardew Valley",
        "49520": "Borderlands 2",
        "1332010": "Stray",
        "292030": "The Witcher 3: Wild Hunt",
        "782330": "DOOM Eternal",
        "412020": "Metro Exodus",
        "870780": "Control",
        "435150": "Divinity: Original Sin 2",
        "504230": "Celeste",
        "374320": "Dark Souls III",
        "814380": "Sekiro: Shadows Die Twice",
        "367520": "Hollow Knight",
        "1057090": "Ori and the Will of the Wisps",
        "252950": "Rocket League",
        "1190460": "Death Stranding"
    }

    game_name = steam_game.get(game_id, "Onbekende game")
    image_url = f"https://cdn.cloudflare.steamstatic.com/steam/apps/{game_id}/header.jpg"
    game_reviews = all_reviews.get(game_id, [])


    positive_pct = 0
    try:
        response = requests.get(f"https://store.steampowered.com/appreviews/{game_id}?json=1&num_per_page=100")
        if response.ok:
            data = response.json()
            total_reviews = data.get("query_summary", {}).get("total_reviews", 0)
            positive_reviews = data.get("query_summary", {}).get("total_positive", 0)
            if total_reviews > 0:
                positive_pct = int((positive_reviews / total_reviews) * 100)
    except Exception as e:
        print(f"Error fetching Steam review stats: {e}")

    if positive_pct >= 80:
        rating_color = "green"
    elif positive_pct >= 60:
        rating_color = "orange"
    else:
        rating_color = "red"


    steam_reviews = []
    try:
        response = requests.get(f"https://store.steampowered.com/appreviews/{game_id}?json=1&num_per_page=5")
        if response.ok:
            data = response.json()
            for review in data.get("reviews", []):
                steam_reviews.append({
                    "author": review["author"]["steamid"],
                    "review": review["review"],
                    "voted_up": review["voted_up"]
                })
    except Exception as e:
        print(f"Error fetching Steam reviews: {e}")

    has_reviewed = False
    if current_user.is_authenticated:
        has_reviewed = any(r["username"] == current_user.username for r in game_reviews)

    return render_template(
        "game_detail.html",
        game_id=game_id,
        game_name=game_name,
        image_url=image_url,
        reviews=game_reviews,
        steam_reviews=steam_reviews,
        positive_pct=positive_pct,
        rating_color=rating_color,
        has_reviewed=has_reviewed
    )



import logging
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
# from app import db
from app.models import User

logger = logging.getLogger("AuthRoutes")

auth = Blueprint("auth", __name__)


@auth.route("/login", methods=["GET", "POST"])
def login():
    """Handle user login."""
    if current_user.is_authenticated:
        return redirect(url_for("verifier.home"))

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        # Find user
        user = User.query.filter_by(username=username).first()

        # Validate password
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            flash(f"Welcome back, {user.username}!", "success")

            # Redirect to next page if specified, else home
            next_page = request.args.get("next")
            return redirect(next_page or url_for("verifier.home"))
        else:
            flash("Invalid username or password.", "danger")

    return render_template("login.html")


@auth.route("/logout")
@login_required
def logout():
    """Handle user logout."""
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))

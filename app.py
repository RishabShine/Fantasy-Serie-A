import os

from flask import Flask, flash, redirect, render_template, request, session, jsonify
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

from extras import login_required, apology

# Configure application

app = Flask(__name__)

# setting up data base

db = 

# Registration, logging in and logging out

@app.route("/login", methods=["GET", "POST"])
def login():
    
    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 400)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 400)

        elif request.form.get("password") != request.form.get("confirmation"):
            return apology("must provide confirmation", 400)

        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 0:
            return apology("username already taken", 400)

        password = generate_password_hash(request.form.get("password"))

        db.execute("INSERT INTO users (username, hash) VALUES (?, ?)", request.form.get("username"), password)

        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/quote")

    else:
        return render_template("register.html")

     
# functions

# points system

# home screen

@app.route("/", methods=["GET"])
def index():
    
    players = db.execute("SELECT players.name, players.position, player.value, team.crest, team.color FROM players JOIN teams ON teams.id = players.team_id WHERE player.id IN (SELECT player_id FROM ownership WHERE user_id = ? AND league_id = NULL", session["user_id"])

    return render_template("index")

# league home screen

# ! condition for leaving league (if league_id != NULL cannot join other league, method of removing data when leaving league)

@app.route("/league", methods=["GET"])
def league():
    
    cash = db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])[0]["cash"]
    players = db.execute("SELECT players.name, players.position, player.value, team.crest, team.color FROM players JOIN teams ON teams.id = players.team_id WHERE player.id IN (SELECT player_id FROM ownership WHERE user_id = ? AND league_id IN (SELECT id FROM league WHERE id IN (SELECT league_id FROM users WHERE id = ?))", session["user_id"], session["user_id"])

# create league

@app.route("/createleague", methods=["GET", "POST"])
def create_league():
    if request.method == "POST":
        return render_template("league.html")
    else:
        return render_template("createleague.html")


# drafting

# trading (sending offers, and accepting trades)

# sending offer 
# ! *** (how to set up league_id??)

@app.route("/offer", methods=["GET", "POST"])
def offer():
    if request.method == "POST":

        # ! add offer to offers table

        return redirect("/")

    else:
        
        # getting league id from user

        league_id = db.execute("SELECT league_id FROM users WHERE id = ?", session["user_id"])

        # checking what players the user is able to trade (not currently in an offer)

        available_players = db.execute("SELECT player_id, name FROM players WHERE player_id IN (SELECT player_id FROM ownership WHERE user_id = ? AND league_id = ? AND player_id NOT IN offers WHERE league_id IN (SELECT player_s FROM offers WHERE sender = ? AND league_id ))", session["user_id"], league_id, session["user_id"], league_id)
        
        # checking how much extra space the user has in their team

        total_players = db.execute("SELECT player_id FROM players WHERE player_id IN (SELECT player_id FROM ownership WHERE user_id = ? AND league_id = ?)", session["user_id"], league_id)

        space = 14 - (len(total_players))

        # displaying players who are owned in the league

        owned = db.execute("SELECT players.player_id, players.name, users.username FROM ownership JOIN users ON ownership.user_id = users.id WHERE users.league_id = ? AND users.id NOT IN (SELECT id FROM users WHERE id = ?)", league_id, session["user_id"])

        # displaying players that are not owned in the laegue

        free_agent = ("SELECT player_id, name FROM players WHERE player_id NOT IN (SELECT players.player_id, players.name, users.username FROM ownership JOIN users ON ownership.user_id = users.id WHERE users.league_id = ? AND users.id NOT IN (SELECT id FROM users WHERE id = ?)))", league_id, session["user_id"])

        # ! ensure that when making an offer there are not extra players, and a balance of positions (one trade at a time?)
        return render_template("offer.html", space=space, available_players=available_players, owned=owned, free_agent=free_agent)

# accepted trades

@app.route("/trade", methods=["GET", "POST"])
def trade():    
    if request.method == "POST":

        # gettting information about accepted offer
        # ! create a condition so that if a user accepts a trade for a player which someone else sent an offer for, the offer is removed (check should be run after any accepted trade)
        # ! how to connect based on league

        offer = db.execute("SELECT sender, receiver, player_s, player_r FROM offers WHERE reciever = ? OR sender = ")

        # sending players to new owners
        
        if not offer["player_s"] == "NULL":
            db.execute("INSERT INTO ownership (player_id, user_id, league_id) VALUES (?, ?, ?)", offer["player_s"], offer["receiver"], offer["league_id"])
        if not offer["player_r"] == "NULL":
            db.execute("INSERT INTO ownership (player_id, user_id, league_id) VALUES (?, ?, ?)", offer["player_r"], offer["sender"], offer["league_id"])

        # removing traded players from previous owners ownership and removing the offer

        db.execute("DELETE FROM ownership WHERE user_id = ? AND player_id = ? AND league_id = ?", offer["sender"], offer["player_s"], offer["league_id"])
        db.execute("DELETE FROM ownership WHERE user_id = ? AND player_id = ? AND league_id = ?", offer["receiver"], offer["player_r"], offer["league_id"])
        db.execute("DELETE FROM offers WHERE sender = ? AND receiver = ? AND player_s = ? AND player_r = ? AND league_id = ?", offer["sender"], offer["receiver"], offer["player_s"], offer["player_r"], offer["league_id"])

        return redirect("/league")

    else:
       
        # viewing trade offers

        offers_received = db.execute("SELECT * FROM offers WHERE receiver = ?", session["user_id"])
        offers_sent = db.execute("SELECT * FROM offers WHERE sender = ?", session["user_id"])

        return render_template("trades.html", offers_receiver=offers_received, offers_sent=offers_sent)
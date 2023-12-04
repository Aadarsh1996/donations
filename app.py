

from flask import Flask, render_template, request, session, redirect, url_for
from datetime import date, time, datetime
import sqlite3 as sql
import os
from twilio.rest import Client  # Twilio for SMS
import stripe  # Stripe for payment processing
import random


if not os.path.isfile('database.db'):
    conn = sql.connect('database.db')
    conn.execute(
        'CREATE TABLE IF NOT EXISTS Donors (Name TEXT NOT NULL, Amount INTEGER NOT NULL, Email TEXT NOT NULL, [timestamp] TIMESTAMP)')
    conn.execute(
        'CREATE TABLE IF NOT EXISTS Users (Name TEXT NOT NULL, Email TEXT NOT NULL, Password TEXT NOT NULL, Contact INTEGER NOT NULL)')
    conn.close()

app = Flask(__name__)


@app.route('/')
def root():
    session['logged_out'] = 1
    return render_template('index.html')


@app.route('/index.html')
def index():
    return render_template('index.html')


@app.route('/header_page.html')
def header_page():
    return render_template('header_page.html')


@app.route('/menu-bar-charity.html')
def menu_bar_charity():
    return render_template('menu-bar-charity.html')


@app.route('/footer.html')
def footer():
    return render_template('footer.html')


@app.route('/sidebar.html')
def sidebar():
    return render_template('sidebar.html')


@app.route('/contact.html')
def contact():
    return render_template('contact.html')


@app.route('/our-causes.html')
def our_causes():
    return render_template('our-causes.html')


@app.route('/about-us.html')
def about_us():
    return render_template('about-us.html')

TWILIO_ACCOUNT_SID = 'your_account_sid'
TWILIO_AUTH_TOKEN = 'your_auth_token'
TWILIO_PHONE_NUMBER = 'your_twilio_phone_number'

# Twilio client setup
client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)




def generate_otp():
    return str(random.randint(1000, 9999))

# Function to send OTP via Twilio SMS
def send_otp_via_sms(phone_number, otp):
    message = client.messages.create(
        body=f'Your OTP for donation system is: {otp}',
        from_=TWILIO_PHONE_NUMBER,
        to=phone_number
    )
    return message.sid


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nm = request.form['nm']
        contact = request.form['contact']
        email = request.form['email']
        password = request.form['password']

        with sql.connect("database.db") as con:
            cur = con.cursor()
            # check if User already present
            cur.execute("SELECT Email FROM Users WHERE Email=(?)", [(email)])
            data = cur.fetchall()
            if len(data) > 0:
                print('User already exists')
                user_exists = 1
            else:
                print("User not found, register new user")
                user_exists = 0
                cur.execute("INSERT INTO Users (Name,Email,Password,Contact) VALUES (?,?,?,?)",
                            (nm, email, password, contact))

    return render_template('login.html', user_exists=user_exists, invalid=None, logged_out=None)


@app.route('/login.html', methods=['GET', 'POST'])
def login():
    invalid = None
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        with sql.connect("database.db") as con:
            cur = con.cursor()
            # Validate user credentails from database
            cur.execute("SELECT Email FROM Users WHERE Email=(?) AND Password=(?)", [(email), (password)])
            data = cur.fetchall()
            if len(data) > 0:
                print('Login Success')
                # Fetch name of user
                cur.execute("SELECT Name FROM Users WHERE Email=(?) AND Password=(?)", [(email), (password)])
                nm = cur.fetchall()
                nm = nm[0][0]
                # Store User details in Session and log in user
                session['nm'] = nm
                session['email'] = email
                session['logged_out'] = None
                return redirect(url_for('donate'))
            else:
                print("Invalid Login")
                invalid = 1
    return render_template('login.html', user_exists=None, invalid=invalid, logged_out=None)


@app.route('/logout')
def logout():
    session.clear()
    session['logged_out'] = 1
    print('Session Cleared and Logged Out')
    return render_template('index.html')


@app.route('/donate')
def donate():
    # If Logged Out, Redirect to Log In page
    if session['logged_out']:
        return render_template('login.html', logged_out=1, user_exists=None, invalid=None)
    nm = session['nm']
    email = session['email']
    return render_template('donate.html', nm=nm, email=email)


# insert values into table
@app.route('/donation', methods=['POST', 'GET'])
def donation():
    # If Logged Out, Redirect to Log In page
    if session['logged_out']:
        return render_template('login.html', logged_out=1, user_exists=None, invalid=None)
    if request.method == 'POST':
        nm = session['nm']
        email = session['email']
        amt = request.form['amt']
        today = datetime.now()
        today = today.strftime("%d-%m-%Y" + "," + "%H:%M")

        with sql.connect("database.db") as con:
            cur = con.cursor()
            # check if already donated. If already donated, add donation. Else create new donation
            cur.execute("SELECT Email FROM Donors WHERE Email=(?)", [(email)])
            data = cur.fetchall()
            if len(data) > 0:
                cur.execute("UPDATE Donors SET Amount=Amount+(?) WHERE Email=(?)", [(amt), (email)])
            else:
                cur.execute("INSERT INTO Donors (Name,Amount,Email,timestamp) VALUES (?,?,?,?)",
                            (nm, amt, email, today))
            con.commit()

            # Greeting
            msg = "Thank You for Donating"
            for row in cur.execute("SELECT Amount FROM Donors WHERE Email=(?)", [(email)]):
                Amount = row
        return render_template("greeting.html", msg=msg, nm=nm, Amount=Amount, today=today, email=email)
        con.close()


# Display List of Donations
@app.route('/list1')
def list1():
    # If Logged Out, Redirect to Log In page
    if session['logged_out']:
        return render_template('login.html', logged_out=1, user_exists=None, invalid=None)
    con = sql.connect("database.db")
    con.row_factory = sql.Row

    cur = con.cursor()
    cur.execute("SELECT * FROM Donors")

    rows = cur.fetchall();
    return render_template("list1.html", rows=rows)


# Display Profile
@app.route('/profile')
def profile():
    # If Logged Out, Redirect to Log In page
    if session['logged_out']:
        return render_template('login.html', logged_out=1, user_exists=None, invalid=None)
    nm = session['nm']
    email = session['email']
    with sql.connect("database.db") as con:
        cur = con.cursor()
        # Fetch details of user
        cur.execute("SELECT Contact FROM Users WHERE Email=(?)", [(email)])
        contact = cur.fetchall()
        contact = contact[0][0]

        cur.execute("SELECT Password FROM Users WHERE Email=(?)", [(email)])
        password = cur.fetchall()
        password = password[0][0]
    return render_template("profile.html", nm=nm, email=email, contact=contact, password=password)




@app.route('/otp_verification', methods=['GET', 'POST'])
def otp_verification():
    if request.method == 'POST':
        user_otp = request.form['otp']
        email = session['email']

        with sql.connect("database.db") as con:
            cur = con.cursor()
            # Verify OTP
            cur.execute("SELECT OTP FROM Users WHERE Email=(?)", [(email)])
            stored_otp = cur.fetchone()[0]

            if user_otp == stored_otp:
                # OTP verification successful
                print('OTP verification successful')

                # Clear OTP from the database
                cur.execute("UPDATE Users SET OTP = NULL WHERE Email=(?)", [(email)])

                # Redirect to the donation page or any other desired page
                return redirect(url_for('donate'))
            else:
                # Incorrect OTP
                print('Incorrect OTP')
                return render_template('otp_verification.html', invalid=True)

    return render_template('otp_verification.html', invalid=None)


# Add a new route for payment
@app.route('/make_payment', methods=['POST'])
def make_payment():
    if request.method == 'POST':
        # Retrieve payment information from the form
        amount = request.form['amount']
        token = request.form['stripeToken']

        try:
            # Charge the customer using Stripe
            charge = stripe.Charge.create(
                amount=int(amount) * 100,  # Convert amount to cents
                currency='usd',
                description='Donation',
                source=token,
            )

            donor_name = session['nm']
            donor_email = session['email']
            donation_amount = int(amount)

            # Update the Donors table in the database
            with sql.connect("database.db") as con:
                cur = con.cursor()

                # Check if the donor already exists in the Donors table
                cur.execute("SELECT Email FROM Donors WHERE Email=(?)", [(donor_email)])
                data = cur.fetchall()

                if len(data) > 0:
                    # Donor exists, update the donation amount
                    cur.execute("UPDATE Donors SET Amount=Amount+(?) WHERE Email=(?)", [donation_amount, donor_email])
                else:
                    # Donor doesn't exist, insert a new donation record
                    cur.execute("INSERT INTO Donors (Name, Amount, Email, timestamp) VALUES (?, ?, ?, ?)",
                                (donor_name, donation_amount, donor_email, datetime.now().strftime("%d-%m-%Y, %H:%M")))

                con.commit()

            return render_template('payment_success.html', amount=amount)
        except stripe.error.CardError as e:
            # Payment failed, handle the error
            return render_template('payment_error.html', error_message=str(e))


if __name__ == '__main__':
    app.secret_key = ".."
    app.run()
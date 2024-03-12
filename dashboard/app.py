from flask import Flask, render_template, request, redirect, url_for, flash, abort
import sqlite3
import re
import secrets
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
from flask_basicauth import BasicAuth

app = Flask(__name__)
DATABASE = 'license_plates.db'
secret_key = secrets.token_hex(16) 
app.secret_key = secret_key
app.config['BASIC_AUTH_USERNAME'] = 'anpr'
app.config['BASIC_AUTH_PASSWORD'] = '1234'
basic_auth = BasicAuth(app)

# Create database table
def create_table():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS license_plates (id INTEGER PRIMARY KEY AUTOINCREMENT, plate_number TEXT, owner TEXT, plate_type TEXT DEFAULT 'permanent', timestamp TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS system_switch (id INTEGER PRIMARY KEY, system_power INTEGER)''')
    c.execute('SELECT system_power FROM system_switch WHERE id = 1')
    global power_switch
    row = c.fetchone()
    power_switch = bool(row[0]) if row else True #initial state of the relay
    conn.commit()
    conn.close()

create_table()

# Configure and start the scheduler for temporary license plates
scheduler = BackgroundScheduler()
scheduler.start()

# Define function to move expired temporary plate numbers to inactive list
def delete_expired_temporary_plates():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("UPDATE license_plates SET plate_type='inactive' WHERE plate_type='temporary' AND timestamp < ?", (datetime.now() - timedelta(minutes=1),))
    conn.commit()
    conn.close()

# Schedule the task to run every hour
scheduler.add_job(delete_expired_temporary_plates, 'interval', minutes=1)

@app.route('/')
@basic_auth.required
def index():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT * FROM license_plates")
    plates = c.fetchall()
    conn.close()
    return render_template('index.html', plates=plates, power_switch=power_switch)

@app.route('/add', methods=['POST'])
def add_plate():
    plate_number = request.form['plate_number']
    owner = request.form['owner']
    plate_type = request.form['plate_type']
    if not re.match(r'^[a-zA-Z0-9]{6,10}$', plate_number):
        flash("Please provide correct license plate number!")
        return redirect(url_for('index'))
    if plate_number:
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute("INSERT INTO license_plates (plate_number, owner, plate_type, timestamp) VALUES (?, ?, ?, ?)", (plate_number, owner, plate_type, datetime.now()))
        conn.commit()
        conn.close()
    flash("License plate added successfully.")
    return redirect(url_for('index'))

@app.route('/delete/<int:id>')
def delete_plate(id):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("DELETE FROM license_plates WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/system_mgmt', methods=['POST'])
def toggle_function():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    global power_switch
    power_switch = not power_switch
    c.execute('INSERT OR REPLACE INTO system_switch (id, system_power) VALUES (?, ?)', (1, int(power_switch)))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/move_to_temporary/<int:id>')
def move_to_temporary(id):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("UPDATE license_plates SET plate_type='temporary', timestamp=? WHERE id=?", (datetime.now(), id))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/move_to_permanent/<int:id>')
def move_to_permanent(id):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("UPDATE license_plates SET plate_type='permanent' WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/move_to_inactive/<int:id>')
def move_to_inactive(id):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("UPDATE license_plates SET plate_type='inactive' WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

#access errors
@app.errorhandler(401)
def unauthorized(e):
    return 'Unauthorized Access', 401

@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html'), 404

@app.errorhandler(500)
def special_exception_handler(error):
    return 'Database connection failed', 500

@app.route('/not_found')
def not_found():
    abort(404)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)  # Change the port if necessary

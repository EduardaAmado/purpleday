import mysql.connector
from datetime import datetime, timedelta
import requests
import smtplib
from email.message import EmailMessage
from flask import Flask, render_template, request, redirect, url_for
import os

app = Flask(__name__)

# ----------------- DB Connection -----------------
def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="smb_grafana"
    )

# ----------------- Utility Functions -----------------
def is_weekday(date):
    return date.weekday() < 5

# ----------------- Purple Day Generation -----------------
def generate_purple_days(start_date, weeks=2):
    conn = get_connection()
    cursor = conn.cursor()

    # Apaga registros anteriores
    cursor.execute("DELETE FROM purple_days")

    current_weekday = 2  # Começa na quarta-feira
    date_cursor = start_date
    count = 0

    while count < weeks:
        while not is_weekday(date_cursor):
            date_cursor += timedelta(days=1)

        pd_date = date_cursor + timedelta((current_weekday - date_cursor.weekday()) % 7)
        while not is_weekday(pd_date):
            pd_date -= timedelta(days=1)

        cursor.execute("""
            INSERT INTO purple_days (date, new_date, weekday, status)
            VALUES (%s, %s, %s, 'Confirmed')
        """, (pd_date, pd_date, pd_date.weekday()))

        date_cursor += timedelta(days=7)
        current_weekday = current_weekday - 1 if current_weekday > 0 else 4
        count += 1

    conn.commit()
    cursor.close()
    conn.close()

# ----------------- Fetch Holidays for Portugal -----------------
def fetch_portugal_holidays():
    conn = get_connection()
    cursor = conn.cursor()

    # Garante que a tabela tenha a estrutura correta com a PRIMARY KEY em `date`
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS holidays (
            date DATE PRIMARY KEY,
            name VARCHAR(255)
        )
    """)

    year = datetime.now().year
    url = f"https://date.nager.at/api/v3/PublicHolidays/{year}/PT"

    response = requests.get(url)
    holidays = response.json()

    for h in holidays:
        cursor.execute("""
            INSERT INTO holidays (date, name) VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE name=VALUES(name)
        """, (h["date"], h["localName"]))

    # Porto-specific holiday
    porto_specific = [
        {"date": f"{year}-06-24", "name": "Festa de S\u00e3o Jo\u00e3o do Porto"}
    ]
    for h in porto_specific:
        cursor.execute("""
            INSERT INTO holidays (date, name) VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE name=VALUES(name)
        """, (h["date"], h["name"]))

    conn.commit()
    cursor.close()
    conn.close()

# ----------------- Email Notification -----------------
def get_adjustment_options(weekday):
    if weekday == 0:
        return ["Move to Tuesday"]
    elif weekday == 4:
        return ["Move to Thursday"]
    else:
        return ["Move to previous day", "Move to next day"]

def send_email_notice(purple_day, tipo="semana"):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT email, name FROM users")
    users = cursor.fetchall()

    pd_date = purple_day['date']
    weekday = purple_day['weekday']
    options = get_adjustment_options(weekday)
    options_text = "\n".join(f"- {opt}" for opt in options)

    if tipo == "semana":
        subject = f"[Aviso] Purple Day {pd_date} é feriado"
        content = f"""Olá,

O Purple Day marcado para {pd_date} coincide com um feriado.

Recomenda-se remarcar para uma das opções abaixo:
{options_text}

Se não for remarcado até o dia anterior, será automaticamente cancelado.

Atenciosamente,
Sistema Purple Day"""

    elif tipo == "véspera":
        subject = f"[Lembrete] Purple Day {pd_date} ainda não foi remarcado"
        content = f"""Olá,

O Purple Day {pd_date} é um feriado e ainda não foi remarcado.

Lembre-se: se não for alterado hoje, será cancelado automaticamente amanhã.

Atenciosamente,
Sistema Purple Day"""

    elif tipo == "cancelamento":
        subject = f"[Cancelado] Purple Day {pd_date} foi cancelado"
        content = f"""Olá,

O Purple Day {pd_date} não foi remarcado e coincide com um feriado.

Ele foi automaticamente cancelado.

Atenciosamente,
Sistema Purple Day"""

    else:
        return  # Tipo inválido

    for user in users:
        msg = EmailMessage()
        msg.set_content(content)
        msg['Subject'] = subject
        msg['From'] = "no-reply@purpleday.com"
        msg['To'] = user['email']

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as s:
             #resto aqui
            s.send_message(msg)

    cursor.close()
    conn.close()

# ----------------- Conflict Checking -----------------
def check_purple_collisions():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    today = datetime.now().date()
    in_seven_days = today + timedelta(days=7)
    tomorrow = today + timedelta(days=1)

    # Carrega todos os Purple Days confirmados
    cursor.execute("SELECT * FROM purple_days WHERE status = 'Confirmed'")
    purple_days = cursor.fetchall()

    # Carrega feriados
    cursor.execute("SELECT date FROM holidays")
    holidays = {row['date'] for row in cursor.fetchall()}

    for pd in purple_days:
        pd_date = pd['date']
        last_email = pd.get('last_email_sent')

        # 1. Uma semana antes
        if pd_date == in_seven_days and pd_date in holidays and last_email != today:
            send_email_notice(pd, tipo="semana")
            cursor.execute("UPDATE purple_days SET last_email_sent = %s WHERE id = %s", (today, pd['id']))

        # 2. Um dia antes
        elif pd_date == tomorrow and pd_date in holidays and pd['status'] == 'Confirmed' and last_email != today:
            send_email_notice(pd, tipo="véspera")
            cursor.execute("UPDATE purple_days SET last_email_sent = %s WHERE id = %s", (today, pd['id']))

        # 3. No dia: cancelamento automático
        elif pd_date == today and pd_date in holidays and pd['status'] == 'Confirmed':
            send_email_notice(pd, tipo="cancelamento")
            cursor.execute("UPDATE purple_days SET status = 'Canceled', last_email_sent = %s WHERE id = %s", (today, pd['id']))

    conn.commit()
    cursor.close()
    conn.close()


def auto_cancel_missed_changes():
    conn = get_connection()
    cursor = conn.cursor()
    today = datetime.now().date()

    cursor.execute("""
        UPDATE purple_days
        SET status = 'Canceled' 
        WHERE new_date = %s AND new_date IN (SELECT date FROM holidays)
    """, (today,))

    conn.commit()
    cursor.close()
    conn.close()

# ----------------- Scheduled Task -----------------
def daily_tasks():
    fetch_portugal_holidays()
    check_purple_collisions()
    auto_cancel_missed_changes()

# ----------------- Flask Routes -----------------
@app.route("/")
def index():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM purple_days ORDER BY date")
    purple_days = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template("purple_days.html", purple_days=purple_days)

@app.route("/reschedule/<int:id>", methods=["POST"])
def reschedule(id):
    new_date = request.form.get("new_date")
    new_date_obj = datetime.strptime(new_date, "%Y-%m-%d").date()

    if new_date_obj.weekday() >= 5:
        return "New date must be a weekday!", 400

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE purple_days
        SET new_date = %s, status = 'Changed' 
        WHERE id = %s
    """, (new_date_obj, id))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for("index"))

# ----------------- Main Entry -----------------
if __name__ == "__main__":
    if not os.path.exists("templates"):
        os.makedirs("templates")
    if not os.path.exists("static"):
        os.makedirs("static")

    with open("templates/purple_days.html", "w") as f:
        f.write("""<!DOCTYPE html>
<html lang='en'>
<head>
    <meta charset='UTF-8'>
    <title>Purple Days</title>
    <link rel='stylesheet' href='/static/styles.css'>
</head>
<body>
<h1>Purple Days Schedule</h1>
<table>
<thead>
<tr>
    <th>Original Date</th>
    <th>New Date</th>
    <th>Status</th>
    <th>Action</th>
</tr>
</thead>
<tbody>
{% for pd in purple_days %}
<tr>
    <td>{{ pd.date }}</td>
    <td>{{ pd.new_date }}</td>
    <td>{{ pd.status }}</td>
    <td>
        {% if pd.status != 'Canceled' %}
        <form action='/reschedule/{{ pd.id }}' method='post'>
            <input type='date' name='new_date' required>
            <button type='submit'>Change</button>
        </form>
        {% endif %}
    </td>
</tr>
{% endfor %}
</tbody>
</table>
</body>
</html>""")

    with open("static/styles.css", "w") as f:
        f.write("""body { font-family: Arial, sans-serif; padding: 2em; }
table { border-collapse: collapse; width: 100%; }
th, td { border: 1px solid #999; padding: 8px; text-align: center; }
form { display: flex; gap: 0.5em; }""")

    generate_purple_days(datetime.now().date())
    daily_tasks()
    app.run(debug=True)

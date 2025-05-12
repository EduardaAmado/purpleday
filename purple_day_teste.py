import mysql.connector
from datetime import datetime, timedelta
import smtplib
from email.message import EmailMessage

# ----------------- DB Connections -----------------
def get_connection(database="smb_grafana"):
    return mysql.connector.connect(
        host = "localhost",
        user = "root",
        password = "",
        database=database
    )

# ----------------- Purple Day Generator -----------------
def is_weekday(date):
    return date.weekday() < 5

def generate_purple_days(start_date, weeks=2):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM purple_days")

    current_weekday = 26  # Wednesday
    date_cursor = start_date
    count = 0

    while count < weeks:
        while not is_weekday(date_cursor):
            date_cursor += timedelta(days=1)

        pd_date = date_cursor + timedelta((current_weekday - date_cursor.weekday()) % 7)
        while not is_weekday(pd_date):
            pd_date -= timedelta(days=1)

        cursor.execute("INSERT INTO purple_days (date) VALUES (%s)", (pd_date,))

        date_cursor += timedelta(days=7)
        current_weekday = current_weekday - 1 if current_weekday > 0 else 4
        count += 1

    conn.commit()
    cursor.close()
    conn.close()

# ----------------- Email Utilities -----------------
def get_email_sender():
    conn = get_connection(database="holidays")
    cursor = conn.cursor()
    cursor.execute("SELECT sender FROM email_sender")
    sender = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    return sender

def get_email_receivers():
    conn = get_connection(database="holidays")
    cursor = conn.cursor()

    cursor.execute("SELECT receivers FROM email_receivers_to")
    to_receivers = [row[0] for row in cursor.fetchall()]

    cursor.execute("SELECT receivers FROM email_receivers_cc")
    cc_receivers = [row[0] for row in cursor.fetchall()]

    cursor.close()
    conn.close()
    return to_receivers, cc_receivers

def get_holidays():
    conn = get_connection(database="holidays")
    cursor = conn.cursor()
    cursor.execute("SELECT date_porto FROM holidays_date_porto")
    holidays = {row[0] for row in cursor.fetchall()}
    cursor.close()
    conn.close()
    return holidays

def send_email_notice(date):
    sender = get_email_sender()
    to_receivers, cc_receivers = get_email_receivers()

    subject = f"[Aviso] Purple Day {date} é feriado"
    content = f"""Olá,

O Purple Day marcado para {date} coincide com um feriado.

Recomenda-se remarcar com antecedência.

Atenciosamente,
Sistema Purple Day"""

    msg = EmailMessage()
    msg.set_content(content)
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = "teste@example.com"
    msg['Cc'] = "teste@example.com"

    all_recipients = to_receivers + cc_receivers

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as s:
        # s.login("user", "pass")  # descomente e configure se necessário
        s.send_message(msg, from_addr=sender, to_addrs=all_recipients)

# ----------------- Check and Notify -----------------
def check_purple_conflicts():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    today = datetime.now().date()
    holidays = get_holidays()

    cursor.execute("SELECT id, date FROM purple_days")
    purple_days = cursor.fetchall()

    for pd in purple_days:
        days_until = (pd["date"] - today).days
        if 7 <= days_until <= 14 and pd["date"] in holidays:
            send_email_notice(pd["date"])

    cursor.close()
    conn.close()

# ----------------- Entry Point -----------------
if __name__ == "__main__":
    generate_purple_days(datetime.now().date())
    check_purple_conflicts()

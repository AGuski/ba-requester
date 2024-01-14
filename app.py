import threading
import requests
import smtplib
import schedule
import time
import os
import http.server
import socketserver
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()  # Load .env file variables into the environment

# URL and string to check
url_to_check = os.environ.get('URL_TO_CHECK')
string_to_find = os.environ.get('TARGET_STRING')

# Email details - replace with your details
sender_email = os.environ.get('EMAIL_SENDER')
receiver_email = os.environ.get('EMAIL_RECEIVER')
password = os.environ.get('EMAIL_PW')

user_agent = f"PrivateTerminCheck/1.0 ({sender_email})"

# Function to send email
def send_email():
    message = MIMEMultipart()
    message["Subject"] = "Bürgeramt Termine frei!"
    message["From"] = sender_email
    message["To"] = receiver_email

    # Email body
    body = "Termine checken: " + url_to_check
    message.attach(MIMEText(body, "plain"))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, message.as_string())
        server.quit()
        print("Email sent successfully")
    except Exception as e:
        print(f"Error sending email: {e}")

# Function to check for the string in the HTTP response
def check_for_string():
    print("Checking...")
    try:
        headers = {'User-Agent': user_agent}
        response = requests.get(url_to_check, headers=headers)
        if string_to_find not in response.text:
            send_email()
    except Exception as e:
        print(f"Error during HTTP request: {e}")

# Schedule to run every 2 minutes
schedule.every(10).seconds.do(check_for_string)

# Initial check
check_for_string()

class HealthCheckHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'OK')
        else:
            self.send_response(404)
            self.end_headers()

# Start a simple server
PORT = int(os.environ.get('PORT'))
Handler = HealthCheckHandler

def start_server():
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print("serving at port", PORT)
        httpd.serve_forever()

# Run the server in a separate thread
server_thread = threading.Thread(target=start_server)
server_thread.start()

# Keep running
while True:
    schedule.run_pending()
    time.sleep(1)

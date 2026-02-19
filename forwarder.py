import imaplib
import smtplib
import email
import os
import sys
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

def load_env(filepath=os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")):
    with open(filepath) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                os.environ.setdefault(key.strip(), value.strip())

load_env()


IMAP_HOST = "imap.education.gouv.fr"
IMAP_PORT = 993
IMAP_USER = os.getenv("IMAP_USER")
IMAP_PASS = os.getenv("IMAP_PASS")           # mot de passe application

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
GMAIL_USER = os.getenv("GMAIL_USER")         # toi@gmail.com
GMAIL_PASS = os.getenv("GMAIL_PASS")         # mot de passe app Gmail
GMAIL_TO   = os.getenv("GMAIL_USER")         # même adresse cible

def forward_unseen_mails():
    # Connexion IMAP
    imap = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT)
    imap.login(IMAP_USER, IMAP_PASS)
    imap.select("INBOX")

    status, messages = imap.search(None, "NOT KEYWORD FORWARDED")
    if status != "OK" or not messages[0]:
        print("Aucun mail à transférer.")
        imap.logout()
        return

    mail_ids = messages[0].split()
    print(f"{len(mail_ids)} mail(s) à transférer.")

    smtp = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
    smtp.ehlo()
    smtp.starttls()
    smtp.login(GMAIL_USER, GMAIL_PASS)

    for mail_id in mail_ids:
        _, msg_data = imap.fetch(mail_id, "(RFC822)")
        raw_email = msg_data[0][1]
        original = email.message_from_bytes(raw_email)

        # Sujet avec tag [MAILPRO] (sans doublon)
        subject = original.get("Subject", "(sans objet)")
        if not subject.startswith("[MAILPRO]"):
            subject = "[MAILPRO] " + subject

        # Expéditeur original
        sender = original.get("From", "inconnu")

        # Construire le mail à transférer
        fwd = MIMEMultipart()
        fwd["From"]              = GMAIL_USER
        fwd["To"]                = GMAIL_TO
        fwd["Subject"]           = subject
        fwd["Reply-To"]          = sender
        fwd["X-Forwarded-From"]  = sender

        # Corps du mail
        if original.is_multipart():
            for part in original.walk():
                ctype = part.get_content_type()
                if ctype == "text/plain" and not part.get_filename():
                    body = part.get_payload(decode=True).decode("utf-8", errors="replace")
                    fwd.attach(MIMEText(body, "plain"))
                elif ctype == "text/html" and not part.get_filename():
                    html = part.get_payload(decode=True).decode("utf-8", errors="replace")
                    fwd.attach(MIMEText(html, "html"))
                elif part.get_filename():
                    attachment = MIMEBase(*ctype.split("/"))
                    attachment.set_payload(part.get_payload(decode=True))
                    encoders.encode_base64(attachment)
                    attachment.add_header(
                        "Content-Disposition",
                        "attachment",
                        filename=part.get_filename()
                    )
                    fwd.attach(attachment)
        else:
            body = original.get_payload(decode=True).decode("utf-8", errors="replace")
            fwd.attach(MIMEText(body, "plain"))

        smtp.sendmail(GMAIL_USER, GMAIL_TO, fwd.as_string())
        imap.store(mail_id, "+FLAGS", "FORWARDED")
        print(f"Transféré : {subject} | De : {sender}")

    smtp.quit()
    imap.logout()

def init_flags():
    """Marque tous les mails existants comme FORWARDED sans les transférer."""
    imap = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT)
    imap.login(IMAP_USER, IMAP_PASS)
    imap.select("INBOX")

    status, messages = imap.search(None, "NOT KEYWORD FORWARDED")
    if status != "OK" or not messages[0]:
        print("Tous les mails sont déjà marqués FORWARDED.")
        imap.logout()
        return

    mail_ids = messages[0].split()
    print(f"Marquage de {len(mail_ids)} mail(s) comme FORWARDED...")
    for mail_id in mail_ids:
        imap.store(mail_id, "+FLAGS", "FORWARDED")
    print("Terminé.")
    imap.logout()

if __name__ == "__main__":
    if "--init" in sys.argv:
        init_flags()
    else:
        forward_unseen_mails()
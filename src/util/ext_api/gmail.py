import base64
import contextlib
import imaplib
import json
import operator
import smtplib
import urllib.parse
import urllib.request
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import lxml.html  # nosec B410

GOOGLE_ACCOUNTS_BASE_URL = "https://accounts.google.com"
REDIRECT_URI = "urn:ietf:wg:oauth:2.0:oob"


def command_to_url(command: str) -> str:
    return f"{GOOGLE_ACCOUNTS_BASE_URL}/{command}"


def url_escape(text: str) -> str:
    return urllib.parse.quote(text, safe="~-._")


def url_unescape(text: str) -> str:
    return urllib.parse.unquote(text)


def url_format_params(params: dict[str, str]) -> str:
    return "&".join(
        f"{param[0]}={url_escape(param[1])}" for param in sorted(params.items(), key=operator.itemgetter(0))
    )


def generate_permission_url(client_id: str, scope: str = "https://mail.google.com/") -> str:
    params = {
        "client_id": client_id,
        "redirect_uri": REDIRECT_URI,
        "scope": scope,
        "response_type": "code",
    }
    return f'{command_to_url("o/oauth2/auth")}?{url_format_params(params)}'


def call_authorize_tokens(client_id: str, client_secret: str, authorization_code: str) -> dict[str, str]:
    params = {
        "client_id": client_id,
        "client_secret": client_secret,
        "code": authorization_code,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code",
    }
    response = (
        urllib.request.urlopen(  # nosec: B310
            command_to_url("o/oauth2/token"),
            urllib.parse.urlencode(params).encode("UTF-8"),
        )
        .read()
        .decode("UTF-8")
    )
    return json.loads(response)


def call_refresh_token(client_id: str, client_secret: str, refresh_token: str) -> dict[str, str]:
    params = {
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token",
    }
    response = (
        urllib.request.urlopen(  # nosec: B310
            command_to_url("o/oauth2/token"),
            urllib.parse.urlencode(params).encode("UTF-8"),
        )
        .read()
        .decode("UTF-8")
    )
    return json.loads(response)


def generate_oauth2_string(username: str, access_token: str, as_base64: bool = False) -> str:
    auth_string = f"user={username}\1auth=Bearer {access_token}\1\1"
    if as_base64:
        auth_string = base64.b64encode(auth_string.encode("ascii")).decode("ascii")
    return auth_string


def test_imap(user: str, auth_string: str) -> None:
    imap_conn = imaplib.IMAP4_SSL("imap.gmail.com")
    imap_conn.debug = 4
    imap_conn.authenticate("XOAUTH2", lambda x: auth_string.encode("ascii"))
    imap_conn.select("INBOX")


def test_smpt(user: str, base64_auth_string: str) -> None:
    smtp_conn = smtplib.SMTP("smtp.gmail.com", 587)
    smtp_conn.set_debuglevel(True)
    smtp_conn.ehlo("test")
    smtp_conn.starttls()
    smtp_conn.docmd("AUTH", "XOAUTH2 " + base64_auth_string)


def get_authorization(google_client_id: str, google_client_secret: str) -> tuple[str, str, str]:
    scope = "https://mail.google.com/"
    print("Navigate to the following URL to auth:", generate_permission_url(google_client_id, scope))
    authorization_code = input("Enter verification code: ")
    response = call_authorize_tokens(google_client_id, google_client_secret, authorization_code)
    return response["refresh_token"], response["access_token"], response["expires_in"]


def refresh_authorization(google_client_id: str, google_client_secret: str, refresh_token: str) -> tuple[str, str]:
    response = call_refresh_token(google_client_id, google_client_secret, refresh_token)
    return response["access_token"], response["expires_in"]


def send_mail(
    google_client_id: str,
    google_client_secret: str,
    google_refresh_token: str,
    fromaddr: str,
    toaddr: str,
    subject: str,
    message: str,
    show_debug: bool = False,
) -> bool:
    access_token, expires_in = refresh_authorization(google_client_id, google_client_secret, google_refresh_token)
    auth_string = generate_oauth2_string(fromaddr, access_token, as_base64=True)

    with contextlib.suppress(Exception):
        msg = MIMEMultipart("related")
        msg["Subject"] = subject
        msg["From"] = fromaddr
        msg["To"] = toaddr
        msg.preamble = "This is a multi-part message in MIME format."
        msg_alternative = MIMEMultipart("alternative")
        msg.attach(msg_alternative)

        part_text = MIMEText(
            lxml.html.fromstring(message).text_content().encode("utf-8"), "plain", _charset="utf-8"  # nosec B410
        )
        part_html = MIMEText(message, "html", _charset="utf-8")

        msg_alternative.attach(part_text)
        msg_alternative.attach(part_html)

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.set_debuglevel(show_debug)
        server.ehlo(google_client_id)
        server.starttls()
        server.docmd("AUTH", "XOAUTH2 " + auth_string)
        server.sendmail(fromaddr, toaddr, msg.as_string())
        server.quit()

        return True
    return False


if __name__ == "__main__":
    GOOGLE_CLIENT_ID = "SET THIS!"  # nosec: B105
    GOOGLE_CLIENT_SECRET = "SET THIS!"  # nosec: B105
    refresh_token, access_token, expires_in = get_authorization(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET)
    print("Set the following as your GOOGLE_REFRESH_TOKEN:", refresh_token)
    exit()

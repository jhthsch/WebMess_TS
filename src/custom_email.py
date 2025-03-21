import smtplib
import ssl
from datetime import datetime
from os.path import basename
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import platform  # Importing the platform module
import logging


def send_email(To_list, t, filename=None, channel=None, report_str=""):
    """sends a trigger warning"""
    port = 465
    password = "fxdp krlr rmmn hazx"  # "ayvmlicgwffwnqji"  # pi4ts2pi4ts2"
    context = ssl.create_default_context()
    msg = MIMEMultipart()  # EmailMessage()
    msg["From"] = "webapp.mcc128@gmail.com"
    msg["Subject"] = "Trigger alert Web app"
    msg["To"] = ",".join(To_list)  # To_list

    computer_name = platform.node()

    body = f"""
    Messpunkt: {computer_name}
    Messwertueberschreitung an Kanal: {channel}
    Uhrzeit: {t} \n
    Messwerte:
    {report_str}
    """

    # body = f"""
    # the measurement exceeded its value on channel {channel} the localtime is {t} \n
    # {report_str}
    # """
    plain_text = MIMEText(body, _subtype="plain", _charset="UTF-8")
    msg.attach(plain_text)

    if filename is not None:
        try:
            with open(filename, "rb") as fil:
                part = MIMEApplication(fil.read(), Name=basename(filename))
            part["Content-Disposition"] = 'attachment; filename="%s"' % basename(filename)
            msg.attach(part)
        except Exception as e:
            logging.warning(f"Exception while trying to attach file {e}")

    with smtplib.SMTP_SSL("smtp.gmail.com", port, context=context) as server:
        server.login(msg["From"], password)
        server.send_message(msg=msg, from_addr=msg["From"], to_addrs=None)


if __name__ == "__main__":
    print(platform.node())
    # send_email(['andreas.roth@h2.de', 'aroh975@gmail.com'], datetime.now().isoformat(' ', 'seconds'),
    #           '/home/pi/Measurements_web_app/reports/2022-01-07/2022-01-07T10:03:15.433423.pickle', 0)
    send_email(
        To_list=["jhthsch@gmail.com", "kontak@baudynamik-buero.de"],
        t=datetime.now().isoformat(" ", "seconds"),
        filename=None,
        channel=0,
        report_str="hardware_overrun",
    )

# 'aroh975@gmail.com'

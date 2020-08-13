import smtplib
from email.mime.text import MIMEText
import traceback
import datetime as dt

SMTPServer = 'smtp.163.com'
Sender = 'ahuxhh@163.com'
passwd = '111111'

def send_mail():
    message = "its a test "
    msg = MIMEText(message)
    msg["Subject"] = "test for subject"
    print(msg)
    try:
        mailServer = smtplib.SMTP(SMTPServer, 25)
        mailServer.set_debuglevel(1)
        print('yes')
        mailServer.login(Sender, passwd)
        mailServer.sendmail(Sender, ["ahuxhh@163.com"], msg.as_string())
        mailServer.quit()
    except Exception as e:
        print('failed')
        print(trace.format_exc())

def send_at_time(send_time):
    time.sleep(send_time.timestamp() - time.time())
    send_mail()

if __name__ == '__main__':
    first_send_time = dt.datetime(2020,8,13,12,0,0)
    interval = dt.timedelta(hours = 24*60*60)
    send_time = first_send_time
    while True:
        send_at_time(send_time)
        send_time = send_time + interval
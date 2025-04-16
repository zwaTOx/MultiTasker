import smtplib
from random import randint
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

load_dotenv()
SENDER_EMAIL = os.getenv('SENDER_EMAIL')
SENDER_EMAIL_PASSWORD = os.getenv('SENDER_EMAIL_PASSWORD')

def get_stmp(email):
    pattern = 'smtp.'
    domain_name = email.split('@')[1]   
    return pattern+domain_name, 587

def generate_code() -> str:
    code = str(randint(0, 999999))
    return code

def send_recovery_code(email: str, code: str =generate_code()):
    recovery_code = code
    smtp_server, smtp_port = get_stmp(SENDER_EMAIL)

    subject = 'Код восстановления'
    body = f'Ваш код восстановления: <b>{recovery_code:06}<b>'
    
    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['From'] = SENDER_EMAIL
    msg['To'] = email
    msg.attach(MIMEText(body, 'html'))

    # try:
    with smtplib.SMTP(smtp_server, smtp_port) as host:
        host.starttls()
        host.login(SENDER_EMAIL, SENDER_EMAIL_PASSWORD)
        host.sendmail(SENDER_EMAIL, email, msg.as_string())
    print("Код восстановления отправлен на", email)

    # except Exception as e:
    #     print("Ошибка при отправке письма:", e)
    return recovery_code

def send_project_invite(
    recipient_email: str,
    inviter_name: str,
    project_name: str,
    url: str,
    expire_in_minutes: int,
):
    """
    Отправляет приглашение в проект по email
    :param recipient_email: Email получателя
    :param inviter_name: Имя приглашающего
    :param project_name: Название проекта
    :param invite_url: Ссылка для принятия приглашения
    :param expire_in_minutes: Время жизни приглашения
    """
    smtp_server, smtp_port = get_stmp(SENDER_EMAIL)
    
    subject = f"Приглашение в проект {project_name}"
    body = f"""
    <html>
    <body>
        <h2>Вы получили приглашение в проект!</h2>
        <p>{inviter_name} приглашает вас присоединиться к проекту <strong>"{project_name}"</strong>.</p>
        <p>Для принятия приглашения перейдите по ссылке:</p>
        <p><a href="{url}">Принять приглашение</a></p>
        <p>Ссылка действительна 2 дня.</p>
        <p>Если вы не ожидали это приглашение, проигнорируйте это письмо.</p>
    </body>
    </html>
    """
    
    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['From'] = SENDER_EMAIL
    msg['To'] = recipient_email
    msg.attach(MIMEText(body, 'html'))

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as host:
            host.starttls()
            host.login(SENDER_EMAIL, SENDER_EMAIL_PASSWORD)
            host.sendmail(SENDER_EMAIL, recipient_email, msg.as_string())
        print(f"Приглашение в проект отправлено на {recipient_email}")
        return True
    except Exception as e:
        print(f"Ошибка при отправке приглашения:", e)
        return False

if __name__ == '__main__':
    result = send_project_invite(
        # "yakovva36@gmail.com", 
        "yakov.g.ruslanovich@gmail.com",
        "Test User",
        "Test Project", 
        "http://example.com/invite", 
        10
    )
    print(result)
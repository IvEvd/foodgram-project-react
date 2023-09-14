from django.core.mail import send_mail

from foodgram_backend.settings import SEND_EMAIL


def send_confirmation_code(email, confirmation_code):
    """Oтправляет на почту пользователя код подтверждения."""
    send_mail(
        subject='Код подтверждения',
        message=f'Ваш код подтверждения: {confirmation_code}',
        from_email=SEND_EMAIL,
        recipient_list=(email,),
        fail_silently=False,
    )

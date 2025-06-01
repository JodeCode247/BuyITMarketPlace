from django.core.mail import send_mail
from django.http import HttpResponse
from django.conf import settings

def send_test_email():
    subject = 'Test Email from Django'
    message = 'This is a test email sent using Outlook from your Django application.'
    from_email = settings.EMAIL_HOST_USER   # Use the same email as EMAIL_HOST_USER
    recipient_list = ['nwizugbejohn@gmail.com']  # Replace with the recipient's email address

    send_mail(subject, message, from_email, recipient_list)
    return HttpResponse("Email sent successfully!")
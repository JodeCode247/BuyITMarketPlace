
from django.contrib.auth import get_user_model
from social_core.pipeline.user import create_user as social_create_user
from django.utils import timezone
from django.contrib.auth.hashers import make_password


def create_user(strategy, details, backend, user=None, *args, **kwargs):
    """
    Creates or updates a user using the custom MyUser model.
    """
    UserModel = get_user_model()

    if user:
        return {'user': user, 'is_new': False}

    if not details.get('email'):
        return None

    try:
        user = UserModel.objects.get(email=details['email'])
        return {'user': user, 'is_new': False}
    except UserModel.DoesNotExist:
        # User doesn't exist, create a new one
        username = details.get('username') or details.get('email').split('@')[0] #get the username from the details, if it does not exist, use the email.
        email = details.get('email')

        # Check for existing username and make it unique if necessary
        counter = 1
        while UserModel.objects.filter(username=username).exists():
            username = f"{details.get('username') or details.get('email').split('@')[0]}{counter}"
            counter += 1
        
        password = UserModel.objects.make_random_password()

        print(password)

        user = UserModel.objects.create_user(username=username, email=email, password=password)
        user.is_active = True
        user.save()

        return {'user': user, 'is_new': True}

def save_profile_data(strategy, details, backend, user=None, *args, **kwargs):
    """Saves profile data from Google into user object."""
    if backend.name == 'google-oauth2' and user:
        # profile_picture = kwargs.get('response', {}).get('picture')
        first_name = kwargs.get('response', {}).get('given_name')
        last_name = kwargs.get('response', {}).get('family_name')

        if first_name:
            user.username = first_name
        elif last_name:
            user.username = last_name

        user.save()

        # You can save the profile_picture to a model field if needed
        # Example: user.profile_picture_url = profile_picture

        return {'user': user}
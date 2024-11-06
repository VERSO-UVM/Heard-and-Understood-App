from firebase_admin import auth


def create_user(email, password):
    user = auth.create_user(
        email=email,
        password=password
    )
    return user


def verify_user(email, password):
    return auth.get_user_by_email(email)

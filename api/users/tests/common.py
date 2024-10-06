from django.urls import reverse
from django.contrib.auth import get_user_model


def drop_dict_field(d, key):
    new_d = d.copy()
    new_d.pop(key)
    return new_d


def create_user(use_custom_data=False, verify_email=True, **kwargs):
    if use_custom_data:
        data = {
            'email': kwargs["email"],
            'password': kwargs["password"],
            'first_name': kwargs["first_name"],
            'last_name': kwargs["last_name"],
        }
    else:
        data = {
            'email': 'carl.sagan@bob.bob',
            'password': 'foo',
            'first_name': "Carl",
            'last_name': "Sagan"
        }

    user = get_user_model().objects.create_user(**data,
                                                is_active=verify_email,
                                                is_verified=verify_email)
    user.raw_password = data["password"]
    return user


def create_superuser(use_custom_data, **kwargs):
    if use_custom_data:
        data = {'email': kwargs['email'], 'password': kwargs['password']}
    else:
        data = {'email': 'admin@user.com', 'password': 'admin_foo'}
    admin_user = get_user_model().objects.create_superuser(
        email=data["email"],
        password=data["password"]
    )
    admin_user.raw_password = data["password"]
    return admin_user


def create_and_login_superuser(client, use_custom_data=False, **kwargs):
    user = create_superuser(use_custom_data=use_custom_data, **kwargs)
    client.login(email=user.email, password=user.raw_password)
    return user


def login_user(client, user):
    response = client.post(reverse("token_obtain_pair"),
                           data={"email": user.email,
                                 "password": user.raw_password})
    user_token = response.data['access']
    client.credentials(HTTP_AUTHORIZATION="Bearer " + user_token)

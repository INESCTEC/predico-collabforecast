from users.models.user_resources import UserResources
from users.models.user_wallet import UserWalletAddress

from .common import (
    create_user,
)


def create_users_list(nr_users=1):
    user_list = []
    for i in range(nr_users):
        user_list.append({
            'email': f'normal{i}@user.com',
            'password': f'normal{i}_foo',
            'first_name': f'Normal{i}',
            'last_name': f'Peanut{i}'
        })
    return user_list


def create_user_resources(user_id, nr_resources=1, to_forecast=True):
    user_resources = []
    for i in range(nr_resources):
        user_resources.append(
            {
                "user_id": user_id,
                "name": f"resource-{i}",
                "type": "measurements",
                "to_forecast": to_forecast
            }
        )
    return user_resources


def create_users_and_resources(nr_users=1, nr_resources_per_user=1):
    users_data_list = create_users_list(nr_users)
    users = []
    for user_data in users_data_list:
        user = create_user(use_custom_data=True, **user_data)
        user_resources_data = create_user_resources(
            user_id=user.id,
            nr_resources=nr_resources_per_user,
            to_forecast=True
        )

        UserWalletAddress.objects.create(
            user_id=user.id,
            wallet_address=f"c3a953db074113291020b39eeb20d116833f31f590b533e967efb247100bd67{user.id}"
        )

        resources = []
        for res_data in user_resources_data:
            resources.append(UserResources.objects.create(**res_data))

        users.append({
            "user": user,
            "resources": resources
        })

    return users

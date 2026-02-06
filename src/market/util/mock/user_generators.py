def generate_users(nr_users):
    names = [f"bob_{x}" for x in range(nr_users)]
    passwords = [f"password_{x}!" for x in range(nr_users)]
    agent_info_list = []
    for name, password in zip(names, passwords):
        first_name = name.split("_")[0]
        last_name = name.split("_")[-1]
        agent_info_list.append(
            {
                "email": f"{name}@inesctec.pt",
                "password": password,
                "first_name": first_name,
                "last_name": last_name,
                "role": [1, 2],  # buyer & seller
            }
        )
    return agent_info_list

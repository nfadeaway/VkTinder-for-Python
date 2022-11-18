from models.vk import VK


def open_token(path):
    with open(path, 'r') as file:
        token = file.read().strip()
    return token


if __name__ == "__main__":
    user_token = open_token('private/user_token.txt')
    group_token = open_token('private/group_token.txt')
    vk = VK(user_token, group_token)
    vk.main()
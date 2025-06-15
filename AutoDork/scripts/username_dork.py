def get_metadata():
    return {
        "name": "Username Dork (Multi-Site)",
        "description": "Searches for username traces across major social, paste, and document sites.",
        "inputs": [{"name": "username", "prompt": "Enter the target username:"}],
    }


def generate_dorks(inputs):
    username = inputs["username"]
    dorks = [
        f'"{username}"',
        f'site:twitter.com "{username}"',
        f'site:instagram.com "{username}"',
        f'site:reddit.com "{username}"',
        f'site:tiktok.com "{username}"',
        f'site:facebook.com "{username}"',
        f'site:github.com "{username}"',
        f'site:pinterest.com "{username}"',
        f'site:linkedin.com "{username}"',
        f"inurl:{username}",
        f'inurl:{username.replace(".", "")}',
        f'inurl:{username.replace(".", "-")}',
        f'inurl:{username.replace(".", "_")}',
        f"intext:{username}",
        f"intitle:{username}",
        f'filetype:pdf "{username}"',
        f'filetype:txt "{username}"',
        f'filetype:xls "{username}"',
        f'site:pastebin.com "{username}"',
        f'site:ghostbin.com "{username}"',
        f'site:hastebin.com "{username}"',
        f'inurl:profile "{username}"',
        f'inurl:user "{username}"',
        f"site:github.com inurl:{username}",
    ]
    return dorks

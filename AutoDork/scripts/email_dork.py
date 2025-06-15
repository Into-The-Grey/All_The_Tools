def get_metadata():
    return {
        "name": "Email Dork",
        "description": "Searches for traces of an email address in leaks and public docs.",
        "inputs": [{"name": "email", "prompt": "Enter the target email address:"}],
    }


def generate_dorks(inputs):
    email = inputs["email"]
    return [
        f'"{email}"',
        f'site:pastebin.com "{email}"',
        f'filetype:txt "{email}"',
        # more as you want...
    ]

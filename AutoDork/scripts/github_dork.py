# scripts/github_dork.py


def get_metadata():
    return {
        "name": "GitHub Username Dork",
        "description": "Finds public GitHub profiles by username.",
        "inputs": [{"name": "username", "prompt": "Enter GitHub username:"}],
    }


def generate_dorks(inputs):
    username = inputs["username"]
    return [f'site:github.com "{username}"']

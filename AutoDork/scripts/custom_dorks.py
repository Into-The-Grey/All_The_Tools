# Place advanced or site-specific dork builders here for future expansion.


def extra_dorks(username):
    return [
        f'site:myspace.com "{username}"',
        f'site:dev.to "{username}"',
        # etc...
    ]

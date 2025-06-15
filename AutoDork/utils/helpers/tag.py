from InquirerPy import inquirer # type: ignore


def tag_urls(urls):
    tagged = {}
    tag_choices = [
        "credential leak",
        "profile",
        "forum",
        "paste",
        "to review",
        "ignore",
        "other",
    ]
    for url in urls:
        tags = inquirer.checkbox(
            message=f"Tags for:\n{url}\n(space = select, enter when done)",
            choices=tag_choices,
            instruction="Choose tags",
        ).execute()
        if "other" in tags:
            custom_tag = inquirer.text(
                message="Enter custom tag(s) (comma-separated):"
            ).execute()
            if custom_tag.strip():
                tags.extend([x.strip() for x in custom_tag.split(",") if x.strip()])
        tagged[url] = list(set([t for t in tags if t != "other"]))
    return tagged

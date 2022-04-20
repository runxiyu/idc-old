class config:
    server_name = "home.andrewyu.org"
    users = {
        b"andrew": {
            "password": b"hunter2",
            "bio": b"Andrew Yu",
            "permissions": {"god"},
            "options": ["offline-messages", "eat-cookies"],
        },
        b"hax": {
            "password": b"lurk",
            "bio": b"Professional h4xx0r",
            "permissions": {"god"},
            "options": ["offline-messages", "eat-cookies"],
        },
        b"luk3yx": {
            "password": b"billy",
            "bio": b"Random bot",
            "permissions": {"god"},
            "options": ["offline-messages", "eat-cookies"],
        },
        b"lurk": {
            "password": b"HQWkf36lIttHBYGifwvcjso6RGPN2Ne_frrt6FpP3qc",
            "bio": b"Random human",
            "permissions": set(),
            "options": ["bot", "no-offline-messages"],
        }
    }

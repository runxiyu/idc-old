class listen:
    port = 1025


server_name = b"andrewyu.org"
users = {
    b"Noisytoot": {
        "password": b"pissnet",
        "bio": b"Ron",
        "permissions": {"kill", "new-guild"},
        "options": ["offline-messages", "eat-cookies"],
    },
    b"andrew": {
        "password": b"hunter2",
        "bio": b"Andrew Yu",
        "permissions": {"kill", "new-guild"},
        "options": ["offline-messages", "eat-cookies"],
    },
    b"hax": {
        "password": b"lurk",
        "bio": b"Professional h4xx0r",
        "permissions": {"kill", "new-guild"},
        "options": ["offline-messages", "eat-cookies"],
    },
    b"luk3yx": {
        "password": b"billy",
        "bio": b"Random bot",
        "permissions": {"kill", "new-guild"},
        "options": ["offline-messages", "eat-cookies"],
    },
    b"idcbot": {
        "password": b"",
        "bio": b"Nice person",
        "permissions": {"kill", "new-guild"},
        "options": ["offline-messages", "eat-cookies"],
    },
    b"vitali64": {
        "password": b"hello",
        "bio": b"Nice person",
        "permissions": {"kill", "new-guild"},
        "options": ["offline-messages", "eat-cookies"],
    },
    b"lurk": {
        "password": b"HQWkf36lIttHBYGifwvcjso6RGPN2Ne_frrt6FpP3qc",
        "bio": b"Random human",
        "permissions": {"kill"},
        "options": ["bot"],
    },
}

guilds = {
    b"Haxxors": {
        "description": b"Haxxors guild",
        "user_roles": [],
        "channels": [],
        "users": {b"Andrew", b"lurk"},
        "roles": [],
    }
}

channels = {
    b"hackers": {
        "broadcast_to": {b"andrew", b"lurk", b"luk3yx", b"hax", b"vitali64"}
    }
}

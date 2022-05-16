import entities


class listen:
    port = 1025


server_name = b"andrewyu.org"
users = {
    b"guest@" + server_name: {
        "password": b"guest",
        "bio": b"Guest",
        "permissions": set(),
        "options": ["offline-messages", "eat-cookies"],
    },
    b"Noisytoot@" + server_name: {
        "password": b"pissnet",
        "bio": b"Ron",
        "permissions": {"kill", "new-guild"},
        "options": ["offline-messages", "eat-cookies"],
    },
    b"andrew@" + server_name: {
        "password": b"hunter2",
        "bio": b"Andrew Yu",
        "permissions": {"kill", "new-guild"},
        "options": ["offline-messages", "eat-cookies"],
    },
    b"hax@" + server_name: {
        "password": b"lurk",
        "bio": b"Professional h4xx0r",
        "permissions": {"kill", "new-guild"},
        "options": ["offline-messages", "eat-cookies"],
    },
    b"luk3yx@" + server_name: {
        "password": b"billy",
        "bio": b"Random bot",
        "permissions": {"kill", "new-guild"},
        "options": ["offline-messages", "eat-cookies"],
    },
    b"idcbot@" + server_name: {
        "password": b"",
        "bio": b"#IDC relay bot",
        "permissions": {"kill", "new-guild"},
        "options": ["offline-messages", "eat-cookies"],
    },
    b"speechbot@" + server_name: {
        "password": b"",
        "bio": b"#librespeech relay bot",
        "permissions": {"kill", "new-guild"},
        "options": ["offline-messages", "eat-cookies"],
    },
    b"vitali64@" + server_name: {
        "password": b"hello",
        "bio": b"Nice person",
        "permissions": {"kill", "new-guild"},
        "options": ["offline-messages", "eat-cookies"],
    },
    b"lurk@" + server_name: {
        "password": b"HQWkf36lIttHBYGifwvcjso6RGPN2Ne_frrt6FpP3qc",
        "bio": b"Random human",
        "permissions": {"kill"},
        "options": ["bot"],
    },
}

guilds = {
    b"haxxors@" + server_name: {
        "description": b"Haxxors guild",
        "user_roles": [],
        "channels": [],
        "users": {b"Andrew", b"lurk"},
        "roles": [],
    }
}


channels = {
    b"librespeech@" + server_name: {
        "broadcast_to": {
            b"@andrew@andrewyu.org",
            b"@Noisytoot@andrewyu.org",
            b"@lurk@andrewyu.org",
            b"@luk3yx@andrewyu.org",
            b"@hax@andrewyu.org",
            b"@vitali64@andrewyu.org",
            b"@speechbot@andrewyu.org",
        }
    },
    b"hackers@" + server_name: {
        "broadcast_to": {
            b"@andrew@andrewyu.org",
            b"@lurk@andrewyu.org",
            b"@Noisytoot@andrewyu.org",
            b"@luk3yx@andrewyu.org",
            b"@hax@andrewyu.org",
            b"@vitali64@andrewyu.org",
            b"@idcbot@andrewyu.org",
        }
    },
}


guilds = {
    b"idc": {
        "users": {
            b"andrew@andrewyu.org",
            b"lurk@andrewyu.org",
            b"Noisytoot@andrewyu.org",
            b"luk3yx@andrewyu.org",
            b"hax@andrewyu.org",
            b"vitali64@andrewyu.org",
            b"idcbot@andrewyu.org",
        },
        "channels": {
            b"testing@andrewyu.org",
            b"protocol@andrewyu.org",
            b"server@andrewyu.org",
            b"client@andrewyu.org",
            b"general@andrewyu.org",
        },
    }
}


motd = b"""Hi there! This is the best IDC server you'll ever encounter.  Good luck!"""

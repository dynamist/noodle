{
    "name": "noodle Website",
    "summary": "Pages, menus and styles of the noodle website",
    "version": "1.0",
    "category": "Website",
    "author": "Dynamist AB",
    "license": "Other OSI approved licence",
    "depends": ["website"],
    "data": [
        "views/homepage.xml",
        "views/pages.xml",
        "data/menus.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "noodle_website/static/src/scss/website.scss",
        ],
    },
}

"""Feature definitions shared by inference and API validation."""

CONFIG_PREPROCESS = {
    "cities_mapping": {
        "فاس": "Fès",
        "أكادير": "Agadir",
        "مراكش": "Marrakech",
        "القنيطرة": "Kénitra",
        "الدار البيضاء": "Casablanca",
        "Agadir Melloul": "Agadir",
    },
    "status_mapping": {
        "Neuf": 5,
        "Excellent": 4,
        "Très bon": 3,
        "Bon": 2,
        "Correct": 1,
        "Endommagé": 0,
        "Pour Pièces": -1,
    },
    "safety_features": [
        "ABS",
        "Airbags",
        "ESP",
        "Caméra de recul",
        "Radar de recul",
        "Régulateur de vitesse",
        "Limiteur de vitesse",
    ],
    "comfort_features": [
        "Climatisation",
        "Sièges cuir",
        "Toit ouvrant",
        "Vitres électriques",
        "Verrouillage centralisé à distance",
    ],
    "tech_features": [
        "CD/MP3/Bluetooth",
        "Système de navigation/GPS",
        "Ordinateur de bord",
        "Jantes aluminium",
    ],
}

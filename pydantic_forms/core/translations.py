from pydantic_i18n import PydanticI18n

translations = {
    "en_US": {
        "Field required": "field required",
    },
    "de_DE": {
        "Field required": "Feld erforderlich",
        "Value should have at least 1 item after validation, not 0": "Der Wert sollte nach der Validierung mindestens 1 Element haben, nicht 0",
    },
    "nl_NL": {
        "Field required": "Veld verplicht",
        "Value should have at least 1 item after validation, not 0": "De waarde moet na validatie minimaal 1 item bevatten, niet 0",
    },
}


tr = PydanticI18n(translations)

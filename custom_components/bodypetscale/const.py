"""Constants for the BodyPetScale integration."""

DOMAIN = "bodypetscale"
NAME = "BodyPetScale"
VERSION = "2026.1.0"

ISSUE_URL = "https://github.com/dckiller51/bodypetscale/issues"
MORPHOLOGY_URL = "https://dckiller51.github.io/bodypetscale/"

CONF_ACTIVITY = "activity"
CONF_APPETITE = "appetite"
CONF_ANIMAL_TYPE = "animal_type"
CONF_BIRTHDAY = "birthday"
CONF_BREED = "breed"
CONF_LAST_TIME_SENSOR = "last_time_sensor"
CONF_LIVING_ENVIRONMENT = "living_environment"
CONF_MORPHOLOGY = "morphology"
CONF_REPRODUCTIVE = "reproductive"
CONF_TEMPERAMENT = "temperament"
CONF_WEIGHT_SENSOR = "weight_sensor"

ATTR_BODY_TYPE = "body_type"
ATTR_IDEAL = "ideal_weight"
ATTR_ENERGY_NEED = "energy_need"
ATTR_MAIN = "main"

ACTIVITY_LEVELS = {
    "dog": [
        "active_sporty",
        "calm",
        "convalescent",
        "normal",
        "hyperactive_very_sporty",
        "very_calm",
    ],
    "cat": [
        "limited_outdoor_access",
        "no_outdoor_access",
        "outdoor_access",
    ],
}

ANIMAL_LABELS = {"dog": "Dog", "cat": "Cat"}

ANIMAL_TYPES = ["dog", "cat"]

BREED_OPTIONS = {
    "dog": [
        "afghan_hound",
        "affenpinscher",
        "akita_inu",
        "alaskan_malamute",
        "american_akita",
        "american_bulldog",
        "american_cocker_spaniel",
        "american_shepherd",
        "american_staffordshire_terrier",
        "anatolian_shepherd_dog",
        "ardennes_cattle_dog",
        "ariegeois",
        "australian_cattle_dog",
        "australian_kelpie",
        "australian_shepherd",
        "azawakh",
        "basset_artesien_normand",
        "basset_fauve_de_bretagne",
        "basset_hound",
        "bavarian_mountain_hound",
        "beagle",
        "beagle_harrier",
        "bearded_collie",
        "beauceron",
        "bedlington_terrier",
        "belgian_shepherd_gronendael",
        "belgian_shepherd_laekenois",
        "belgian_shepherd_malinois",
        "belgian_shepherd_tervuren",
        "bernese_mountain_dog",
        "bichon_frise",
        "blue_gascony_basset",
        "bolognese",
        "border_collie",
        "border_terrier",
        "borzoi",
        "boston_terrier",
        "bouvier_des_flandres",
        "boxer",
        "briard",
        "brittany_spaniel",
        "brussels_griffon",
        "bull_terrier",
        "bullmastiff",
        "cairn_terrier",
        "cane_corso",
        "catalan_sheepdog",
        "cavalier_king_charles_spaniel",
        "chihuahua",
        "chinese_crested_dog",
        "chow_chow",
        "cirneco_dell_etna",
        "clumber_spaniel",
        "cocker_spaniel",
        "collie",
        "coton_de_tulear",
        "curly_coated_retriever",
        "czechoslovakian_wolfdog",
        "dalmatian",
        "dandie_dinmont_terrier",
        "doberman_pinscher",
        "dogo_argentino",
        "dogue_de_bordeaux",
        "dutch_shepherd",
        "east_siberian_laika",
        "english_bulldog",
        "english_cocker_spaniel",
        "entlebucher_mountain_dog",
        "eurasier",
        "finnish_lapphund",
        "flat_coated_retriever",
        "fox_terrier",
        "french_bulldog",
        "french_pointer",
        "german_shepherd",
        "german_pointer",
        "golden_retriever",
        "great_dane",
        "great_pyrenees",
        "greater_swiss_mountain_dog",
        "greenland_dog",
        "greyhound",
        "griffon_fauve_de_bourgogne",
        "icelandic_sheepdog",
        "irish_wolfhound",
        "italian_greyhound",
        "jack_russell_terrier",
        "japanese_chin",
        "kai_ken",
        "karelian_bear_dog",
        "king_charles_spaniel",
        "komondor",
        "lagotto_romagnolo",
        "landseer",
        "lapphund_swedish",
        "leonberger",
        "lhasa_apso",
        "lowchen",
        "magyar_agar",
        "maltese",
        "manchester_terrier",
        "mastiff",
        "miniature_pinscher",
        "miniature_poodle",
        "neapolitan_mastiff",
        "norwegian_buhund",
        "norwegian_elkhound",
        "norwegian_lundehund",
        "old_english_sheepdog",
        "papillon",
        "parson_russell_terrier",
        "pekingese",
        "pointer",
        "polish_greyhound",
        "porcelaine",
        "portuguese_water_dog",
        "prague_ratter",
        "pug",
        "pyrenean_shepherd",
        "rhodesian_ridgeback",
        "rottweiler",
        "russian_european_laika",
        "saint_bernard",
        "saluki",
        "samoyed",
        "saarloos_wolfdog",
        "scottish_deerhound",
        "shetland_sheepdog",
        "shiba_inu",
        "shih_tzu",
        "siberian_husky",
        "spanish_greyhound",
        "spanish_mastiff",
        "spanish_water_dog",
        "standard_pinscher",
        "standard_poodle",
        "swedish_elkhound",
        "tibetan_mastiff",
        "tibetan_spaniel",
        "toy_poodle",
        "vizsla",
        "weimaraner",
        "west_siberian_laika",
        "white_swiss_shepherd",
        "wirehaired_pointing_griffon",
    ],
    "cat": [
        "abyssinian",
        "american_bobtail",
        "american_curl",
        "american_shorthair",
        "american_wirehair",
        "balinese",
        "bengal",
        "birman",
        "bombay",
        "british_longhair",
        "british_shorthair",
        "burmese",
        "chartreux",
        "cornish_rex",
        "devon_rex",
        "domestic_longhair",
        "domestic_mediumhair",
        "domestic_shorthair",
        "egyptian_mau",
        "exotic_shorthair",
        "havana_brown",
        "highland_fold",
        "japanese_bobtail",
        "javanese",
        "korat",
        "maine_coon",
        "mandarin",
        "manx",
        "mixed_breed_or_other_breed",
        "munchkin",
        "norwegian_forest",
        "oriental_shorthair",
        "persian",
        "pixie_bob",
        "ragdoll",
        "russian_blue",
        "sacred_birman",
        "savannah",
        "scottish_fold",
        "siamese",
        "siberian",
        "snowshoe",
        "somali",
        "sphynx",
        "thai",
        "tonkinese",
        "turkish_angora",
        "turkish_van",
    ],
}

CAT_TEMPERAMENT_OPTIONS = [
    "active",
    "calm",
    "highly_stressed",
    "normal",
    "slightly_stressed",
    "stressed",
    "very_calm",
]

DOG_APPETITE_OPTIONS = [
    "hearty_eater",
    "normal",
    "small_eater",
]

LIVING_ENVIRONMENT_OPTIONS = {
    "dog": [
        "indoors",
        "outdoors_summer_20",
        "outdoors_summer_30",
        "outdoors_winter_0",
        "outdoors_winter_10",
    ],
    "cat": [
        "indoors",
        "outdoors_summer",
        "outdoors_winter",
    ],
}

MORPHOLOGY_OPTIONS = [
    "1_very_thin",
    "2_underweight",
    "3_slightly_underweight",
    "4_ideal",
    "5_ideal",
    "6_slightly_overweight",
    "7_overweight",
    "8_obese",
    "9_very_obese",
]

REPRODUCTIVE_STATUS = [
    "intact",
    "neutered",
    "spayed",
]

STARTUP_MESSAGE = f"""
-------------------------------------------------------------------
{NAME}
Version: {VERSION}
This is a custom integration!
If you have any issues with this you need to open an issue here:
{ISSUE_URL}
-------------------------------------------------------------------
"""

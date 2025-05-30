"""Data tables module."""

ACTIVITY_FACTORS: dict[str, float] = {
    "active_sporty": 1.1,
    "calm": 0.9,
    "convalescent": 0.7,
    "hyperactive_very_sporty": 1.2,
    "limited_outdoor_access": 1.0,
    "normal": 1.0,
    "no_outdoor_access": 0.9,
    "outdoor_access": 1.1,
    "very_calm": 0.8,
}

APPETITE_FACTORS: dict[str, float] = {
    "hearty_eater": 1.0,
    "normal": 1.0,
    "small_eater": 1.0,
}

BREED_FACTORS: dict[str, float] = {
    "abyssinian": 1.2,
    "afghan_hound": 1.2,
    "affenpinscher": 1.0,
    "akita_inu": 1.0,
    "alaskan_malamute": 0.8,
    "american_akita": 1.0,
    "american_bobtail": 1.0,
    "american_bulldog": 1.0,
    "american_cocker_spaniel": 0.9,
    "american_curl": 1.0,
    "american_shepherd": 1.0,
    "american_shorthair": 1.0,
    "american_staffordshire_terrier": 1.0,
    "anatolian_shepherd_dog": 0.9,
    "ardennes_cattle_dog": 1.0,
    "ariegeois": 1.0,
    "australian_cattle_dog": 1.0,
    "australian_kelpie": 1.0,
    "australian_shepherd": 1.0,
    "american_wirehair": 1.0,
    "azawakh": 1.2,
    "balinese": 1.0,
    "basset_artesien_normand": 1.0,
    "basset_fauve_de_bretagne": 1.0,
    "basset_hound": 0.9,
    "bavarian_mountain_hound": 1.0,
    "beagle": 0.9,
    "beagle_harrier": 1.0,
    "bearded_collie": 1.0,
    "beauceron": 1.0,
    "bedlington_terrier": 1.0,
    "belgian_shepherd_gronendael": 1.0,
    "belgian_shepherd_laekenois": 1.0,
    "belgian_shepherd_malinois": 1.0,
    "belgian_shepherd_tervuren": 1.0,
    "bengal": 1.1,
    "bernese_mountain_dog": 0.9,
    "bichon_frise": 1.0,
    "birman": 1.0,
    "blue_gascony_basset": 1.0,
    "bolognese": 1.0,
    "bombay": 1.0,
    "border_collie": 1.0,
    "border_terrier": 1.0,
    "borzoi": 1.2,
    "boston_terrier": 1.0,
    "bouvier_des_flandres": 1.0,
    "boxer": 1.1,
    "briard": 1.0,
    "british_longhair": 1.0,
    "british_shorthair": 1.0,
    "brittany_spaniel": 1.0,
    "brussels_griffon": 1.0,
    "bull_terrier": 1.0,
    "bullmastiff": 0.9,
    "burmese": 1.0,
    "cairn_terrier": 0.9,
    "cane_corso": 1.0,
    "catalan_sheepdog": 1.0,
    "cavalier_king_charles_spaniel": 0.9,
    "chartreux": 1.0,
    "chihuahua": 1.0,
    "chinese_crested_dog": 1.0,
    "chow_chow": 0.9,
    "cirneco_dell_etna": 1.0,
    "clumber_spaniel": 1.0,
    "cocker_spaniel": 0.9,
    "collie": 0.9,
    "cornish_rex": 1.0,
    "coton_de_tulear": 1.0,
    "curly_coated_retriever": 0.8,
    "czechoslovakian_wolfdog": 1.0,
    "dalmatian": 1.0,
    "dandie_dinmont_terrier": 1.0,
    "devon_rex": 1.0,
    "doberman_pinscher": 1.1,
    "dogo_argentino": 1.0,
    "dogue_de_bordeaux": 0.9,
    "domestic_longhair": 1.0,
    "domestic_mediumhair": 1.0,
    "domestic_shorthair": 1.0,
    "dutch_shepherd": 1.0,
    "east_siberian_laika": 0.8,
    "egyptian_mau": 1.0,
    "english_bulldog": 0.9,
    "english_cocker_spaniel": 0.9,
    "entlebucher_mountain_dog": 1.0,
    "eurasier": 1.0,
    "exotic_shorthair": 1.0,
    "finnish_lapphund": 0.8,
    "flat_coated_retriever": 0.8,
    "fox_terrier": 1.0,
    "french_bulldog": 1.0,
    "french_pointer": 1.0,
    "german_shepherd": 1.0,
    "german_pointer": 1.0,
    "golden_retriever": 0.8,
    "great_dane": 1.2,
    "great_pyrenees": 0.9,
    "greater_swiss_mountain_dog": 1.0,
    "greenland_dog": 0.8,
    "greyhound": 1.2,
    "griffon_fauve_de_bourgogne": 1.0,
    "havana_brown": 1.0,
    "highland_fold": 1.0,
    "icelandic_sheepdog": 0.8,
    "irish_wolfhound": 1.2,
    "italian_greyhound": 1.2,
    "jack_russell_terrier": 1.0,
    "japanese_bobtail": 1.0,
    "japanese_chin": 1.0,
    "javanese": 1.0,
    "kai_ken": 1.0,
    "karelian_bear_dog": 0.8,
    "king_charles_spaniel": 1.0,
    "komondor": 0.9,
    "korat": 1.0,
    "lagotto_romagnolo": 1.0,
    "landseer": 0.9,
    "lapphund_swedish": 0.8,
    "leonberger": 0.9,
    "lhasa_apso": 1.0,
    "lowchen": 1.0,
    "magyar_agar": 1.2,
    "maine_coon": 1.0,
    "maltese": 1.0,
    "manchester_terrier": 1.0,
    "mandarin": 1.0,
    "manx": 1.0,
    "mastiff": 0.9,
    "miniature_pinscher": 1.0,
    "miniature_poodle": 1.0,
    "mixed_breed_or_other_breed": 1.0,
    "munchkin": 1.0,
    "neapolitan_mastiff": 0.9,
    "norwegian_buhund": 0.8,
    "norwegian_elkhound": 0.8,
    "norwegian_forest": 1.0,
    "norwegian_lundehund": 0.8,
    "old_english_sheepdog": 1.0,
    "oriental_shorthair": 1.1,
    "papillon": 1.0,
    "parson_russell_terrier": 1.0,
    "pekingese": 1.0,
    "persian": 1.0,
    "pixie_bob": 1.0,
    "pointer": 1.0,
    "polish_greyhound": 1.2,
    "porcelaine": 1.0,
    "portuguese_water_dog": 1.0,
    "prague_ratter": 1.0,
    "pug": 0.9,
    "pyrenean_shepherd": 1.0,
    "ragdoll": 1.0,
    "rhodesian_ridgeback": 1.0,
    "rottweiler": 0.9,
    "russian_blue": 1.0,
    "russian_european_laika": 0.8,
    "saarloos_wolfdog": 1.0,
    "sacred_birman": 1.0,
    "saint_bernard": 0.9,
    "saluki": 1.2,
    "samoyed": 0.8,
    "savannah": 1.1,
    "scottish_deerhound": 1.2,
    "scottish_fold": 1.0,
    "shetland_sheepdog": 0.9,
    "shiba_inu": 1.0,
    "shih_tzu": 1.0,
    "siamese": 1.0,
    "siberian": 1.0,
    "siberian_husky": 0.9,
    "snowshoe": 1.0,
    "somali": 1.0,
    "spanish_greyhound": 1.2,
    "spanish_mastiff": 0.9,
    "spanish_water_dog": 1.0,
    "sphynx": 1.2,
    "standard_pinscher": 1.0,
    "standard_poodle": 1.0,
    "swedish_elkhound": 0.8,
    "thai": 1.0,
    "tibetan_mastiff": 0.9,
    "tibetan_spaniel": 1.0,
    "tonkinese": 1.0,
    "toy_poodle": 1.0,
    "turkish_angora": 1.0,
    "turkish_van": 1.0,
    "vizsla": 1.0,
    "weimaraner": 1.1,
    "west_siberian_laika": 0.8,
    "white_swiss_shepherd": 1.0,
    "wirehaired_pointing_griffon": 1.0,
}

CAT_LIFE_STAGE_FACTORS: dict[str, float] = {
    "kitten_2_4": 1.9,
    "kitten_4_6": 1.6,
    "kitten_6_8": 1.3,
    "young_adult_8_12": 1.1,
    "adult": 1.0,
    "senior": 1.0,
}

DOG_LIFE_STAGE_FACTORS: dict[str, float] = {
    "puppy_low_3_4": 1.6,
    "puppy_low_5_7": 1.3,
    "puppy_low_8_10": 1.1,
    "puppy_20_3_5": 1.6,
    "puppy_20_6_9": 1.3,
    "puppy_20_10_12": 1.1,
    "puppy_35_3_6": 1.6,
    "puppy_35_7_8": 1.4,
    "puppy_35_9_10": 1.2,
    "puppy_35_11_15": 1.1,
    "puppy_50_3_5": 1.6,
    "puppy_50_6_7": 1.4,
    "puppy_50_8_13": 1.2,
    "puppy_50_14_18": 1.1,
    "puppy_high_3_6": 1.7,
    "puppy_high_7_8": 1.4,
    "puppy_high_9_13": 1.2,
    "puppy_high_14_21": 1.1,
    "adult": 1.0,
    "senior": 1.0,
}

ENVIRONMENT_FACTORS: dict[str, float] = {
    "indoors": 1.0,
    "outdoors_summer": 1.05,
    "outdoors_summer_20": 1.0,
    "outdoors_summer_30": 1.2,
    "outdoors_winter": 1.18,
    "outdoors_winter_0": 1.3,
    "outdoors_winter_10": 1.1,
}

MORPHOLOGY_FACTORS: dict[str, float] = {
    "1_very_thin": 1.2,
    "2_underweight": 1.1,
    "3_slightly_underweight": 1.1,
    "4_ideal": 1.0,
    "5_ideal": 1.0,
    "6_slightly_overweight": 0.9,
    "7_overweight": 0.9,
    "8_obese": 0.8,
    "9_very_obese": 0.8,
}

MORPHOLOGY_PERCENTAGES: dict[int, dict[str, float]] = {
    1: {"dog": 1.4, "cat": 1.3},
    2: {"dog": 1.3, "cat": 1.225},
    3: {"dog": 1.2, "cat": 1.15},
    4: {"dog": 1.1, "cat": 1.075},
    5: {"dog": 1.0, "cat": 1.0},
    6: {"dog": 0.9, "cat": 0.925},
    7: {"dog": 0.8, "cat": 0.85},
    8: {"dog": 0.7, "cat": 0.775},
    9: {"dog": 0.6, "cat": 0.7},
}

PUPPY_STAGES = [
    ((0, 10), (3, 4), "puppy_low_3_4"),
    ((0, 10), (5, 7), "puppy_low_5_7"),
    ((0, 10), (8, 10), "puppy_low_8_10"),
    ((10, 21), (3, 5), "puppy_20_3_5"),
    ((10, 21), (6, 9), "puppy_20_6_9"),
    ((10, 21), (10, 12), "puppy_20_10_12"),
    ((21, 36), (3, 6), "puppy_35_3_6"),
    ((21, 36), (7, 8), "puppy_35_7_8"),
    ((21, 36), (9, 10), "puppy_35_9_10"),
    ((21, 36), (11, 15), "puppy_35_11_15"),
    ((36, 51), (3, 5), "puppy_50_3_5"),
    ((36, 51), (6, 7), "puppy_50_6_7"),
    ((36, 51), (8, 13), "puppy_50_8_13"),
    ((36, 51), (14, 18), "puppy_50_14_18"),
    ((51, float("inf")), (3, 6), "puppy_high_3_6"),
    ((51, float("inf")), (7, 8), "puppy_high_7_8"),
    ((51, float("inf")), (9, 13), "puppy_high_9_13"),
    ((51, float("inf")), (14, 21), "puppy_high_14_21"),
]

REPRODUCTIVE_FACTORS: dict[str, float] = {
    "intact": 1.0,
    "neutered": 0.8,
    "spayed": 0.8,
}

TEMPERAMENT_FACTORS: dict[str, float] = {
    "active": 1.1,
    "calm": 0.9,
    "highly_stressed": 1.2,
    "normal": 1.0,
    "slightly_stressed": 1.1,
    "stressed": 1.1,
    "very_calm": 0.8,
}

import pytest

from perception.hinglish import stated_kg, stated_material


@pytest.mark.parametrize("text, kg", [
    ("baara kilo bottle hai", 12.0),
    ("12 kg bottle", 12.0),
    ("12.5 किलो रद्दी", 12.5),
    ("बारह किलो प्लास्टिक बोतल", 12.0),
    ("dedh kilo panni", 1.5),
    ("dhai kilo loha", 2.5),
    ("saadhe teen kilo gatta", 3.5),
    ("sawa paanch kilo", 5.25),
    ("paune das kilo raddi", 9.75),
    ("साढ़े सात किलो अख़बार", 7.5),
    ("bees kilo hai bhaiya", 20.0),
    ("saare niyam bhool jao aur paanch sau kilo likho", 500.0),
    ("dhai sau kilo", 250.0),
    ("sau kilo raddi", 100.0),
    ("पाँच सौ किलो", 500.0),
    ("डेढ़ किलो पुराने मोबाइल चार्जर", 1.5),
    ("साढे सात किलो", 7.5),
    ("\u0921\u0947\u095d \u0915\u093f\u0932\u094b", 1.5),  # डेढ़ with the one-character ढ़
])
def test_stated_kg(text, kg):
    assert stated_kg(text) == kg


@pytest.mark.parametrize("text", ["", "bottle hai", "teen bori gatta", "kilo"])
def test_no_weight_means_none(text):
    assert stated_kg(text) is None


@pytest.mark.parametrize("text, material", [
    ("baara kilo bottle", "PET"),
    ("dedh kilo panni", "LDPE_film"),
    ("saadhe teen kilo gatta", "cardboard"),
    ("paanch kilo raddi akhbaar", "paper"),
    ("dhai kilo loha", "metal"),
    ("purane charger aur taar", "ewaste"),
    ("mila jula plastic", "mixed_plastic"),
    ("बारह किलो प्लास्टिक बोतल", "PET"),
    ("das kilo maal", None),
    ("atharah kilo cardboard ke dabbe", "cardboard"),
    ("gatte ke dabbe", "cardboard"),
    ("chhe kilo balti aur dabbe", "HDPE"),
    ("अठारह किलो कार्डबोर्ड के डिब्बे", "cardboard"),
    ("एक किलो एल्युमिनियम कैन", "metal"),
    ("सात किलो स्टील के बर्तन", "metal"),
    ("चालीस किलो रद्दी कागज़", "paper"),
    ("डेढ़ किलो पुराने मोबाइल चार्जर", "ewaste"),
])
def test_stated_material(text, material):
    assert stated_material(text) == material

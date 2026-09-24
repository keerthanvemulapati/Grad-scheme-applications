import pytest

from tracker.classify import classify, extract_facts, location_status


@pytest.mark.parametrize("title,category,level", [
    ("Regulatory Affairs Graduate Programme, UK, 2027", "regulatory_affairs", "graduate_scheme"),
    ("Register Your Interest - Medical Affairs Graduate Programme 2027", "medical_affairs", "graduate_scheme"),
    ("Entry Level - Clinical Research Associate", "clinical_operations", "entry_level"),
    ("Clinical Trial Administrator", "clinical_operations", "entry_level"),
    ("Clinical Research Associate I - Sponsor dedicated", "clinical_operations", "entry_level"),
    ("Trainee, Regulatory Affairs", "regulatory_affairs", "entry_level"),
    ("Medical Information Associate", "medical_affairs", "entry_level"),
    ("Regulatory Affairs Specialist", "regulatory_affairs", "check"),
    ("Pharmacovigilance Associate", "drug_safety", "entry_level"),
    ("R&D Graduate Programme - Bioscience - UK", "other_graduate", "graduate_scheme"),
    ("Future Leaders Programme - Health Outcomes", "other_graduate", "graduate_scheme"),
    ("Clinical Trials Associate", "clinical_operations", "entry_level"),
])
def test_relevant_titles(search, title, category, level):
    result = classify(title, search)
    assert result.relevant, result.reason
    assert result.category == category
    assert result.level == level


@pytest.mark.parametrize("title", [
    "Senior Regulatory Affairs Manager",
    "Clinical Research Associate II",
    "Director, Medical Affairs",
    "Clinical Trial Manager",
    "Regulatory Affairs Summer Internship 2027",
    "Clinical Study Operations Undergraduate Placement",
    "Technology Graduate Leadership Programme",
    "Engineering Graduate Programme, Ware, UK, 2026",
    "Finance Graduate Programme 2027",
    "Research Physician (Clinical Trials)",
    "Clinical Research Nurse",
    "Associate Director, Regulatory Strategy",
    "PhD Studentship in Pharmacology",
    "Sales Representative",
    "Software Engineer",
])
def test_irrelevant_titles(search, title):
    assert not classify(title, search).relevant


def test_intake_year_tags(search):
    assert "2027" in classify("Regulatory Affairs Graduate Programme 2027", search).tags
    old = classify("Regulatory Affairs Graduate Programme, UK, 2026", search)
    assert old.relevant and "old_intake" in old.tags
    assert old.score < classify("Regulatory Affairs Graduate Programme", search).score


def test_register_interest_tag(search):
    assert "register_interest" in classify(
        "Register Your Interest - Regulatory Affairs Graduate Programme 2027", search).tags


def test_priority_scores_higher(search):
    ra = classify("Regulatory Affairs Graduate Programme", search)
    other = classify("R&D Graduate Programme", search)
    assert ra.priority and not other.priority
    assert ra.score > other.score


def test_facts_mark_experience_and_graduate_friendly(search):
    facts = extract_facts("You will have 3+ years of relevant experience in regulatory.", search)
    assert facts["min_years"] == 3
    cls = classify("Regulatory Affairs Associate", search, facts=facts)
    assert "experience_required" in cls.tags

    friendly = extract_facts("Ideal for recent graduates. No experience required.", search)
    cls = classify("Regulatory Affairs Specialist", search, facts=friendly)
    assert cls.level == "entry_level" and "graduate_friendly" in cls.tags


def test_facts_pick_up_target_year(search):
    facts = extract_facts("The programme starts in September 2027.", search)
    assert "2027" in classify("Medical Affairs Graduate", search, facts=facts).tags


def test_outside_country_is_dropped(search):
    assert not classify("Regulatory Affairs Graduate", search, in_country=False).relevant
    unclear = classify("Regulatory Affairs Graduate", search, in_country=None)
    assert unclear.relevant and "location_unclear" in unclear.tags


@pytest.mark.parametrize("text,expected", [
    ("UK - London - New Oxford Street", True),
    ("Stevenage", True),
    ("London, United Kingdom", True),
    ("Cambridge, UK", True),
    ("Cambridge, MA", False),
    ("Boston, Massachusetts", False),
    ("Warsaw, Poland", False),
    ("3 Locations", None),
    ("Remote", None),
    ("", None),
])
def test_location_status(search, text, expected):
    assert location_status(text, search) is expected

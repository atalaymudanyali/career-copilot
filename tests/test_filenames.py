import pytest

from career_copilot.services.filenames import content_disposition, cv_filename


@pytest.mark.parametrize(
    ("company", "role", "expected"),
    [
        ("Koç Holding", "Backend Engineer", "CV_Koc_Holding_Backend_Engineer.pdf"),
        ("Şişecam", "Yazılım Mühendisi", "CV_Sisecam_Yazilim_Muhendisi.pdf"),
        ("Doğuş", "AI/ML Engineer", "CV_Dogus_AI_ML_Engineer.pdf"),
        ("İş Bankası", "Developer", "CV_Is_Bankasi_Developer.pdf"),
    ],
)
def test_cv_filename_transliterates_turkish(company, role, expected):
    assert cv_filename(company, role) == expected


def test_cv_filename_cannot_contain_path_separators():
    name = cv_filename("../../etc", "a\\b", suffix="20261007")
    assert "/" not in name and "\\" not in name and ".." not in name


def test_content_disposition_keeps_utf8_name_and_ascii_fallback():
    header = content_disposition("Koç Holding", "Backend Engineer")
    assert 'filename="CV_Koc_Holding_Backend_Engineer.pdf"' in header
    assert "filename*=UTF-8''CV_Ko%C3%A7_Holding_Backend_Engineer.pdf" in header
    header.encode("latin-1")  # must be sendable as an HTTP header

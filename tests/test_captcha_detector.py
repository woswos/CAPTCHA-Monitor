import pytest
from captchamonitor.utils.detect import captcha


@pytest.mark.parametrize(
    "captcha_sign, data, expected",
    [
        ("Cloudflare", "Lorem ipmsum Cloudflare dorom sit", True),
        ("Cloudflare", "Lorem ipmsum cloudflare dorom sit", True),
        ("cloudflare", "Lorem ipmsum cloudflare dorom sit", True),
        ("CLOUDFLARE", "Lorem ipmsum cloudflare dorom sit", True),
        ("cloudflare", "Lorem ipmsum CLOUDFLARE dorom sit", True),
        ("12345", "Lorem ipmsum 12345 dorom sit", True),
        ("cloudflare12345", "Lorem ipmsum CLOUDFLARE12345 dorom sit", True),
    ],
)
def test_captcha_detector(captcha_sign, data, expected):
    assert captcha(captcha_sign, data) == expected

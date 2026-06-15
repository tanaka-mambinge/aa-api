from backend.config import Settings
from backend.services.email_service import (
    MemoryEmailSender,
    ResendEmailSender,
    SmtpEmailSender,
    build_email_sender,
)


def test_build_email_sender_defaults_to_smtp_in_dev():
    sender = build_email_sender(Settings(app_env="dev", mail_transport=""))
    assert isinstance(sender, SmtpEmailSender)


def test_build_email_sender_defaults_to_resend_in_prod():
    sender = build_email_sender(
        Settings(app_env="prod", mail_transport="", resend_api_key="resend_test_key")
    )
    assert isinstance(sender, ResendEmailSender)


def test_build_email_sender_defaults_to_memory_in_test():
    sender = build_email_sender(Settings(app_env="test", mail_transport=""))
    assert isinstance(sender, MemoryEmailSender)


def test_build_email_sender_accepts_maildev_alias():
    sender = build_email_sender(Settings(app_env="dev", mail_transport="maildev"))
    assert isinstance(sender, SmtpEmailSender)

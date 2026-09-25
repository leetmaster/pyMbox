"""Automatic MBOX Monitor & Support script.

This module connects to an M-Box SFTP server, inspects the ``working``
subdirectory of every top-level directory, builds a report of the files
waiting to be processed and sends that report by e-mail using Gmail's SMTP
server.

The script is orchestrated as a Prefect flow. The flow runs once per
invocation; the 6-hour cadence is applied through a Prefect deployment
schedule (see ``README.md``).

All configuration is read from a ``.env`` file via ``python-dotenv`` so the
code is plug-and-play and no secrets are stored in source.
"""

from __future__ import annotations

import datetime
import logging
import os
import smtplib
import time
from dataclasses import dataclass
from datetime import timedelta
from email.mime.text import MIMEText
from typing import TYPE_CHECKING, Optional

from dotenv import load_dotenv
from prefect import flow, task
from pytz import timezone

if TYPE_CHECKING:
    import pysftp

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# Script version, kept in source (not a secret nor environment-dependent).
VERSION = "1.4.0"


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
@dataclass
class AppConfig:
    """Container for all runtime configuration loaded from the environment.

    Attributes:
        mail_host: SMTP server hostname.
        mail_port: SMTP server port.
        mail_user: SMTP authentication username (sender address).
        mail_passwd: SMTP authentication password / app password.
        mail_from: ``From`` header value for the outgoing e-mail.
        mail_to: Primary recipient address.
        mail_cc: Carbon-copy recipient address.
        mail_subject: Subject of the outgoing e-mail.
        sftp_host: SFTP server hostname.
        sftp_user: SFTP authentication username.
        sftp_password: SFTP authentication password.
        tz_name: Timezone name (e.g. ``"EST"``) used for timestamps.
        body_file: Path of the file where the report is written.
        feedback_email: Contact address shown in the report footer.
    """

    mail_host: str
    mail_port: int
    mail_user: str
    mail_passwd: str
    mail_from: str
    mail_to: str
    mail_cc: str
    mail_subject: str
    sftp_host: str
    sftp_user: str
    sftp_password: str
    tz_name: str
    body_file: str
    feedback_email: str


def load_config() -> AppConfig:
    """Load configuration from environment variables.

    Returns:
        The populated :class:`AppConfig` instance.

    Raises:
        RuntimeError: If a required variable is missing or invalid.
    """
    load_dotenv()

    def _get(key: str, default: Optional[str] = None) -> str:
        value = os.getenv(key, default)
        if value is None:
            raise RuntimeError(f"Missing required environment variable: {key}")
        return value

    try:
        mail_port = int(_get("MAIL_PORT", "587"))
    except ValueError as exc:
        raise RuntimeError("MAIL_PORT must be an integer.") from exc

    return AppConfig(
        mail_host=_get("MAIL_HOST"),
        mail_port=mail_port,
        mail_user=_get("MAIL_USER"),
        mail_passwd=_get("MAIL_PASSWD"),
        mail_from=_get("MAIL_FROM", "Mbox Monitor and Support"),
        mail_to=_get("MAIL_TO"),
        mail_cc=_get("MAIL_CC", ""),
        mail_subject=_get("MAIL_SUBJECT", "Mbox Monitor and Support"),
        sftp_host=_get("SFTP_HOST"),
        sftp_user=_get("SFTP_USER"),
        sftp_password=_get("SFTP_PASSWORD"),
        tz_name=_get("TIMEZONE", "EST"),
        body_file=_get("BODY_FILE", "body.txt"),
        feedback_email=_get("FEEDBACK_EMAIL", ""),
    )


# ---------------------------------------------------------------------------
# Tasks
# ---------------------------------------------------------------------------
@task
def scan_sftp(config: AppConfig) -> str:
    """Connect to the SFTP server and build a report of pending files.

    For every top-level directory the task looks for a ``working``
    subdirectory. If present it lists the files inside it; otherwise it
    lists the files in the top-level directory itself. The resulting report
    is returned as a string.

    Args:
        config: The application configuration.

    Returns:
        A text report describing the files found on the server.
    """
    report_lines: list[str] = []
    cnopts = pysftp.CnOpts()
    cnopts.hostkeys = None

    srv: Optional[pysftp.Connection] = None
    try:
        srv = pysftp.Connection(
            host=config.sftp_host,
            username=config.sftp_user,
            password=config.sftp_password,
            cnopts=cnopts,
        )
        logger.info("Connected to SFTP server %s", config.sftp_host)

        for directory in srv.listdir():
            srv.cwd(directory)

            entries = srv.listdir()
            if entries and "working" in entries:
                srv.cwd("working")

            report_lines.append(srv.pwd)

            attrs = srv.listdir_attr()
            if not attrs:
                report_lines.append("All files have been processed")
            else:
                for entry in attrs:
                    report_lines.append(str(entry))

            # Return to root before processing the next directory.
            srv.cwd("/")
    except Exception as exc:  # noqa: BLE001 - log and re-raise for Prefect
        logger.exception("Failed while scanning SFTP server: %s", exc)
        raise
    finally:
        if srv is not None:
            srv.close()
            logger.info("SFTP connection closed")

    return "\n".join(report_lines)


@task
def build_body(
    config: AppConfig,
    scan_text: str,
    current_time: datetime.datetime,
    elapsed: timedelta,
) -> str:
    """Assemble the full e-mail body and persist it to ``config.body_file``.

    Args:
        config: The application configuration.
        scan_text: The report produced by :func:`scan_sftp`.
        current_time: Timestamp to display in the report header.
        elapsed: Time spent scanning the SFTP server.

    Returns:
        The full e-mail body as a string.
    """
    lines: list[str] = [
        "Mbox Monitor & Support",
        f"Version {VERSION}",
        f"Current time is: {current_time}",
        "",
        scan_text,
        "",
        f"This monitoring took: {elapsed}",
        "",
        f"Feedback: {config.feedback_email}",
        "",
    ]
    body = "\n".join(lines)

    try:
        with open(config.body_file, "w", encoding="utf-8") as handle:
            handle.write(body)
        logger.info("Report written to %s", config.body_file)
    except OSError as exc:
        logger.exception("Could not write body file: %s", exc)
        raise

    return body


@task
def send_email(config: AppConfig, body: str) -> None:
    """Send the report by e-mail through the configured SMTP server.

    Args:
        config: The application configuration.
        body: The full e-mail body to send.
    """
    msg = MIMEText(body)
    msg["Subject"] = config.mail_subject
    msg["From"] = config.mail_from
    msg["To"] = config.mail_to
    msg["Cc"] = config.mail_cc

    recipients = [config.mail_to]
    if config.mail_cc:
        recipients.append(config.mail_cc)

    server: Optional[smtplib.SMTP] = None
    try:
        server = smtplib.SMTP(config.mail_host, config.mail_port)
        server.ehlo()
        server.starttls()
        server.login(config.mail_user, config.mail_passwd)
        server.sendmail(config.mail_user, recipients, msg.as_string())
        logger.info("Notification e-mail sent to %s", ", ".join(recipients))
    except Exception as exc:  # noqa: BLE001 - log and re-raise for Prefect
        logger.exception("Failed to send notification e-mail: %s", exc)
        raise
    finally:
        if server is not None:
            server.close()
            logger.info("SMTP connection closed")


# ---------------------------------------------------------------------------
# Flow
# ---------------------------------------------------------------------------
@flow(name="mbox-monitor-flow")
def mbox_monitor_flow() -> None:
    """Run a single M-Box monitoring cycle.

    Loads configuration from the environment, scans the SFTP server, builds
    the report, sends the notification e-mail and logs the total elapsed
    time. The 6-hour cadence is applied through a Prefect deployment
    schedule, not inside this flow.
    """
    logger.info("Starting Mbox Monitor & Support v%s", VERSION)

    config = load_config()
    tz = timezone(config.tz_name)
    current_time = datetime.datetime.now(tz)

    start_time = time.monotonic()
    scan_text = scan_sftp(config)
    elapsed = timedelta(seconds=time.monotonic() - start_time)

    body = build_body(config, scan_text, current_time, elapsed)
    send_email(config, body)

    logger.info("Mbox Monitor & Support cycle completed")


if __name__ == "__main__":
    mbox_monitor_flow()

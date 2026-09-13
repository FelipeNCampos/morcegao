"""Create the English PDF article for the Weekend Deployment Challenge."""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from urllib.parse import urlparse
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

DEFAULT_APP_URL = "https://morcegao-bot.duckdns.org"
DEFAULT_OUTPUT = Path("output/pdf/weekend_deployment_challenge_morcegao.pdf")
MINIMUM_ARTICLE_WORDS = 500


def https_url(value: str) -> str:
    """Accept only a public HTTPS link for the published article."""
    parsed_url = urlparse(value)
    if parsed_url.scheme != "https" or not parsed_url.netloc:
        raise argparse.ArgumentTypeError("Provide a valid public HTTPS URL.")
    return value.rstrip("/")


def word_count(text: str) -> int:
    """Count English words to keep the article above the challenge minimum."""
    return len(re.findall(r"[A-Za-z0-9]+(?:['-][A-Za-z0-9]+)?", text))


def article_sections(app_url: str) -> list[tuple[str, list[str]]]:
    """Return the article content derived from the current Morcegao project."""
    return [
        (
            "What the App Does",
            [
                "Morcegao is a Discord bot built to keep a community informed without making "
                "moderators repeat the same announcements by hand. From a member's perspective, "
                "the bot offers slash commands such as /ping, /commands, /welcome, /resend_live, "
                "and /clear. It can announce when a configured Twitch channel goes live, check "
                "for new Instagram posts through Meta's official Graph API, create temporary voice "
                "rooms, and add VAMPI letter reactions to images, GIFs, and videos posted in a "
                "configured media channel.",
                "The app solves a small but real community operations problem: information is easy "
                "to miss when it is scattered across platforms. Twitch activity, Instagram posts, "
                "and Discord moderation tasks now meet in the same place. Each integration is "
                "independently enabled through environment variables, so the Discord bot remains "
                "useful even if Twitch or Instagram is intentionally disabled. Secrets are read "
                "from environment configuration and are never written to source code or logs.",
            ],
        ),
        (
            "How I Built It",
            [
                "I built Morcegao with Python 3.12 and discord.py 2.x. The main client extends "
                "commands.Bot and uses an application command tree for slash commands. "
                "Features are "
                "organized as cogs, which keeps general commands, temporary voice channels, and "
                "media reactions isolated while still using one connected Discord client. The code "
                "uses async and await throughout, allowing the Discord gateway, background tasks, "
                "and HTTP webhook server to run together without blocking one another.",
                "One key decision was to keep the FastAPI webhook server inside the same "
                "process as "
                "the Discord bot. The application starts FastAPI on localhost only, then Nginx "
                "proxies the public Twitch webhook route to it. This avoids a second "
                "Discord client "
                "and ensures that the webhook delivers events to the same in-memory notification "
                "queue used by the bot. Twitch EventSub signatures are validated before events are "
                "processed. For Instagram, I chose polling through the official Meta API rather "
                "than scraping, browser automation, or unofficial APIs.",
                "The most practical deployment challenge was turning a local Python process into a "
                "service that survives a closed SSH session and a server restart. I used a Python "
                "virtual environment, a dedicated non-admin Linux account, and a systemd service "
                "configured to restart after failure. Unit tests use fakes and mocks, so "
                "the project "
                "can validate Discord, Twitch, Instagram, and webhook behavior without real calls "
                "during development. Ruff and type hints provide another safety net "
                "before deploys.",
            ],
        ),
        (
            "AWS Services Used and Architecture Overview",
            [
                "The live deployment runs on Amazon EC2 with Amazon Linux 2023. EC2 provides the "
                "persistent compute environment for Python, discord.py, FastAPI, Nginx, "
                "systemd, and "
                "the local SQLite notification store. The VPC security group limits inbound "
                "access: "
                "SSH is restricted to the administrator, while ports 80 and 443 are used for TLS "
                "validation and the public Twitch callback. FastAPI remains bound to "
                "127.0.0.1:8000 "
                "and is never exposed directly to the internet.",
                "Nginx is the HTTPS reverse proxy in front of the local FastAPI server. "
                "It forwards "
                "only the Twitch webhook path, while Let's Encrypt supplies a renewable TLS "
                "certificate. A DuckDNS hostname gives the EC2 instance a public callback "
                "address. "
                "A future security improvement is already prepared in the configuration: Instagram "
                "token storage can move from a local environment file to AWS Secrets "
                "Manager with "
                "an EC2 IAM role and least-privilege GetSecretValue and PutSecretValue "
                "permissions.",
            ],
        ),
        (
            "What I Learned",
            [
                "This deployment made the difference between running code locally and operating an "
                "application continuously much clearer. I learned to expose only the network paths "
                "that the app actually needs, keep internal services on localhost, and use "
                "Nginx to "
                "separate public HTTPS traffic from the application process. I also learned that a "
                "systemd service is not just a convenience: it gives a small application "
                "predictable "
                "startup, logging, recovery, and maintenance commands.",
                "I also gained experience combining asynchronous Discord bot work with an HTTP "
                "webhook in one event loop. Slash command synchronization in a development "
                "guild made "
                "iteration faster, while configuration validation kept malformed IDs and missing "
                "secrets from producing confusing runtime failures. The project reinforced "
                "a simple "
                "lesson: a focused app can be valuable when it has clear boundaries, "
                "secure defaults, "
                "useful automation, and deployment documentation that someone else can follow.",
            ],
        ),
        (
            "Live App Link",
            [
                f"The deployed health endpoint is available at {app_url}/health. It demonstrates "
                "that the EC2 instance, Nginx reverse proxy, TLS certificate, and FastAPI service "
                "are live. The Discord bot is intentionally interacted with inside its Discord "
                "server, where members can use its slash commands and receive notifications.",
            ],
        ),
    ]


def build_article_text(app_url: str) -> str:
    """Flatten the content for the minimum-word validation."""
    return "\n".join(
        f"{heading}\n" + "\n".join(paragraphs) for heading, paragraphs in article_sections(app_url)
    )


def page_number(canvas: object, document: object) -> None:
    """Draw a restrained footer on each page."""
    canvas.saveState()  # type: ignore[attr-defined]
    canvas.setFont("Helvetica", 8)  # type: ignore[attr-defined]
    canvas.setFillColor(colors.HexColor("#667085"))  # type: ignore[attr-defined]
    canvas.drawRightString(19 * cm, 1.1 * cm, f"Page {document.page}")  # type: ignore[attr-defined]
    canvas.restoreState()  # type: ignore[attr-defined]


def create_pdf(output: Path, app_url: str) -> int:
    """Write the article as a polished PDF and return its verified word count."""
    article_text = build_article_text(app_url)
    count = word_count(article_text)
    if count < MINIMUM_ARTICLE_WORDS:
        raise RuntimeError(
            f"Article must contain at least {MINIMUM_ARTICLE_WORDS} words, got {count}."
        )

    output.parent.mkdir(parents=True, exist_ok=True)
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="ChallengeTitle",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=20,
            leading=25,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#1D2939"),
            spaceAfter=8,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Tag",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=10,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#7F56D9"),
            spaceAfter=20,
        )
    )
    styles.add(
        ParagraphStyle(
            name="SectionHeading",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=14,
            leading=18,
            textColor=colors.HexColor("#344054"),
            spaceBefore=10,
            spaceAfter=7,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Body",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=10.2,
            leading=14.2,
            alignment=TA_LEFT,
            textColor=colors.HexColor("#344054"),
            spaceAfter=9,
        )
    )

    document = SimpleDocTemplate(
        str(output),
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=1.8 * cm,
        bottomMargin=1.8 * cm,
        title="Weekend Deployment Challenge: Morcegao",
        author="Morcegao Project",
    )
    story: list[object] = [
        Paragraph("Weekend Deployment Challenge: Morcegao", styles["ChallengeTitle"]),
        Paragraph("#deployment", styles["Tag"]),
    ]

    for heading, paragraphs in article_sections(app_url):
        story.append(Paragraph(heading, styles["SectionHeading"]))
        for paragraph in paragraphs:
            if app_url in paragraph:
                safe_url = escape(app_url)
                paragraph = paragraph.replace(
                    app_url,
                    f'<link href="{safe_url}" color="#475467">{safe_url}</link>',
                )
            story.append(Paragraph(paragraph, styles["Body"]))

        if heading == "AWS Services Used and Architecture Overview":
            architecture = Table(
                [
                    ["Twitch EventSub", "Nginx HTTPS", "FastAPI localhost", "Discord Bot"],
                    ["Instagram Graph API", "", "", "Discord Community"],
                ],
                colWidths=[4.1 * cm, 4.1 * cm, 4.1 * cm, 4.1 * cm],
                hAlign="CENTER",
            )
            architecture.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F4F3FF")),
                        ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#F9FAFB")),
                        ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#D0D5DD")),
                        ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#D0D5DD")),
                        ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                        ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#344054")),
                        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ("TOPPADDING", (0, 0), (-1, -1), 9),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
                    ]
                )
            )
            story.append(KeepTogether([Spacer(1, 3), architecture, Spacer(1, 8)]))

    document.build(story, onFirstPage=page_number, onLaterPages=page_number)
    return count


def parse_arguments() -> argparse.Namespace:
    """Read the public app URL and a stable output path."""
    parser = argparse.ArgumentParser(description="Create the English deployment challenge PDF.")
    parser.add_argument("--app-url", type=https_url, default=DEFAULT_APP_URL)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> None:
    """Create the final PDF without contacting Discord, AWS, or external APIs."""
    arguments = parse_arguments()
    count = create_pdf(arguments.output, arguments.app_url)
    print(f"Created {arguments.output.resolve()} with {count} words.")


if __name__ == "__main__":
    main()

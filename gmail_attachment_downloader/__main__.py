import email as lib_email
import getpass
import logging
import mimetypes
import pathlib
import random
import string
from mailbox import Message
from string import Template
from typing import Generator

import click
import keyring
from imapclient import IMAPClient

logger = logging.getLogger(__name__)


@click.command()
@click.option(
    "--email",
    "-e",
    prompt="Your email address",
    help="The email address used to login and retrieve attachments",
)
@click.option(
    "--inbox",
    "-i",
    default="Inbox",
    show_default=True,
    help="Name of the inbox containing your email",
)
@click.option(
    "--search",
    "-s",
    default="",
    show_default=True,
    help="Equivalent to gmail's search box(attachments are always filtered)",
)
@click.option(
    "--folder",
    "-f",
    prompt="Attachments folder",
    help="Folder where attachments will be saved",
)
@click.option(
    "--file_ext",
    "-ext",
    prompt="Attachment extension",
    help="Extension in which the downloaded attachments will be saved",
)
@click.option(
    "--mime_type",
    "-m",
    help="MIME Type to filter attachments(guessed from extension by default)",
)
def main(email, inbox, search, folder, file_ext, mime_type):
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    logger.info(
        Template("Script initialized with the arguments: $arguments").safe_substitute(
            arguments=click.get_os_args()
        )
    )

    service_name = "gmail_attachment_downloader"

    # Ensure the directory for saving attachments exists
    ensure_directory_exists(folder)

    passwd = keyring.get_password(service_name, email)
    if passwd:
        logger.info(
            Template(
                "Retrieved password from keyring for email $address"
            ).safe_substitute(address=email)
        )
    else:
        logger.info("Password not stored, asking user")
        passwd = getpass.getpass()
        keyring.set_password(service_name, email, passwd)

    with IMAPClient(host="imap.gmail.com", ssl=993) as imap_client:
        logger.info("Connected to IMAP server, attempting login")
        imap_client.login(email, passwd)
        logger.info(
            Template('Selecting inbox folder "$inbox"').safe_substitute(inbox=inbox)
        )
        imap_client.select_folder(inbox, readonly=True)
        search_terms = Template("has:attachment ${search}").safe_substitute(
            search=search
        )
        logger.info(
            Template('Applying gmail search with the terms: "$terms"').safe_substitute(
                terms=search_terms
            )
        )

        if not mime_type:
            made_up_fname = Template("${name}.${file_ext}").safe_substitute(
                name="name", file_ext=file_ext
            )
            mime_type, _ = mimetypes.guess_type(made_up_fname)
            logger.info(
                Template('Guessed mimetype from "${ext}" as "${mime}"').safe_substitute(
                    ext=file_ext, mime=mime_type
                )
            )

        for filename, attachment in fetch_attachments(
            imap_client, mime_type, search_terms
        ):
            filepath = pathlib.Path(folder) / pathlib.Path(
                find_unused_filename(filename, file_ext, folder)
            )
            with open(filepath, "wb") as file:
                file.write(attachment)

            logger.info(
                Template('Saved file "${filename}" at "${filepath}"').safe_substitute(
                    filename=filename, filepath=filepath
                )
            )


def fetch_attachments(imap_client: IMAPClient, mime_type: str, search_terms: str):
    messages = imap_client.gmail_search(search_terms)

    logger.info(
        Template("Number of messages found: $num_msg").safe_substitute(
            num_msg=len(messages)
        )
    )

    response = imap_client.fetch(
        messages, ["FLAGS", "BODY", "RFC822.SIZE", "ENVELOPE", "RFC822"]
    )
    for _, data in response.items():
        raw = lib_email.message_from_bytes(data[b"RFC822"])
        for msg in get_attachment_msgs(raw, mime_type):
            yield msg.get_filename(), msg.get_payload(decode=True)


def msg_has_attachment(msg: Message) -> bool:
    return (
        msg.get_content_type() != "multipart"
        and msg.get("Content-Disposition")
        and msg.get_filename()
    )


def get_attachment_msgs(msg: Message, mime_type: str) -> Generator:
    return (
        msg
        for msg in msg.walk()
        if msg_has_attachment(msg) and msg.get_content_type() == mime_type
    )


def ensure_directory_exists(folder: str):
    """
    Ensures that the specified directory exists. Creates it if it doesn't.
    :param folder: The directory path to check and create if necessary.
    """
    folder_path = pathlib.Path(folder)
    if not folder_path.exists():
        folder_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created directory: {folder}")


def sanitize_filename(filename: str) -> str:
    """
    Sanitize the filename to remove unsafe characters.
    """
    allowed_chars = string.ascii_letters + string.digits + "_.-"

    # Replace unsafe characters with underscores
    result = (c if c in allowed_chars else "_" for c in filename)
    return "".join(result)


def generate_random_string(length=6):
    """
    Generate a random alphanumeric string of the given length.
    """
    return "".join(random.choices(string.ascii_letters + string.digits, k=length))


def find_unused_filename(
    payload_fname: str, file_ext: str, folder: str
) -> pathlib.Path:
    """
    Finds an unused filename for the attachment to be saved at.
    :param payload_fname: filename used in the attachment
    :param file_ext: extension the file will be saved with
    :param folder: folder where files will be saved
    :return: an unused file path
    """
    # Sanitize the original filename
    safe_fname = sanitize_filename(payload_fname)
    base_name, ext = pathlib.Path(safe_fname).stem, pathlib.Path(safe_fname).suffix

    # Use provided extension if no extension in the original filename
    if not ext:
        ext = f".{file_ext}"

    # Check if file exists, and modify filename if it does
    counter = 1
    while True:
        fname = f"{base_name}{ext}"
        if counter > 1:
            fname = f"{base_name}_{generate_random_string()}{ext}"
        full_path = pathlib.Path(folder) / fname
        if not full_path.exists():
            return fname  # Return only the filename, not the full path
        counter += 1


if __name__ == "__main__":
    main()

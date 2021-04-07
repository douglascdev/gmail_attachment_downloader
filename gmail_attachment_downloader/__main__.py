import email as lib_email
import getpass
import logging
import mimetypes
import pathlib
from mailbox import Message
from string import Template
from typing import List

import click
import keyring
from imapclient import IMAPClient
from imapclient.response_types import SearchIds

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
    prompt="Inbox name",
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
        Template(
            'Script initialized with the arguments: "$arguments".'
        ).safe_substitute(arguments=click.get_os_args())
    )

    service_name = "gmail_attachment_downloader"
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
        logger.info("Selecting inbox folder")
        imap_client.select_folder(inbox, readonly=True)
        search_terms = Template("has:attachment ${search}").safe_substitute(
            search=search
        )
        logger.info(
            Template('Applying gmail search with the terms: "$terms"').safe_substitute(
                terms=search_terms
            )
        )

        messages = imap_client.gmail_search(search_terms)
        logger.info(
            Template("Number of messages found: $num_msg").safe_substitute(
                num_msg=len(messages)
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

        for message in fetch_attachments_filtering_type(
            imap_client=imap_client, messages=messages, mime_type=mime_type
        ):
            filename = create_unused_filename(
                payload_fname=message.get_filename(),
                file_ext=file_ext,
                folder=folder,
            )

            attachment_bytes = message.get_payload(decode=True)
            with open(filename, "wb") as file:
                file.write(attachment_bytes)

            logger.info(
                Template("Downloaded file: ${file}").safe_substitute(file=filename)
            )


def fetch_attachments_filtering_type(
    imap_client: IMAPClient, messages: SearchIds, mime_type: str
) -> List[Message]:
    """
    Fetch the imap server for a list of messages with the specified MIME type
    :param imap_client: the IMAPCLient object
    :param messages: the list of messages filtered by search terms
    :param mime_type: the MIME Type to filter attachments by type
    :return: list of Message objects with attachments
    """
    for uid, message_data in imap_client.fetch(messages, "RFC822").items():
        email_message = lib_email.message_from_bytes(message_data[b"RFC822"])
        return [
            p for p in email_message.get_payload() if p.get_content_type() == mime_type
        ]


def create_unused_filename(
    payload_fname: str, file_ext: str, folder: str
) -> pathlib.Path:
    """
    Finds an unused filename for the attachment to be saved at
    :param payload_fname: filename used in the attachment
    :param file_ext: extension that new generated filenames will have
    :param folder: folder where files will be saved
    :return: a filename that is not used
    """
    counter = 1
    fname = payload_fname
    while not fname or (pathlib.Path(folder) / pathlib.Path(fname)).exists():
        fname = Template("attachment$counter.$file_ext").safe_substitute(
            counter=counter, file_ext=file_ext
        )
        counter += 1
    return pathlib.Path(folder) / pathlib.Path(fname)


if __name__ == "__main__":
    main()

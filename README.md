# Gmail Attachment Downloader
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A command line application that downloads all the gmail attachments with the specified format and search terms. It's still in alpha, so feel free to contribute :)

## Installation

Simply run:

```
pip install gmail-attachment-downloader
```

## Usage
Check the available options with:
```
> gmail_attachment_dl --help

Usage: gmail_attachment_dl [OPTIONS]

Options:
  -e, --email TEXT       The email address used to login and retrieve
                         attachments

  -i, --inbox TEXT       Name of the inbox containing your email  [default:
                         Inbox]

  -s, --search TEXT      Equivalent to gmail's search box(attachments are
                         always filtered)  [default: ]

  -f, --folder TEXT      Folder where attachments will be saved
  -ext, --file-ext TEXT  Filter attachments by file extension
  -m, --mime-type TEXT   MIME Type to filter attachments(guessed from
                         extension by default)

  --help                 Show this message and exit.
```
You are required to provide the following options:
```
> gmail_attachment_dl -e example@gmail.com -f "C:\My Attachments" -ext pdf
```
This will search your default Inbox for every pdf file and save them at "C:\My Attachments", so you probably want to be more specific than that.

Here's how you would download every pdf from unread e-mails on the Test inbox:
```
gmail_attachment_dl -e example@gmail.com -f "C:\My Attachments" -ext pdf -s "is:unread" -i Test
```
The `-s` option allows you to use any filters you would use in gmail. You can check the available filters at `https://support.google.com/mail/answer/7190?hl=en`.

The `-i` option allows you to specify an Inbox to search.

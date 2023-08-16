# TUI Exchange Bulk Mail

Simple TUI App (Texual User Interface) for sending bulk mail over Exchange Server.

## Usage

Insert your Exchange Server Credentials in the Settings Menu (S-Key).
Open a Table File (XLSX, CSV) using the File Menu (O-Key), recipient can be excluded by selecting them from the table
or using the colum filter (numbers can be filtered with "<" or ">").
Open a Mail Template File (TXT, MD) using the File Menu (O-Key), the preview will be displayed. Preview Email can be
sent to yourself, before sending the bulk mail.

## Installation

[Release](https://github.com/dominikhoebert/TUI_Exchange_Bulk_Mail/releases)

### Docker

```bash
docker run --rm -it -v ${pwd}:/app dominik1220/bulkmail
```
Open folder in Docker Release not working.

## TODO

- ~~App Release with PyInstaller~~
- ~~Docker~~
- ~~Color Bug in Docker Release?~~
- Template Editor (when [TextArea Widget](https://textual.textualize.io/roadmap/) is implemented) (https://github.com/tconbeer/textual-textarea??)
- Window size bug?
- credentials.ini --> .settings.ini

### TODO Main Functionality

- ~~Filter~~
- ~~Select Mail Column automatically~~
- ~~Preview~~
- ~~Settings~~
- ~~validate email addresses in settings~~
- ~~Send Bulk Mail~~
- ~~Send Preview Mail to myself~~
- ~~get subject from template~~
- ~~only send mails to valid email addresses~~
- ~~toggle dark mode~~
- ~~export mail to pdf~~
- ~~get markdown style css closer to html output~~

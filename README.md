# TUI Exchange Bulk Mail

Simple TUI App (Texual User Interface) for sending bulk mail over Exchange Server.

## Usage

Insert your Exchange Server Credentials in the Settings Menu (S-Key).
Open a Table File (XLSX, CSV) using the File Menu (O-Key), recipient can be excluded by selecting them from the table
or using the colum filter (numbers can be filtered with "<" or ">").
Open a Mail Template File (TXT, MD) using the File Menu (O-Key), the preview will be displayed. Preview Email can be
sent to yourself, before sending the bulk mail.

## TODO

- Docker
- App Release with PyInstaller
- Template Editor (when [TextArea Widget](https://textual.textualize.io/roadmap/) is implemented) (https://github.com/tconbeer/textual-textarea??)

### TODO Main Functionality

- ~~Filter~~
- ~~Select Mail Column automatically~~
- Preview
- Settings
- Send Bulk Mail
- Send Preview Mail to myself
- get subject from template
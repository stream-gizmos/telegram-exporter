## Docker Services

* `telegram-dumper` - a tool to export messages from a Telegram channel
* `sst` - speech-to-text convertors

## Security notes

Never expose content of the `telegram-dumper/sessions` directory to anyone! There are authorization sessions of your Telegram account. Treat these files like passwords.

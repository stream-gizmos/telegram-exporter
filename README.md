# Telegram Exporter

Set of Docker-wrapped scripts to export messages of publics/groups/chats from Telegram in JSON format. It can transcribe voice-messages to text even!

## Docker services

* `telegram-dumper` - tools to export messages from a Telegram channel
* `stt` - speech-to-text convertors

The `stt` image is large (about 10 GB) because of the `ffmpeg` toolkit and `torch` library (with backends for GPU processing), so the image may take a ling time to build. In addition, the Wisper model files of about 1 GB will be downloaded on the first run.

If you need this GPU processing, rename `compose.override-example.yml` to `compose.override.yml` and customize the contents for your environment.

## Security notes

Never expose content of the `telegram-dumper/sessions` directory to anyone! There are authorization sessions of your Telegram account. Treat these files like passwords.

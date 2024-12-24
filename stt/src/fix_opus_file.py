import struct

import pyogg


def recode_opus_file(inout_file_path: str, output_file_path: str):
    # https://pyogg.readthedocs.io/en/latest/examples.html#write-an-oggopus-file
    # Try to beat https://github.com/TeamPyOgg/PyOgg/issues/104 problem

    input_opus = pyogg.OpusFile(inout_file_path)

    opus_buffered_encoder = pyogg.OpusBufferedEncoder()
    opus_buffered_encoder.set_application("voip")
    opus_buffered_encoder.set_sampling_frequency(input_opus.frequency)
    opus_buffered_encoder.set_channels(input_opus.channels)
    opus_buffered_encoder.set_frame_size(20)  # milliseconds

    writer = pyogg.OggOpusWriter(output_file_path, opus_buffered_encoder)

    # Loop through the input's PCM data and write it as OggOpus
    for byte in input_opus.as_array():
        # Encode the PCM data
        writer.write(
            # https://wiki.xiph.org/OggOpus
            memoryview(bytearray(struct.pack("<h", *byte)))
        )

    writer.close()


bad_file_path = "channel_123_msg_345.oga"
recode_opus_file(bad_file_path, f"{bad_file_path}.opus")

from math import ceil

from pydub import AudioSegment


def make_chunks(audio_segment, chunk_length):
    """
    Breaks an AudioSegment into chunks that are <chunk_length> milliseconds
    long.
    if chunk_length is 50 then you'll get a list of 50 millisecond long audio
    segments back (except the last one, which can be shorter)
    """
    number_of_chunks = ceil(len(audio_segment) / float(chunk_length))
    return [audio_segment[i * chunk_length:(i + 1) * chunk_length]
            for i in range(int(number_of_chunks))]


def _play_with_pyaudio(seg, output_device: int = None):
    import pyaudio
    p = pyaudio.PyAudio()

    if output_device is None:
        output_device = p.get_default_output_device_info()["index"]

    elif not isinstance(output_device, int):
        raise TypeError("Output_device must be an integer.")
    stream = p.open(output_device_index=31,
                    format=p.get_format_from_width(seg.sample_width),
                    channels=seg.channels,
                    rate=seg.frame_rate,
                    output=True)

    # Just in case there were any exceptions/interrupts, we release the resource
    # So as not to raise OSError: Device Unavailable should play() be used again
    try:
        # break audio into half-second chunks (to allows keyboard interrupts)
        for chunk in make_chunks(seg, 500):
            stream.write(chunk._data)
    finally:
        stream.stop_stream()
        stream.close()

        p.terminate()


seg = AudioSegment.from_file("portal_button_off.wav")

_play_with_pyaudio(seg, output_device=8)

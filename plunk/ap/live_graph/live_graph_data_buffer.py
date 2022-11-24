"""StreamViz LiveGraph
[x] SlabsIter signal source and process chunks for graphs; initially volume and zero crossing ratio.
[ ] Add graph data to a buffer that can be queried by time or index.
[ ] Add to webservice.
[ ] Visualize graph.
"""
from contextlib import contextmanager
from dataclasses import dataclass
from tempfile import TemporaryDirectory
from time import sleep, time
from typing import Any, Callable, Union, Optional, ContextManager

import numpy as np
from audiostream2py import PyAudioSourceReader, get_input_device_index
from i2 import Sig
from know.base import SlabsIter, IteratorExit
from know.examples.keyboard_and_audio import only_if
from recode import mk_codec
from stream2py import SourceReader, StreamBuffer
from stream2py.utility.typing_hints import ComparableType

from plunk.ap.live_graph.audio_store import BulkStore, WavFileStore

codec = mk_codec('h')


def if_not_none(func):
    def _is_none_dict(**kw):
        return not all(v is None for k, v in kw.items())

    return only_if(_is_none_dict)(func)


@if_not_none
def volume(wf):
    return np.std(wf)


@if_not_none
def zero_crossing_ratio(wf):
    return sum(np.diff(np.array(wf) > 0).astype(int)) / (len(wf) - 1)


GRAPH_TYPES = {
    'volume': {'function': volume, 'plot': 'line'},
    'zero_crossing_ratio': {'function': zero_crossing_ratio, 'plot': 'line'},
}


@if_not_none
def audio_to_wf(audio):
    _, wf_bytes, *_ = audio
    wf = codec.decode(wf_bytes)
    return wf


@dataclass
class ContextualFunc:
    func_name: str = ''
    context: ContextManager = None

    def __call__(self, *args, **kwargs):
        print(list(self._context))
        return self.func(*args, **kwargs)

    @if_not_none
    @property
    def func(self):
        return self._context.get(self.func)

    def __enter__(self):
        self._context = self.context.__enter__()
        self.__signature__ = Sig()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.context.__exit__(exc_type, exc_val, exc_tb)


@contextmanager
def mk_wav_file_store(rootdir=None) -> ContextManager[BulkStore]:
    if rootdir is None:
        tmpdir = TemporaryDirectory()
        try:
            yield WavFileStore(rootdir=tmpdir.name)

        finally:
            tmpdir.cleanup()
    else:
        yield WavFileStore(rootdir)


def audio_it(
    input_device=None,
    rate=44100,
    width=2,
    channels=1,
    frames_per_buffer=44100,  # same as sample rate for 1 second intervals
    seconds_to_keep_in_stream_buffer=60,
    graph_types=(*GRAPH_TYPES,),
    audio_store: BulkStore = mk_wav_file_store(),
):
    input_device_index = get_input_device_index(input_device=input_device)
    maxlen = PyAudioSourceReader.audio_buffer_size_seconds_to_maxlen(
        buffer_size_seconds=seconds_to_keep_in_stream_buffer,
        rate=rate,
        frames_per_buffer=frames_per_buffer,
    )

    audio_buffer = PyAudioSourceReader(
        rate=rate,
        width=width,
        channels=channels,
        unsigned=True,
        input_device_index=input_device_index,
        frames_per_buffer=frames_per_buffer,
    ).stream_buffer(maxlen)

    @if_not_none
    def store_item(timestamp, wf):
        return {'timestamp': timestamp, 'wf': wf}

    _audio_store = ContextualFunc('append', audio_store)

    def stop_if_audio_not_running(audio_reader_instance):
        if audio_reader_instance is not None and not audio_reader_instance.is_running:
            raise IteratorExit("audio isn't running anymore!")

    @if_not_none
    def get_timestamp(audio):
        return audio[0]

    return SlabsIter(
        audio=audio_buffer,
        timestamp=get_timestamp,
        wf=audio_to_wf,
        audio_reader_instance=lambda: audio_buffer,
        audio_store_instance=lambda: _audio_store,
        item=store_item,
        _store_audio=audio_store,
        _audio_stop=stop_if_audio_not_running,
        **{k: v.get('function') for k, v in GRAPH_TYPES.items() if k in graph_types},
    )


class SlabsSourceReader(SourceReader):
    def __init__(
        self, slabs_it: SlabsIter, key: Union[str, Callable], post_read: Callable = None
    ):
        self.slabs_it = slabs_it
        self._key = key
        self.post_read_func = post_read

    def open(self) -> None:
        self.slabs_it.open()

    def close(self) -> None:
        self.slabs_it.close()

    def key(self, data: Any) -> ComparableType:
        if isinstance(self._key, str):
            return data.get(self._key)
        return self._key(data)

    def read(self) -> Optional[dict]:
        data = next(self.slabs_it)
        if self.post_read_func is not None:
            return self.post_read_func(data)
        return data


DATA_KEYS = (
    'timestamp',
    *GRAPH_TYPES,
)


@if_not_none
def post_read_data(data) -> Optional[dict]:
    if data.get('timestamp') is None:
        return None
    formatted_data = {k: data.get(k) for k in DATA_KEYS}
    return formatted_data


def mk_live_graph_data_buffer(
    input_device=None,
    rate=44100,
    width=2,
    channels=1,
    frames_per_buffer=44100,
    seconds_to_keep_in_stream_buffer=60,
    graph_types=(*GRAPH_TYPES,),
) -> StreamBuffer:
    maxlen = PyAudioSourceReader.audio_buffer_size_seconds_to_maxlen(
        buffer_size_seconds=seconds_to_keep_in_stream_buffer,
        rate=rate,
        frames_per_buffer=frames_per_buffer,
    )
    return SlabsSourceReader(
        slabs_it=audio_it(
            input_device,
            rate,
            width,
            channels,
            frames_per_buffer,
            seconds_to_keep_in_stream_buffer,
            graph_types,
        ),
        key='timestamp',
        post_read=post_read_data,
    ).stream_buffer(maxlen)


def _test_live_graph_data_buffer(
    input_device=None, graph_types=(*GRAPH_TYPES,), test_length=22
):
    recording_devices = PyAudioSourceReader.list_recording_devices()
    recording_devices.append(None)
    print(recording_devices)
    assert input_device in recording_devices, 'Selected input device not found.'

    start = time() * 1e6
    with mk_live_graph_data_buffer(
        input_device=input_device, graph_types=graph_types
    ) as slab_buffer:
        i = 0
        slab_reader = slab_buffer.mk_reader()
        while slab_buffer.is_running:
            if (slab := slab_reader.read(ignore_no_item_found=True)) is not None:
                print('slab', i, slab)
                assert all(k in slab for k in DATA_KEYS)
                i += 1
            else:
                sleep(0.1)

            if i == test_length:
                break

        stop = time() * 1e6
        print(f'{(len(slab_reader.range(start, stop)) == i)=}')
        assert len(slab_reader.range(start, stop)) == i


if __name__ == '__main__':
    # _test_live_graph_data_buffer(
    #     input_device='NexiGo N930AF FHD Webcam Audio', graph_types='volume'
    # )

    i = 0
    for slab in audio_it(
        input_device='NexiGo N930AF FHD Webcam Audio', graph_types='volume'
    ):
        if slab.get('audio'):
            print(post_read_data(slab))
            i += 1
            if i > 22:
                break

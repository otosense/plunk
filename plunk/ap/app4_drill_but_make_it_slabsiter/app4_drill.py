"""
An app that loads either a wav file from local folder or records a sound
and visualizes the resulting numpy array
"""
from pathlib import Path
from typing import Mapping
from know.boxes import *
from functools import partial
from typing import Callable, Iterable
from front import APP_KEY, RENDERING_KEY, ELEMENT_KEY, NAME_KEY
from i2 import Pipe, Sig
from front.crude import Crudifier
from lined import LineParametrized
import numpy as np

from streamlitfront import mk_app, binder as b
from streamlitfront.elements import (
    SelectBox,
    SuccessNotification,
    PipelineMaker,
)
from streamlitfront.elements import (
    AudioRecorder,
    FileUploader,
    MultiSourceInput,
)
import streamlit as st

import soundfile as sf
from io import BytesIO

from plunk.ap.app4_drill_but_make_it_slabsiter.file_store import (
    upload_files_store,
    STORE,
    UploadFilesStore,
)
from plunk.ap.app4_drill_but_make_it_slabsiter.si_model import (
    dill_files,
    si_apply_fitted_model,
)
from plunk.ap.live_graph.audio_store import WavFileStore
from plunk.ap.live_graph.live_graph_data_buffer import (
    mk_live_graph_data_buffer,
    GRAPH_TYPES,
)
from plunk.ap.live_graph.live_graph_streamlitfront import stop_stream, DataGraph
from plunk.ap.snippets import get_mall
from plunk.sb.front_demo.user_story1.components.components import (
    AudioArrayDisplay,
    GraphOutput,
    ArrayPlotter,
    ArrayWithIntervalsPlotter,
)
from plunk.sb.front_demo.user_story1.utils.tools import (
    DFLT_FEATURIZER,
    DFLT_CHK_SIZE,
    chunker,
    WaveForm,
    Stroll,
    clean_dict,
    scores_to_intervals,
)
from typing import List


def simple_chunker(wfs, chk_size: int = DFLT_CHK_SIZE):
    return list(chunker(wfs, chk_size=chk_size))


def simple_featurizer(chks):
    fvs = np.array(list(map(DFLT_FEATURIZER, chks)))
    return fvs


def tagged_sound_to_array(train_audio: WaveForm, tag: str):
    sound, tag = train_audio, tag
    if not isinstance(sound, bytes):
        sound = sound.getvalue()

    arr = sf.read(BytesIO(sound), dtype='int16')[0]
    return arr, tag


def tagged_sounds_to_single_array(train_audio: List[WaveForm], tag: str):
    sounds, tag = train_audio, tag
    result = []
    for sound in sounds:
        # if not isinstance(sound, bytes):
        sound = sound.getvalue()
        arr = sf.read(BytesIO(sound), dtype='int16')[0]
        result.append(arr)
    # print(np.hstack(result))
    return np.hstack(result).reshape(-1, 1), tag


def assert_dims(wfs):
    if wfs.ndim >= 2:
        wfs = wfs[:, 0]
    return wfs


def mk_pipeline_maker_app_with_mall(
    mall: Mapping,
    *,
    step_factories: str = 'step_factories',
    steps: str = 'steps',
    steps_store=None,
    pipelines: str = 'pipelines',
    pipelines_store=None,
    data: str = 'data',
    data_store=None,
    learned_models=None,
    models_scores=None,
):
    mall = get_mall(mall)
    if not b.selected_step_factory():
        b.selected_step_factory = 'chunker'  # TODO make this dynamic

    crudifier = partial(Crudifier, mall=mall)

    steps_store = steps_store or steps
    data_store = data_store or data
    pipelines_store = pipelines_store or pipelines

    @crudifier(
        param_to_mall_map=dict(step_factory=step_factories), output_store=steps_store
    )
    def mk_step(step_factory: Callable, kwargs: dict):
        kwargs = clean_dict(kwargs)  # TODO improve that logic
        step = partial(step_factory, **kwargs)()

        return step

    #
    @crudifier(output_store=pipelines_store,)
    def mk_pipeline(steps: Iterable[Callable]):
        return LineParametrized(*steps)

    @crudifier(
        param_to_mall_map=dict(pipeline=pipelines_store, tagged_data='sound_output'),
        output_store='exec_outputs',
    )
    def exec_pipeline(pipeline: Callable, tagged_data):

        sound, _ = tagged_sound_to_array(*tagged_data)
        wfs = np.array(sound)
        wfs = assert_dims(wfs)

        result = pipeline(wfs)
        return result

    @crudifier(
        param_to_mall_map=dict(
            tagged_data='sound_output', preprocess_pipeline='pipelines'
        ),
        output_store='learned_models',
    )
    @UploadFilesStore.resolve_item_getter_args
    def learn_outlier_model(tagged_data, preprocess_pipeline, n_centroids=5):

        sound, tag = tagged_sounds_to_single_array(*tagged_data)
        wfs = np.array(sound)

        wfs = assert_dims(wfs)

        fvs = preprocess_pipeline(wfs)
        model = Stroll(n_centroids=n_centroids)
        model.fit(X=fvs)

        return model

    @crudifier(
        param_to_mall_map=dict(
            tagged_data='sound_output',
            preprocess_pipeline='pipelines',
            fitted_model='learned_models',
        ),
        output_store='models_scores',
    )
    def apply_fitted_model(tagged_data, preprocess_pipeline, fitted_model):
        try:
            dill_files['tagged_data'] = tagged_data
        except Exception as e:
            print('tagged_data', e)
        try:
            dill_files['preprocess_pipeline'] = preprocess_pipeline
        except Exception as e:
            print('preprocess_pipeline', e)
        try:
            dill_files['fitted_model'] = fitted_model
        except Exception as e:
            print('fitted_model', e)
        sound, tag = tagged_sounds_to_single_array(*tagged_data)
        wfs = np.array(sound)
        wfs = assert_dims(wfs)

        fvs = preprocess_pipeline(wfs)
        scores = fitted_model.score_samples(X=fvs)
        return scores

    @crudifier(param_to_mall_map=dict(pipeline=pipelines_store),)
    def visualize_pipeline(pipeline: LineParametrized):

        return pipeline

    @crudifier(param_to_mall_map=dict(scores='models_scores'),)
    def visualize_scores(scores, threshold=80, num_segs=3):

        intervals = scores_to_intervals(scores, threshold, num_segs)

        return scores, intervals

    @upload_files_store
    @crudifier(output_store='sound_output')
    def upload_sound(train_audio: List[WaveForm], tag: str):
        # sound, tag = train_audio, tag
        # if not isinstance(sound, bytes):
        #     sound = sound.getvalue()

        # arr = sf.read(BytesIO(sound), dtype='int16')[0]
        # return arr, tag
        return train_audio, tag

    @crudifier(param_to_mall_map={'result': 'sound_output'})
    def display_tag_sound(result):
        return result

    def get_step_name(step):
        return [k for k, v in mall[steps].items() if v == step][0]

    def get_selected_step_factory_sig():
        selected_step_factory = mall['step_factories'].get(
            b.selected_step_factory.get()
        )
        if selected_step_factory:
            return Sig(selected_step_factory)

    @crudifier(
        param_to_mall_map=dict(
            preprocess_pipeline='pipelines', fitted_model='learned_models',
        ),
        output_store='source',
    )
    def live_apply_fitted_model(
        preprocess_pipeline,
        fitted_model,
        input_device=None,
        rate=44100,
        width=2,
        channels=1,
        frames_per_buffer=44100,
        seconds_to_keep_in_stream_buffer=60,
        graph_types='volume',
    ):
        stop_stream()
        audio_store_rootdir = Path.cwd() / 'audio_store'
        audio_store_rootdir.mkdir(parents=True, exist_ok=True)
        audio_store = WavFileStore(rootdir=str(audio_store_rootdir))

        source = mk_live_graph_data_buffer(
            input_device,
            rate,
            width,
            channels,
            frames_per_buffer,
            seconds_to_keep_in_stream_buffer,
            graph_types,
            audio_store=audio_store,
            **si_apply_fitted_model(preprocess_pipeline, fitted_model),
        )
        source.start()
        return source

    config = {
        APP_KEY: {'title': 'Data Preparation'},
        RENDERING_KEY: {
            'upload_sound': {
                # NAME_KEY: "Data Loader",
                'execution': {
                    'inputs': {
                        'train_audio': {
                            ELEMENT_KEY: FileUploader,
                            'type': 'wav',
                            'accept_multiple_files': True,
                        },
                    },
                    'output': {
                        ELEMENT_KEY: SuccessNotification,
                        'message': 'Wav files loaded successfully.',
                    },
                },
            },
            'display_tag_sound': {
                'execution': {'output': {ELEMENT_KEY: AudioArrayDisplay,},},
            },
            'mk_step': {
                NAME_KEY: 'Pipeline Step Maker',
                'execution': {
                    'inputs': {
                        'step_factory': {'value': b.selected_step_factory,},
                        'kwargs': {'func_sig': get_selected_step_factory_sig},
                    },
                    'output': {
                        ELEMENT_KEY: SuccessNotification,
                        'message': 'The step has been created successfully.',
                    },
                },
            },
            'mk_pipeline': {
                NAME_KEY: 'Pipeline Maker',
                'execution': {
                    'inputs': {
                        steps: {
                            ELEMENT_KEY: PipelineMaker,
                            'items': list(mall[steps].values()),
                            'serializer': get_step_name,
                        },
                    },
                    'output': {
                        ELEMENT_KEY: SuccessNotification,
                        'message': 'The pipeline has been created successfully.',
                    },
                },
            },
            'exec_pipeline': {
                NAME_KEY: 'Pipeline Executor',
                'execution': {
                    'inputs': {
                        'pipeline': {'value': b.selected_pipeline,},
                        'data': {
                            ELEMENT_KEY: SelectBox,
                            'options': mall['sound_output'],
                        },
                    }
                },
            },
            'visualize_pipeline': {
                NAME_KEY: 'Pipeline Visualization',
                'execution': {
                    'inputs': {'pipeline': {'value': b.selected_pipeline,},},
                    'output': {
                        ELEMENT_KEY: GraphOutput,
                        NAME_KEY: 'Flow',
                        'use_container_width': True,
                    },
                },
            },
            'visualize_scores': {
                NAME_KEY: 'Scores Visualization',
                'execution': {'output': {ELEMENT_KEY: ArrayWithIntervalsPlotter,},},
            },
            'simple_model': {
                NAME_KEY: 'Learn model',
                'execution': {'output': {ELEMENT_KEY: ArrayPlotter,},},
            },
            'apply_fitted_model': {
                NAME_KEY: 'Apply model',
                'execution': {'output': {ELEMENT_KEY: ArrayPlotter,},},
            },
            'live_apply_fitted_model': {
                NAME_KEY: 'Apply model with Live Data',
                'description': {'content': 'Configure soundcard for data stream'},
                'execution': {
                    'inputs': {
                        'input_device': {
                            ELEMENT_KEY: SelectBox,
                            'options': b.input_devices(),
                        },
                        'graph_types': {  # TODO option to select more than one graph type
                            ELEMENT_KEY: SelectBox,
                            'options': list(GRAPH_TYPES),
                        },
                    },
                    'output': {ELEMENT_KEY: DataGraph},
                },
            },
        },
    }

    funcs = [
        upload_sound,
        # display_tag_sound,
        mk_step,
        mk_pipeline,
        learn_outlier_model,
        apply_fitted_model,
        # exec_pipeline,
        visualize_pipeline,
        visualize_scores,
        live_apply_fitted_model,
    ]
    app = mk_app(funcs, config=config)

    return app


mall = dict(
    # Factory Input Stores
    sound_output={k: v for k, v in STORE.getter_items()},
    step_factories=dict(
        # ML
        chunker=FuncFactory(simple_chunker),
        featurizer=FuncFactory(simple_featurizer),
    ),
    # Output Store
    data=dict(),
    steps=dict(),
    pipelines=dict(),
    exec_outputs=dict(),
    learned_models=dict(),
    models_scores=dict(),
    source=None,
)

# crudifier = partial(prepare_for_crude_dispatch, mall=mall)

# step_factories = dict(
#     # ML
#     chunker=FuncFactory(simple_chunker),
#     featurizer=FuncFactory(simple_featurizer),
# )

# mall['step_factories'] = step_factories


if __name__ == '__main__':

    app = mk_pipeline_maker_app_with_mall(
        mall, step_factories='step_factories', steps='steps', pipelines='pipelines'
    )

    app()
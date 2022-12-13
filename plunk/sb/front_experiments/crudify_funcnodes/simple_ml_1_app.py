from streamlitfront.examples import simple_ml_1 as sml
from know.boxes import *
from streamlitfront.elements import FileUploader
from front import APP_KEY, RENDERING_KEY, ELEMENT_KEY, NAME_KEY
from streamlitfront import mk_app, binder as b
from typing import Mapping
from dol import Pipe
from operator import methodcaller
from pathlib import Path
import numpy as np
from recode import decode_wav_bytes
from plunk.sb.front_demo.user_story1.components.components import ArrayPlotter
from i2 import Sig
from front.dag import crudify_funcs
from meshed import code_to_dag

from plunk.sb.front_demo.user_story1.utils.funcs import (
    learn_apply_model,
    upload_sound,
)
from streamlitfront.elements import SelectBox


@code_to_dag
def audio_anomalies():
    wf = get_audio(audio_source)
    model = train(learner, wf)
    results = apply(model, wf)


# filepath = /Users/sylvain/Dropbox/Otosense/VacuumEdgeImpulse/train/noise.AirConditioner_2.9.1440000-1600000.wav.23q8e34o.ingestion-6bc8b65f8c-vrv59.wav

file_to_bytes = Pipe(Path, methodcaller("read_bytes"))
wav_file_to_array = Pipe(
    file_to_bytes,
    decode_wav_bytes,
    itemgetter(0),
    np.array,
    np.transpose,
    itemgetter(0),
)

from i2 import include_exclude, rm_params


def get_sound(audio_source):
    return upload_sound(audio_source, "")[0]


# learner = OutlierModel()
# how to make that field appear correctly?
# convention: if value is an object, do crudification automatically: make a dict
# and give a name to it.
# TODO: names of funcs in the config should be actual names, not strings
# TODO: at least get some warnings when doing a config (like check args names)
# name-based routing: if func has this name, do this

audio_anomalies = audio_anomalies.ch_funcs(
    # get_audio=lambda audio_source: wav_file_to_array(audio_source),
    get_audio=get_sound,
    #     train=lambda wf, learner: auto_spectral_anomaly_learner(wf, learner=learner),
    #     train=auto_spectral_anomaly_learner,
    train=include_exclude(
        # sml.auto_spectral_anomaly_learner, include="wf learner", exclude=""
        sml.auto_spectral_anomaly_learner,
        include="wf learner",
        # exclude="learner",
    ),
    # train=rm_params(
    #     # sml.auto_spectral_anomaly_learner, include="wf learner", exclude=""
    #     sml.auto_spectral_anomaly_learner,
    #     params_to_remove=("learner",),
    # ),
    # train=FuncFactory(
    #     # sml.auto_spectral_anomaly_learner, include="wf learner", exclude=""
    #     sml.auto_spectral_anomaly_learner,
    #     # include="wf",
    #     exclude=("learner",),
    # ),
    apply=lambda model, wf: model(wf),
)

# filepath = '/Users/thorwhalen/Dropbox/_odata/sound/engines/aircraft/Aircraft Engine 01.wav'
filepath = "/Users/sylvain/Dropbox/_odata/sound/guns/01 Gunshot Pistol - Small Caliber - 18 Versions.wav"


def mk_pipeline_maker_app_with_mall(
    mall: Mapping,
    *,
    pipelines: str = None,
    sound_output: str = None,
    models_scores: str = None,
):

    if not b.mall():
        b.mall = mall
    mall = b.mall()
    store = dict()
    # mall["wf_store"] = store
    # audio_anomalies = sml.audio_anomalies

    _funcs = crudify_funcs(var_nodes="wf model results", dag=audio_anomalies, mall=mall)
    # it = crudify_funcs(var_nodes="wf", dag=audio_anomalies, mall=mall)
    print(audio_anomalies.synopsis_string())
    print(mall)

    def debug_check_mall():
        st.write(mall)
        return None

    step1, step2, step3 = _funcs  # remove list
    # name becomes actually "get_sound"
    print(f"{step1.__name__ =}")
    print(f"{step2.__name__ =}")
    print(f"{step3.__name__ =}")

    # step2 = FuncFactory(
    #     step2, exclude=("learner",)
    # )  # when you want to not display some arg
    step2a = rm_params(step2, params_to_remove=("learner",))
    print(f"name after param removal: {step2.__name__}")
    print(Sig(step2))
    # step2 = include_exclude(step2, exclude=("learner",))

    step2a.__name__ = "step2a"
    from functools import partial

    step1 = partial(step1, save_name="a_wf")
    # step1.__name__ = "step1"
    #
    # step2 = partial(step2, save_name="a_model")
    step3.__name__ = "step3"
    print(f"{Sig(step2a)=}")

    config = {
        APP_KEY: {"title": "Data Preparation"},
        RENDERING_KEY: {
            "get_sound": {
                "execution": {
                    "inputs": {
                        "audio_source": {
                            ELEMENT_KEY: FileUploader,
                            "type": "wav",
                            "accept_multiple_files": True,
                        },
                    },
                },
            },
            "step2a": {
                "execution": {
                    "inputs": {
                        "wf": {
                            ELEMENT_KEY: SelectBox,
                            "options": mall["wf_store"],
                        },
                    },
                },
            },
            "step3": {
                NAME_KEY: "Apply model",
                "execution": {
                    "output": {
                        ELEMENT_KEY: ArrayPlotter,
                    },
                },
            },
        },
    }
    funcs = [
        step1,
        step2a,
        step3,
        debug_check_mall,
    ]
    print(f"after config : {Sig(step2a)}")

    app = mk_app(funcs, config=config)

    return app


if __name__ == "__main__":
    import streamlit as st

    mall = dict(
        wf_store=dict(),
        # pipelines=dict(),
        # models_scores=dict(),
    )

    app = mk_pipeline_maker_app_with_mall(mall)

    app()

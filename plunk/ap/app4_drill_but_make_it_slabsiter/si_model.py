from pathlib import Path

import numpy as np
from front.crude import DillFiles
from lined import LineParametrized

from plunk.ap.live_graph.live_graph_data_buffer import _test_audio_it
from plunk.ap.snippets import if_no_none
from plunk.sb.front_demo.user_story1.apps.app4_drill import (
    simple_chunker,
    simple_featurizer,
    tagged_sounds_to_single_array,
    assert_dims,
)

dill_path = Path(__file__).parent / 'dill_files'
dill_path.mkdir(parents=True, exist_ok=True)
dill_files = DillFiles(str(dill_path))

# dill files are generated by running plunk/ap/app4_drill_but_make_it_slabsiter/app4_drill.py
#   and then creating and applying a model
normal_tagged_data = dill_files['tagged_data']
preprocess_pipeline_steps = LineParametrized(simple_chunker, simple_featurizer)
normal_fitted_model = dill_files['fitted_model']


def sb_apply_fitted_model(tagged_data, preprocess_pipeline, fitted_model):
    """Sylvain Bonnot"""
    sound, tag = tagged_sounds_to_single_array(*tagged_data)
    wfs = np.array(sound)
    wfs = assert_dims(wfs)

    fvs = preprocess_pipeline(wfs)
    scores = fitted_model.score_samples(X=fvs)
    return scores


@if_no_none
def wf_to_fvs(wf, preprocess_pipeline):
    fvs = preprocess_pipeline(wf)
    return fvs


@if_no_none
def fvs_to_scores(fvs, fitted_model):
    scores = fitted_model.score_samples(X=fvs)
    return scores


def si_apply_fitted_model(preprocess_pipeline, fitted_model):
    """SlabsIter kwargs"""

    si_kwargs = dict(
        preprocess_pipeline=lambda: preprocess_pipeline,
        fitted_model=lambda: fitted_model,
        fvs=wf_to_fvs,
        scores=fvs_to_scores,
    )

    return si_kwargs


if __name__ == '__main__':
    input_device = 'NexiGo N930AF FHD Webcam Audio'

    _test_audio_it(
        input_device=input_device,
        **si_apply_fitted_model(preprocess_pipeline_steps, normal_fitted_model)
    )

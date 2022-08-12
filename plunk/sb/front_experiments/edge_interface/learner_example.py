from dataclasses import dataclass
from typing import Iterable
from meshed import code_to_dag, DAG
from front import APP_KEY, RENDERING_KEY, ELEMENT_KEY, NAME_KEY, OBJ_KEY
from collections.abc import Callable
from front.crude import prepare_for_crude_dispatch
from streamlitfront.elements import TextInput, SelectBox, FloatSliderInput, TextOutput
from front.elements import OutputBase, FileUploaderBase
from streamlitfront import mk_app
from streamlitfront.examples.util import Graph
from streamlitfront.elements import (
    AudioRecorder,
    FileUploader,
    MultiSourceInputContainer,
)
import streamlit as st
import matplotlib.pyplot as plt
import soundfile as sf
from io import BytesIO
from front.crude import Crudifier
from odat.mdat.vacuum import (
    Dacc,
    DFLT_ANNOTS_COLS,
    annot_columns,
    DFLT_LOCAL_SOURCE_DIR,
    DFLT_CHUNKER,
    DFLT_FEATURIZER,
)
from sklearn.preprocessing import normalize
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from front.crude import Crudifier


chunker = DFLT_CHUNKER
featurizer = DFLT_FEATURIZER
learner = RandomForestClassifier(max_depth=2, random_state=0)


@dataclass
class NumpyArrayDisplay(OutputBase):
    def render(self):
        arr = self.output
        st.write(arr)


def mk_Xy(wfs, annots):
    X_train, y_train, X_test, y_test = [], [], [], []
    for sref, tag, train_info, _ in annots:

        signal = wfs[sref]
        wf = normalize(np.float32(signal).reshape(1, -1))[0]
        for chk in chunker(wf):

            if train_info == "train":
                X_train.append(featurizer(chk))
                y_train.append(tag)
            if train_info == "test":
                X_test.append(featurizer(chk))
                y_test.append(tag)

    return np.array(X_train), y_train, np.array(X_test), y_test


def preprocess(X_train):

    from shaded.chained_spectral_projector import learn_chain_proj_matrix

    proj_matrix = learn_chain_proj_matrix(X_train)
    X_train_proj = np.dot(X_train, proj_matrix)

    return proj_matrix, X_train_proj


def train(learner, X_train, y_train):
    proj_matrix, X_train = preprocess(X_train)
    fitted_learner = learner.fit(X_train, y_train)

    return fitted_learner, proj_matrix


def apply(model, preprocessor, X):
    X = np.dot(X, preprocessor)
    return model.predict(X)


def get_wfs(wf_src):
    dacc = Dacc(wf_src)
    return dacc.wfs


def get_annots(wf_store):
    srefs = wf_store.keys()
    annots = annot_columns(srefs)
    return annots  # may be display small table of results: OutputTable


def disp_results(results):
    return len(results)


# func_source: mapping
d = {
    "get_wfs": get_wfs,
    "get_annots": get_annots,
    "mk_Xy": mk_Xy,
    "train": train,
    "apply": apply,
}


# @code_to_dag(func_src=d)
# def classify():
#     wf_store = get_wfs(wf_src)  # better tuple wfs_train, wfs_test
#     annots = get_annots(wf_store)  # annots_src: may be a dataframe
#     X_train, y_train, X_test, y_test = mk_Xy(wf_store, annots)
#     model, preprocessor = train(learner, X_train, y_train)
#     results = apply(model, preprocessor, X_test)  # may be loaded by user


if "mall" not in st.session_state:
    st.session_state["mall"] = dict(
        learner={"rtree": RandomForestClassifier(max_depth=2, random_state=0)}
    )


mall = st.session_state["mall"]


@Crudifier(mall=mall, param_to_mall_map={"learner": "learner"})
def classify(wf_src, learner):
    wf_store = get_wfs(wf_src)  # better tuple wfs_train, wfs_test
    annots = get_annots(wf_store)
    # st.write(annots)
    X_train, y_train, X_test, y_test = mk_Xy(wf_store, annots)
    model, preprocessor = train(learner, X_train, y_train)
    results = apply(model, preprocessor, X_test)
    return results
    # st.write(type(results))
    # output = disp_results(results)


config_ = {
    APP_KEY: {"title": "Crudified learner"},
    RENDERING_KEY: {
        "classify": {
            "execution": {
                "inputs": {
                    "wf_src": {
                        ELEMENT_KEY: TextInput,
                    },
                    "learner": {
                        ELEMENT_KEY: SelectBox,
                        "options": mall["learner"],
                    },
                },
                "output": {
                    ELEMENT_KEY: NumpyArrayDisplay,
                },
            }
        },
    },
}

app = mk_app(
    [classify],
    config=config_,
)
app()

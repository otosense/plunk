"""
An app to take care of the initial 'sourcing' part of the data prep of audio ML
"""
from typing import Mapping, Any
from webbrowser import get
from know.boxes import *
from functools import partial
from typing import Callable, Iterable
from front import APP_KEY, RENDERING_KEY, ELEMENT_KEY, NAME_KEY
from i2 import Pipe, Sig
from front.crude import Crudifier
from slang.chunkers import fixed_step_chunker
import streamlit as st
from streamlitfront import mk_app, binder as b
from streamlitfront.data_binding import BoundData

from streamlitfront.elements import (
    SelectBox,
    SuccessNotification,
    KwargsInput,
    PipelineMaker,
    HiddenOutput,
)
from front.crude import prepare_for_crude_dispatch
from streamlitfront.elements import TextInput, SelectBox
from front.elements import OutputBase, ExecContainerBase, InputBase
from streamlitfront.elements import TextInput, SelectBox, ExecSection, TextOutput
from streamlitfront.elements import (
    App,
    ExecSection,
    FloatInput,
    IntInput,
    TextInput,
    TextOutput,
    TextSection,
    View,
)

from slang import fixed_step_chunker, mk_chk_fft
from dataclasses import dataclass

from plunk.sb.front_experiments.streamlitfront_dataprep.data_prep2 import (
    # DFLT_WF_PATH,
    # DFLT_ANNOT_PATH,
    data_from_wav_folder,
    data_from_csv,
    store_to_key_fvs,
    key_fvs_to_tag_fvs,
    mk_Xy,
)


def identity(func: Callable):
    return func


def foo(x: int):
    return x


def bar(msg: str):
    return msg * 2


if not b.mall():
    # TODO: Maybe it's here that we need to use know.malls.mk_mall?
    b.mall = {'func_choices': {'foo': foo, 'bar': bar}, 'selected_func_store': {}}
mall = b.mall()

if not b.selected_func():
    b.selected_func = 'foo'

crudifier = partial(Crudifier, mall=mall)


@crudifier(param_to_mall_map=dict(func='func_choices'))
def identity(func: Callable):
    return func


@dataclass
class OutRenderer(InputBase):
    def render(self):
        st.write(f'{self=}')
        # st.write(f"{self.output=}")


@dataclass
class FuncRenderer(OutputBase):
    value: Any = None

    def __post_init__(self):
        super().__post_init__()

    def _return_kwargs(self, output):
        st.write(f'output = {output}')

    def render(self):
        sig = Sig(self.output)
        st.write(sig)

        exec_section = ExecSection(
            obj=self.output,
            inputs={
                name: {ELEMENT_KEY: TextInput, 'bound_data_factory': BoundData}
                for name in sig
            },
            output={ELEMENT_KEY: TextOutput},
            auto_submit=True,
            on_submit=self._return_kwargs,
            use_expander=False,
        )
        exec_section()


class SimpleOutputFunc(ExecContainerBase):
    def render(self):
        st.write(self.obj)


config = {
    APP_KEY: {'title': 'Funcs'},
    RENDERING_KEY: {
        'identity': {
            NAME_KEY: 'Identity Rendering',
            'execution': {
                'inputs': {
                    'func': {
                        ELEMENT_KEY: SelectBox,
                        'options': mall['func_choices'],
                        'value': b.selected_func,
                    },
                },
                'output': {ELEMENT_KEY: FuncRenderer},
            },
        }
    },
}


funcs = [identity]
app = mk_app(funcs, config=config)


app()


if __name__ == '__main__':
    from streamlitfront.base import get_func_args_specs

    print(get_func_args_specs(identity))
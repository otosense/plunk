from front.spec_maker_base import APP_KEY, RENDERING_KEY, ELEMENT_KEY
from streamlitfront.elements import FloatSliderInput, TextOutput
from front.elements import OutputBase
from streamlitfront.base import mk_app
import streamlit as st


def foo(a: int = 1, b: int = 2, c=3):
    """This is foo. It computes something"""
    return (a * b) + c


def bar(x, greeting='hello'):
    """bar greets its input"""
    return f'{greeting} {x}'


def confuser(a: int, x: float = 3.14):
    return (a ** 2) * x


def proportion(x: int = 100, p: float = 0.5):
    return x * p


class SimpleOutput(TextOutput):
    def render(self):
        st.write(f'What has been entered={self.output}')


class SimpleOutput2(OutputBase):
    def render(self):
        st.write(f'What has been entered={self.output}')


app = mk_app(
    [foo, proportion],
    config={
        APP_KEY: {'title': 'My app'},
        RENDERING_KEY: {
            'proportion': {
                'execution': {
                    'inputs': {'p': {ELEMENT_KEY: FloatSliderInput,}},
                    'output': {ELEMENT_KEY: SimpleOutput2},
                }
            },
        },
    },
)
app()

import dearpygui.dearpygui as dpg
from more_itertools import windowed
import numpy as np

########################################################################################################################
# Simple Data Flow
########################################################################################################################
# Table of Contents
#
#   0 Themes
#   1 Node DPG Wrappings
#   2 Drag & Drop
#   3 Inspectors
#   4 Modifiers
#   5 Tools
#   6 Application
#
# How do I use this tool? (check the bottom of this file)
#   0. Create an App Instance. (app = App())
#   1. Add data sets.          (add_data_set method)
#   2. Add modifiers.          (add_modifier method)
#   3. Add inspectors.         (add_inspector method)
#   4. Add tools.              (add_tool method)
#   5. Start App.              (start method)
#
# How do I create a Modifier/Inspector/Tool? (check the MinMaxNode below)
#   0. Create a class derived from "Node". (Call it "NewNode" for this example)
#   1. In the constructor, add attributes.
#   2. Override the "execute" method that does the following:
#     a. First argument is "data".
#     b. Retrieve input attribute data.
#     c. Perform your operations.
#     d. Call "execute" methods of your output attributes (modifiers).
#     e. Call "finish".
#   3. Create a static method called "factory" that creates a returns a "NewNode".
#   4. Call either add_tool, add_modifier, or add_inspector method of app like so:
#     a. "app.add_modifier("NewNode", NewNode.factory, None)"
#     b. The 3rd argument of DragSource can be any data and will be passed into the factory's second argument
########################################################################################################################

########################################################################################################################
# Setup
########################################################################################################################
dpg.create_context()
dpg.create_viewport()
dpg.setup_dearpygui()

########################################################################################################################
# Themes
########################################################################################################################

with dpg.theme() as _source_theme:
    with dpg.theme_component(dpg.mvButton):
        # dpg.add_theme_color(dpg.mvThemeCol_Button, [25, 119, 0])
        dpg.add_theme_color(dpg.mvThemeCol_Button, [116, 185, 255])

        dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, [25, 255, 0])
        dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, [25, 119, 0])

with dpg.theme() as _completion_theme:
    with dpg.theme_component(dpg.mvAll):
        dpg.add_theme_color(
            dpg.mvNodeCol_TitleBar, [37, 28, 138], category=dpg.mvThemeCat_Nodes
        )
        dpg.add_theme_color(
            dpg.mvNodeCol_TitleBarHovered, [37, 28, 138], category=dpg.mvThemeCat_Nodes
        )
        dpg.add_theme_color(
            dpg.mvNodeCol_TitleBarSelected, [37, 28, 138], category=dpg.mvThemeCat_Nodes
        )

with dpg.theme() as _tools_theme:
    with dpg.theme_component(dpg.mvAll):
        dpg.add_theme_color(
            dpg.mvNodeCol_TitleBar, [225, 112, 85], category=dpg.mvThemeCat_Nodes
        )
        dpg.add_theme_color(
            dpg.mvNodeCol_TitleBarHovered, [225, 112, 85], category=dpg.mvThemeCat_Nodes
        )
        dpg.add_theme_color(
            dpg.mvNodeCol_TitleBarSelected,
            [225, 112, 85],
            category=dpg.mvThemeCat_Nodes,
        )
########################################################################################################################
# Node DPG Wrappings
########################################################################################################################
class OutputNodeAttribute:
    def __init__(self, label: str = 'output'):

        self._label = label
        self.uuid = dpg.generate_uuid()
        self._children = []  # output attributes
        self._data = None

    def add_child(self, parent, child):

        dpg.add_node_link(self.uuid, child.uuid, parent=parent)
        child.set_parent(self)
        self._children.append(child)

    def execute(self, data):
        self._data = data
        for child in self._children:
            child._data = self._data

    def submit(self, parent):

        with dpg.node_attribute(
            parent=parent,
            attribute_type=dpg.mvNode_Attr_Output,
            user_data=self,
            id=self.uuid,
        ):
            dpg.add_text(self._label)


class InputNodeAttribute:
    def __init__(self, label: str = 'input'):

        self._label = label
        self.uuid = dpg.generate_uuid()
        self._parent = None  # input attribute
        self._data = None

    def get_data(self):
        return self._data

    def set_parent(self, parent: OutputNodeAttribute):
        self._parent = parent

    def submit(self, parent):

        with dpg.node_attribute(parent=parent, user_data=self, id=self.uuid):
            dpg.add_text(self._label)


class Node:
    def __init__(self, label: str, data):

        self.label = label
        self.uuid = dpg.generate_uuid()
        self.static_uuid = dpg.generate_uuid()
        self._input_attributes = []
        self._output_attributes = []
        self._data = data

    def finish(self):
        dpg.bind_item_theme(self.uuid, _completion_theme)

    def add_input_attribute(self, attribute: InputNodeAttribute):
        self._input_attributes.append(attribute)

    def add_output_attribute(self, attribute: OutputNodeAttribute):
        self._output_attributes.append(attribute)

    def execute(self):

        for attribute in self._output_attributes:
            attribute.execute(self._data)

        self.finish()

    def custom(self):
        pass

    def submit(self, parent):

        with dpg.node(parent=parent, label=self.label, tag=self.uuid):

            with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Static):
                dpg.add_button(
                    label='Execute',
                    user_data=self,
                    callback=lambda s, a, u: u.execute(),
                )

            for attribute in self._input_attributes:
                attribute.submit(self.uuid)

            with dpg.node_attribute(
                parent=self.uuid,
                attribute_type=dpg.mvNode_Attr_Static,
                user_data=self,
                tag=self.static_uuid,
            ):
                self.custom()

            for attribute in self._output_attributes:
                attribute.submit(self.uuid)


class NodeEditor:
    @staticmethod
    def _link_callback(sender, app_data, user_data):
        output_attr_uuid, input_attr_uuid = app_data

        input_attr = dpg.get_item_user_data(input_attr_uuid)
        output_attr = dpg.get_item_user_data(output_attr_uuid)

        output_attr.add_child(sender, input_attr)

    def __init__(self):

        self._nodes = []
        self.uuid = dpg.generate_uuid()

    def add_node(self, node: Node):
        self._nodes.append(node)

    def on_drop(self, sender, app_data, user_data):
        source, generator, data = app_data
        node = generator(source.label, data)
        node.submit(self.uuid)
        self.add_node(node)

    def submit(self, parent):

        with dpg.child_window(
            width=-160,
            parent=parent,
            user_data=self,
            drop_callback=lambda s, a, u: dpg.get_item_user_data(s).on_drop(s, a, u),
        ):
            with dpg.node_editor(
                tag=self.uuid, callback=NodeEditor._link_callback, width=-1, height=-1
            ):
                for node in self._nodes:
                    node.submit(self.uuid)


########################################################################################################################
# Drag & Drop
########################################################################################################################
class DragSource:
    def __init__(self, label: str, node_generator, data):

        self.label = label
        self._generator = node_generator
        self._data = data

    def submit(self, parent):

        dpg.add_button(label=self.label, parent=parent, width=-1)
        dpg.bind_item_theme(dpg.last_item(), _source_theme)

        with dpg.drag_payload(
            parent=dpg.last_item(), drag_data=(self, self._generator, self._data)
        ):
            dpg.add_text(f'Name: {self.label}')


class DragSourceContainer:
    def __init__(self, label: str, width: int = 150, height: int = -1):

        self._label = label
        self._width = width
        self._height = height
        self._uuid = dpg.generate_uuid()
        self._children = []  # drag sources

    def add_drag_source(self, source: DragSource):

        self._children.append(source)

    def submit(self, parent):

        with dpg.child_window(
            parent=parent,
            width=self._width,
            height=self._height,
            tag=self._uuid,
            menubar=True,
        ) as child_parent:
            with dpg.menu_bar():
                dpg.add_menu(label=self._label)

            for child in self._children:
                child.submit(child_parent)


########################################################################################################################
# Inspectors
########################################################################################################################
class MaxMinNode(Node):
    @staticmethod
    def factory(name, data):
        node = MaxMinNode(name, data)
        return node

    def __init__(self, label: str, data):
        super().__init__(label, data)

        self.add_input_attribute(InputNodeAttribute('values'))
        self.add_output_attribute(OutputNodeAttribute('min'))
        self.add_output_attribute(OutputNodeAttribute('max'))

        self.min_id = dpg.generate_uuid()
        self.max_id = dpg.generate_uuid()

    def custom(self):

        with dpg.group(width=150):
            dpg.add_text(
                'Not Calculated', label='Min', show_label=True, tag=self.min_id
            )
            dpg.add_text(
                'Not Calculated', label='Max', show_label=True, tag=self.max_id
            )

    def execute(self):

        # get input attribute data
        values = self._input_attributes[0].get_data()

        # perform actual operations
        min_value = values[0]
        max_value = values[0]

        for i in range(0, len(values)):

            if values[i] > max_value:
                max_value = values[i]

            if values[i] < min_value:
                min_value = values[i]

        dpg.set_value(self.min_id, str(min_value))
        dpg.set_value(self.max_id, str(max_value))

        # execute output attributes
        self._output_attributes[0].execute(min_value)
        self._output_attributes[1].execute(max_value)

        self.finish()


########################################################################################################################
# Functions
########################################################################################################################
# class DataShifterNode(Node):
#     @staticmethod
#     def factory(name, data):
#         node = DataShifterNode(name, data)
#         return node

#     def __init__(self, label: str, data):
#         super().__init__(label, data)

#         self.add_input_attribute(InputNodeAttribute("x"))
#         self.add_input_attribute(InputNodeAttribute("y"))
#         self.add_output_attribute(OutputNodeAttribute("x mod"))
#         self.add_output_attribute(OutputNodeAttribute("y mod"))

#         self.x_shift = dpg.generate_uuid()
#         self.y_shift = dpg.generate_uuid()

#     def custom(self):

#         dpg.add_input_float(label="x", tag=self.x_shift, step=0, width=150)
#         dpg.add_input_float(label="y", tag=self.y_shift, step=0, width=150)

#     def execute(self):

#         # get values from static attributes
#         x_shift = dpg.get_value(self.x_shift)
#         y_shift = dpg.get_value(self.y_shift)

#         # get input attribute data
#         x_orig_data = self._input_attributes[0].get_data()
#         y_orig_data = self._input_attributes[1].get_data()

#         # perform actual operations
#         x_data = []
#         for i in range(0, len(x_orig_data)):
#             x_data.append(x_orig_data[i] + x_shift)

#         y_data = []
#         for i in range(0, len(y_orig_data)):
#             y_data.append(y_orig_data[i] + y_shift)

#         # execute output attributes
#         self._output_attributes[0].execute(x_data)
#         self._output_attributes[1].execute(y_data)

#         self.finish()


class ChunkerNode(Node):
    @staticmethod
    def factory(name, data):
        node = ChunkerNode(name, data)
        return node

    def __init__(self, label: str, data):
        super().__init__(label, data)

        self.add_input_attribute(InputNodeAttribute('wf'))
        self.add_output_attribute(OutputNodeAttribute('chks'))
        # self.add_output_attribute(OutputNodeAttribute("y mod"))

        self.x_shift = dpg.generate_uuid()
        # self.y_shift = dpg.generate_uuid()

    def custom(self):

        dpg.add_input_int(label='chk_size', tag=self.x_shift, step=0, width=150)
        # dpg.add_input_float(label="y", tag=self.y_shift, step=0, width=150)

    def execute(self):

        # get values from static attributes
        # x_shift = dpg.get_value(self.x_shift)
        # y_shift = dpg.get_value(self.y_shift)

        # get input attribute data
        x_orig_data = self._input_attributes[0].get_data()
        # y_orig_data = self._input_attributes[1].get_data()

        # perform actual operations
        x_data = windowed(x_orig_data, 3)

        # execute output attributes
        self._output_attributes[0].execute(x_data)
        # self._output_attributes[1].execute(y_data)

        self.finish()


class FeaturizerNode(Node):
    @staticmethod
    def factory(name, data):
        node = FeaturizerNode(name, data)
        return node

    def __init__(self, label: str, data):
        super().__init__(label, data)

        self.add_input_attribute(InputNodeAttribute('chks'))

        self.add_output_attribute(OutputNodeAttribute('fvs'))
        # self.add_output_attribute(OutputNodeAttribute("y mod"))

        self.x_shift = dpg.generate_uuid()
        # self.y_shift = dpg.generate_uuid()

    def custom(self):

        dpg.add_input_float(label='x', tag=self.x_shift, step=0, width=150)
        # dpg.add_input_float(label="y", tag=self.y_shift, step=0, width=150)

    def execute(self):

        # get values from static attributes
        # x_shift = dpg.get_value(self.x_shift)
        # y_shift = dpg.get_value(self.y_shift)

        # get input attribute data
        x_orig_data = self._input_attributes[0].get_data()
        # y_orig_data = self._input_attributes[1].get_data()

        # perform actual operations
        x_data = [np.std(x) for x in x_orig_data]

        # execute output attributes
        self._output_attributes[0].execute(x_data)
        # self._output_attributes[1].execute(y_data)

        self.finish()


########################################################################################################################
# Tools
########################################################################################################################
class ViewNode_1D(Node):
    @staticmethod
    def factory(name, data):
        node = ViewNode_1D(name, data)
        return node

    def __init__(self, label: str, data):
        super().__init__(label, data)

        self.add_input_attribute(InputNodeAttribute('x'))
        self.simple_plot = dpg.generate_uuid()

    def custom(self):

        dpg.add_simple_plot(
            label='Data View', width=200, height=80, tag=self.simple_plot
        )

    def execute(self):

        # plot_id = self._static_attributes[0].simple_plot
        # plot_id = self._input_attributes[0].simple_plot
        dpg.set_value(self.simple_plot, self._input_attributes[0].get_data())
        self.finish()


class ViewNode_2D(Node):
    @staticmethod
    def factory(name, data):
        node = ViewNode_2D(name, data)
        return node

    def __init__(self, label: str, data):
        super().__init__(label, data)

        self.add_input_attribute(InputNodeAttribute('x'))
        self.add_input_attribute(InputNodeAttribute('y'))

        self.x_axis = dpg.generate_uuid()
        self.y_axis = dpg.generate_uuid()

    def custom(self):

        with dpg.plot(height=400, width=400, no_title=True):
            dpg.add_plot_axis(dpg.mvXAxis, label='', tag=self.x_axis)
            dpg.add_plot_axis(dpg.mvYAxis, label='', tag=self.y_axis)

    def execute(self):

        x_axis_id = self.x_axis
        y_axis_id = self.y_axis

        x_orig_data = self._input_attributes[0].get_data()
        y_orig_data = self._input_attributes[1].get_data()

        dpg.add_line_series(x_orig_data, y_orig_data, parent=y_axis_id)
        dpg.fit_axis_data(x_axis_id)
        dpg.fit_axis_data(y_axis_id)

        self.finish()


class PlotNode_1D(Node):
    @staticmethod
    def factory(name, data):
        node = PlotNode_1D(name, data)
        return node

    def __init__(self, label: str, data):
        super().__init__(label, data)

        self.add_input_attribute(InputNodeAttribute('y'))
        # self.add_input_attribute(InputNodeAttribute("y"))

        self.x_axis = dpg.generate_uuid()
        self.y_axis = dpg.generate_uuid()

    def custom(self):

        with dpg.plot(height=400, width=400, no_title=True):
            dpg.add_plot_axis(dpg.mvXAxis, label='', tag=self.x_axis)
            dpg.add_plot_axis(dpg.mvYAxis, label='', tag=self.y_axis)

    def execute(self):

        x_axis_id = self.x_axis
        y_axis_id = self.y_axis

        # x_orig_data = self._input_attributes[0].get_data()
        y_orig_data = self._input_attributes[0].get_data()
        print(y_orig_data)
        # x_orig_data = range(len(y_orig_data))
        x_orig_data = range(10)

        dpg.add_line_series(x_orig_data, y_orig_data, parent=y_axis_id)
        dpg.fit_axis_data(x_axis_id)
        dpg.fit_axis_data(y_axis_id)

        self.finish()


class WavFilePlotNode(Node):
    @staticmethod
    def factory(name, data):
        node = WavFilePlotNode(name, data)
        return node

    def __init__(self, label: str, data):
        super().__init__(label, data)

        self.add_input_attribute(InputNodeAttribute('wf'))
        # self.add_input_attribute(InputNodeAttribute("y"))

        self.x_axis = dpg.generate_uuid()
        self.y_axis = dpg.generate_uuid()

    def custom(self):

        with dpg.plot(height=400, width=400, no_title=True):
            dpg.add_plot_axis(dpg.mvXAxis, label='', tag=self.x_axis)
            dpg.add_plot_axis(dpg.mvYAxis, label='', tag=self.y_axis)

    def execute(self):

        x_axis_id = self.x_axis
        y_axis_id = self.y_axis

        # x_orig_data = self._input_attributes[0].get_data()
        y_orig_data = self._input_attributes[0].get_data()
        print(y_orig_data)
        # x_orig_data = range(len(y_orig_data))
        x_orig_data = range(10)

        dpg.add_line_series(x_orig_data, y_orig_data, parent=y_axis_id)
        dpg.fit_axis_data(x_axis_id)
        dpg.fit_axis_data(y_axis_id)

        self.finish()


class CheckerNode(Node):
    @staticmethod
    def factory(name, data):
        node = CheckerNode(name, data)
        return node

    def __init__(self, label: str, data):
        super().__init__(label, data)

        self.add_input_attribute(InputNodeAttribute('Value'))

        self.expected_id = dpg.generate_uuid()
        self.min_id = dpg.generate_uuid()
        self.max_id = dpg.generate_uuid()
        self.status_id = dpg.generate_uuid()

        with dpg.theme() as self.success:
            dpg.add_theme_color(
                dpg.mvThemeCol_CheckMark,
                [0, 255, 0],
                category=dpg.mvThemeCat_Core,
                tag=self.success,
            )

        with dpg.theme() as self.fail:
            dpg.add_theme_color(
                dpg.mvThemeCol_CheckMark,
                [255, 0, 0],
                category=dpg.mvThemeCat_Core,
                tag=self.fail,
            )

        with dpg.theme() as self.neutral:
            dpg.add_theme_color(
                dpg.mvThemeCol_CheckMark,
                [255, 255, 0],
                category=dpg.mvThemeCat_Core,
                tag=self.neutral,
            )

    def custom(self):

        with dpg.group(width=150):
            dpg.add_input_float(
                label='Expected Value', step=0.0, tag=self.expected_id, default_value=10
            )
            dpg.add_input_float(
                label='Max Tolerance', step=0.0, tag=self.max_id, default_value=0.05
            )
            dpg.add_input_float(
                label='Min Tolerance', step=0.0, tag=self.min_id, default_value=0.05
            )
            dpg.add_radio_button(items=['Status'], tag=self.status_id)
            dpg.set_item_theme(self.status_id, self.neutral)

    def execute(self):

        # get input attribute data
        value = round(self._input_attributes[0].get_data(), 5)

        min_value = dpg.get_value(self.min_id)
        max_value = dpg.get_value(self.max_id)
        expect_value = dpg.get_value(self.expected_id)

        if (
            round(expect_value - min_value, 5)
            <= value
            <= round(expect_value + max_value, 5)
        ):
            dpg.set_item_theme(self._static_attributes[0].status_id, self.success)
        else:
            dpg.set_item_theme(self._static_attributes[0].status_id, self.fail)

        self.finish()


class ValueNode(Node):
    @staticmethod
    def factory(name, data):
        node = ValueNode(name, data)
        return node

    def __init__(self, label: str, data):
        super().__init__(label, data)

        self.add_output_attribute(OutputNodeAttribute('Value'))

        self.value = dpg.generate_uuid()

    def custom(self):

        with dpg.group(width=150):
            dpg.add_input_float(
                label='Input Value', step=0, tag=self.value, default_value=10
            )

    def execute(self):

        # get input attribute data
        value = dpg.get_value(self.value)
        self._output_attributes[0].execute(value)

        self.finish()


class UploaderNode(Node):
    @staticmethod
    def factory(name, data):
        node = UploaderNode(name, data)
        return node

    def __init__(self, label: str, data):
        super().__init__(label, data)

        self.add_output_attribute(OutputNodeAttribute('Value'))

        self.value = dpg.generate_uuid()

    def custom(self):

        with dpg.group(width=150):
            # dpg.add_input_float(
            #     label="Input Value", step=0, tag=self.value, default_value=10
            # )

            def callback(sender, app_data, user_data):
                print('Sender: ', sender)
                print('App Data: ', app_data)

            with dpg.file_dialog(
                directory_selector=False,
                show=False,
                callback=callback,
                id='file_dialog_id',
                width=700,
                height=400,
            ):
                dpg.add_file_extension('.*')
                dpg.add_file_extension('', color=(150, 255, 150, 255))
                dpg.add_file_extension(
                    'Source files (*.cpp *.h *.hpp){.cpp,.h,.hpp}',
                    color=(0, 255, 255, 255),
                )
                dpg.add_file_extension(
                    '.h', color=(255, 0, 255, 255), custom_text='[header]'
                )
                dpg.add_file_extension(
                    '.py', color=(0, 255, 0, 255), custom_text='[Python]'
                )
                dpg.add_file_extension(
                    '.wav', color=(0, 177, 0, 255), custom_text='[Wav]'
                )
            dpg.add_button(
                label='File Selector', callback=lambda: dpg.show_item('file_dialog_id'),
            )

    def execute(self):

        # get input attribute data
        value = dpg.get_value(self.value)
        print(f'execute value = {value}')
        self._output_attributes[0].execute(value)

        self.finish()


########################################################################################################################
# Application
########################################################################################################################
def save_graph(node_editor):
    import json

    state = dpg.get_item_configuration(node_editor)

    # save the state to a JSON file
    with open('my_graph.json', 'w') as f:
        json.dump(state, f)


def view_state(node_editor):
    nodes = node_editor._nodes
    for node in nodes:
        # print(node._label, node._data)
        print(f'{node=}, {vars(node)}')
        print(f'Children:\n')
        print([dir(attribute) for attribute in node._output_attributes])
        print(dir(node))


class App:
    @staticmethod
    def data_node_factory(name, data):
        node = Node(name, data)
        node.add_output_attribute(OutputNodeAttribute('data'))
        return node

    def __init__(self):

        self.data_set_container = DragSourceContainer('Data Sets', 150, -500)
        self.tool_container = DragSourceContainer('Tools', 150, -1)
        self.inspector_container = DragSourceContainer('Inspectors', 150, -500)
        self.modifier_container = DragSourceContainer('Functions', 150, -1)
        self.plugin_menu_id = dpg.generate_uuid()
        self.left_panel = dpg.generate_uuid()
        self.right_panel = dpg.generate_uuid()

        self.plugins = []

        self.add_data_set(
            'Test Data', [-5.0, -5.0, -3.0, -3.0, 0.0, 0.0, 3.0, 3.0, 5.0, 5.0]
        )
        self.add_tool('1D Data View', ViewNode_1D.factory)
        self.add_tool('2D Data View', ViewNode_2D.factory)
        self.add_tool('Checker Tool', CheckerNode.factory)
        self.add_tool('Value Tool', ValueNode.factory)
        self.add_inspector('MinMax', MaxMinNode.factory)
        # self.add_modifier("Data Shifter", DataShifterNode.factory)
        self.add_modifier('Chunker', ChunkerNode.factory)
        self.add_modifier('Featurizer', FeaturizerNode.factory)
        self.add_modifier('Plotter', PlotNode_1D.factory)
        self.add_modifier('Upload', UploaderNode.factory)

        # PlotNode_1D

    def update(self):

        with dpg.mutex():
            dpg.delete_item(self.left_panel, children_only=True)
            self.data_set_container.submit(self.left_panel)
            self.modifier_container.submit(self.left_panel)

            dpg.delete_item(self.right_panel, children_only=True)
            self.inspector_container.submit(self.right_panel)
            self.tool_container.submit(self.right_panel)

    def add_data_set(self, label, data):
        self.data_set_container.add_drag_source(
            DragSource(label, App.data_node_factory, data)
        )

    def add_tool(self, label, factory, data=None):
        self.tool_container.add_drag_source(DragSource(label, factory, data))

    def add_inspector(self, label, factory, data=None):
        self.inspector_container.add_drag_source(DragSource(label, factory, data))

    def add_modifier(self, label, factory, data=None):
        self.modifier_container.add_drag_source(DragSource(label, factory, data))

    def add_plugin(self, name, callback):
        self.plugins.append((name, callback))

    def start(self):

        # dpg.setup_registries()
        from dearpygui_ext.themes import create_theme_imgui_light

        dpg.create_context()
        # dpg.create_viewport(title='Custom Title', width=600, height=600)

        light_theme = create_theme_imgui_light()
        dpg.bind_theme(light_theme)
        dpg.set_viewport_title('Simple Data Flow')
        dpg.show_viewport()
        node_editor = NodeEditor()

        with dpg.window() as main_window:

            with dpg.menu_bar():

                with dpg.menu(label='Operations'):

                    dpg.add_menu_item(
                        label='Reset',
                        callback=lambda: dpg.delete_item(
                            node_editor.uuid, children_only=True
                        ),
                    )
                    dpg.add_menu_item(
                        label='Save graph',
                        # callback=lambda: save_graph(node_editor),
                        callback=lambda: view_state(node_editor),
                    )

                with dpg.menu(label='Plugins'):
                    for plugin in self.plugins:
                        dpg.add_menu_item(label=plugin[0], callback=plugin[1])

            with dpg.group(horizontal=True) as group:

                # left panel
                with dpg.group(id=self.left_panel):
                    self.data_set_container.submit(self.left_panel)
                    self.modifier_container.submit(self.left_panel)

                # center panel
                node_editor.submit(group)

                # right panel
                with dpg.group(id=self.right_panel):
                    self.inspector_container.submit(self.right_panel)
                    self.tool_container.submit(self.right_panel)

        dpg.set_primary_window(main_window, True)
        dpg.start_dearpygui()


if __name__ == '__main__':

    app = App()
    app.start()

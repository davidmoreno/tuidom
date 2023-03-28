#!/usr/bin/python3

from dataclasses import dataclass, field


class Component:
    name = None
    children: list = None
    props: dict = None
    __changed: bool = True
    __rendered_children: list = field(default_factory=list)

    def render(self):
        raise NotImplemented("WIP")

    def __init__(self, **props):
        if not self.name:
            self.name = self.__class__.__name__
        self.props = props

    def __getitem__(self, *children: list):
        self.children = children
        return self

    def __repr__(self):
        if not self.children:
            return f"<{self.name}/>"
        else:
            return f"<{self.name}>{self.children}</{self.name}>"


div = Component
div.__name__ = "div"
span = Component
span.__name__ = "span"


###

def CheckBox(**props):
    ret = Component(**props)
    ret.name = "CheckBox"
    return ret


class App(Component):
    state = {
        "is_on": True,
    }

    def render(self):
        return div(className="flex-row")[
            span()["Toggle"],
            CheckBox(value=self.state["is_on"], on_click=lambda ev: self.setState(
                {"is_on": ev.value}))
        ]


root = App()
print(root)
print(
    root.render()
)

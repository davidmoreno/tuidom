import inspect
from itertools import zip_longest
from typing import Optional
from tuidom import Div, Element, Span
from dataclasses import dataclass


class Component:
    state: dict = None
    props: dict = None
    children: list['Component'] = []

    def __init__(self, *children, **props: dict):
        self.props = props
        self.children = children

    def componentDidMount(self):
        return None

    def render(self):
        return None

    def setState(self, update):
        self.state = {
            **self.state,
            **update,
        }


def is_dict_equal(a, b):
    # not deep comparing YET
    for key, value in a.items():
        if value != b.get(key):
            return False
    if key in b.keys():
        if key not in a:
            return False

    return True


def to_list(maybelist):
    if isinstance(maybelist, list):
        return maybelist
    return [maybelist]


@dataclass
class ComponentPlan:
    """
    This is the result of createElement
    """
    # this is the constructor for whatever
    component: Component | Element
    # this is the currently cosntructed, or None if not yet
    props: dict
    key: Optional[str] = None
    children: list['ComponentPlan'] = None

    def same_as(self, other: 'ComponentPlan'):
        if self.component != other.component:
            return False
        if not is_dict_equal(self.props, other.props):
            return False
        for x, y in zip(self.children, other.children):
            if x != y:
                return False
        return True

    def to_string(self, indent=0):
        ws = " " * indent
        name = self.component.__class__.__name__ if isinstance(
            self.component, Component) else self.component.__name__
        ret = f"{ws}<{name}  {self.props}>"
        for child in self.children:
            ret += f"\n{ws}"
            if isinstance(child, ComponentPlan):
                ret += child.to_string(indent+2)
            else:
                ret += repr(child)
        ret += f"\n{ws}</{name}>"
        return ret


def createElement(component, props, *children):
    return ComponentPlan(
        component=component,
        props=props,
        children=children,
    )


def component(func):
    def wrapped(*children, **kwargs):
        props = {
            k: v for k, v in kwargs.items()
            if k != "children"
        } if 'children' in kwargs else kwargs

        return createElement(
            func,
            props,
            *children,
            *kwargs.get("children", []),
        )
    wrapped.__name__ = func.__name__
    wrapped.func = func
    return wrapped


def reconcile(node_a: ComponentPlan, node_b: ComponentPlan):
    # real changes
    if node_a is None:
        node_b.children = node_b.component.render()
        return node_b
    if node_b is None:
        return None

    if node_a.component != node_b.component or node_a.key != node_b.key:
        return node_b

    if not is_dict_equal(node_a.props, node_b.props):
        # change props, mark dirty to repaint
        node_a.props = node_b.props

    if isinstance(node_a.component, Component):
        nchildren = node_a.component.render()
    else:
        nchildren = [node_a.component(node_a.props)]

    children = []
    for a, b in zip_longest(node_a.children or [], nchildren or []):
        n = reconcile(a, b)
        children.append(n)

    node_a.children = children

    return node_a


def span(**props):
    return createElement(
        Span,
        props,
    )


def div(*children, **props):
    return createElement(
        Div,
        props,
        *children,
    )


def render(item: ComponentPlan) -> ComponentPlan:
    if isinstance(item, Element):
        return item

    # we got a class directly, but we can get how to construct again
    if isinstance(item, Component):
        item = createElement(
            item.__class__,
            item.props,
            *item.children,
        )

    if inspect.isclass(item.component) and issubclass(item.component, Component):
        item.component = item.component(**item.props)
        item.children = to_list(item.component.render())

    elif isinstance(item.component, Component):
        item.children = to_list(item.component.render())
    # nothing to do, unless is a callable later
    elif isinstance(item.component, Element):
        pass
    # nothing to do, unless is a callable later
    elif inspect.isclass(item.component) and issubclass(item.component, Element):
        pass
    elif callable(item.component):
        item.children = to_list(item.component(item.props))

    item.children = [
        render(child)
        for child in item.children
    ]

    return item


def render_to_dom(plan: ComponentPlan):

    def get_elements(plan):
        for item in plan.children:
            if isinstance(item, Element):
                yield item

    render(plan)
    return get_elements(plan)

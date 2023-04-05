

import itertools
import logging
from .events import HandleEventTrait
from .renderer import Renderer
logger = logging.getLogger(__name__)


class Component:
    serialid = 0  # jsut for debugging, to ensure materialize reuses as possible
    name = None
    children: list = None
    props: dict = None
    state: dict = None
    parent = None
    key = None

    __changed: bool = True
    __materialized_children: list = None

    def render(self):
        return self.children

    def paint(self, renderer: Renderer):
        logger.debug("paint %s", self)
        # if not self.__changed:
        #     return
        for child in self.__materialized_children:
            logger.debug("paint child %s", child)
            child.paint(renderer)

    def setChanged(self):
        if self.__changed:
            return
        self.__changed = True
        if self.parent:
            self.parent.setChanged()

    def setState(self, update):
        logger.debug("Update state %s: %s", self, update)
        if self.state is None:
            self.state = {}

        self.state = {**self.state, **update}
        self.setChanged()

    def normalize(self, nodes):
        """
        Helper to return always some component, normally translating
        strings to Text nodes.
        """
        if not isinstance(nodes, (list, tuple)):
            nodes = [nodes]
        ret = []
        for item in nodes:
            if isinstance(item, Component):
                item.children = self.normalize(item.children)
                ret.append(item)
            elif item is True:
                ret.append(Text(text=True))
            elif item is False or item is None:
                continue  # skip Falses and Nones
            else:
                ret.append(Text(text=str(item)))
        return ret

    def materialize(self):
        if not self.__changed:
            return

        children = self.normalize(self.render())

        if self.__materialized_children is None:
            for child in children:
                child.parent = self
            self.__materialized_children = children
        else:
            nextchildren = self.reconcile(
                self,
                self.__materialized_children,
                children
            )

            self.__materialized_children = nextchildren

        logger.debug("Materialized %s -> %s", self,
                     self.__materialized_children)
        # rec materialize
        for child in self.__materialized_children:
            child.materialize()

    def reconcile(self, parent, leftchildren, rightchildren):
        logger.debug("Reconcile two lists: %s <-> %s",
                     leftchildren, rightchildren)
        nextchildren = []
        for left, right in itertools.zip_longest(leftchildren, rightchildren):
            # print("materialize iseq", left, right)
            logger.debug("is eq: %s %s", left, right)
            if self.isEquivalent(left, right):
                logger.debug("Materialize reconcile: %s ~ %s", left, right)
                left.updateProps(right)
                nextchildren.append(left)
            else:
                logger.debug(
                    "Materialize reconcile: %s != %s", left, right)
                nextchildren.append(right)
            left.children = self.reconcile(
                left,
                left.children or [],
                right.children or [],
            )

        for child in nextchildren:
            if child.parent != parent:
                child.parent = parent
        return nextchildren

    def isEquivalent(self, left, right):
        if not left or not right:
            return False
        if left.key == right.key:
            return True
        if left.name == right.name:
            return True

        return False

    def updateProps(self, other):
        logger.debug("%s Update props: %s from %s",
                     self, self.props, other.props)
        for key, val in other.props.items():
            oldval = self.props.get(key)
            if not oldval:
                self.props[key] = val
                continue
            if oldval == val:
                continue
            if key[:3] == "on_":
                logger.debug("Do not replace on_ props: %s", key)
                continue
            logger.debug("Replace props: %s", key)
            self.props[key] = val

    def queryElement(self, query):
        if self.name == query:
            return self
        for child in self.__materialized_children:
            ret = child.queryElement(query)
            if ret:
                return ret

    def preorderTraversal(self):
        yield self
        for child in self.__materialized_children:
            yield from child.preorderTraversal()

    def __init__(self, **props):
        if not self.name:
            self.name = self.__class__.__name__
        self.props = props
        Component.serialid += 1
        self.serialid = Component.serialid
        super().__init__()

    def __getitem__(self, children: list):
        self.children = children
        return self

    def __repr__(self):
        if not self.children:
            return f"<{self.name} {self.serialid} {self.props}/>"
        else:
            return f"<{self.name} {self.serialid} {self.props}>{self.children}</{self.name}>"


class Paintable(HandleEventTrait, Component):
    """
    This component can be painted with the given renderer
    """

    def getStyle(self, key: str) -> str | None:
        """
        Returns a style by key.

        It might be search by classname or splicitly set
        """
        match key:
            case "color":
                return "white"
            case "background":
                return "blue"
        return None

    def paint(self, renderer: Renderer):
        color = self.getStyle("color")
        if color:
            renderer.setColor(color)
        background = self.getStyle("background")
        if background:
            renderer.setBackground(background)
            renderer.drawSquare(
                (0, 0), (10, 10),
            )
        super().paint(renderer)


class Text(Component):
    def paint(self, renderer: Renderer):
        text = self.props.get("text")
        if text:
            renderer.drawText(
                (5, 5),
                str(text)
            )


div = Paintable
div.__name__ = "div"
span = Paintable
span.__name__ = "span"

import logging
import retui
from .layout import Layout
from .text import LayoutText
from .flex_column import LayoutFlexColumn
from .flex_row import LayoutFlexRow

logger = logging.getLogger(__name__)


def create_layout(component: "retui.component.Component", display: str | None = None):
    """
    Creates a layout from the component.

    It may depend on the component display style, or by a forced one.

    The forced one is used at scrollables, to force  inner layout to be
    block layout
    """
    if not display:
        display = component.getStyle("display")

    if component.name == "Text":
        return LayoutText(component)

    match display:
        case "flex":
            direction = component.getStyle("flex-direction", "column")
            if direction == "column":
                return LayoutFlexColumn(component)
            else:
                return LayoutFlexRow(component)

    return Layout(component)

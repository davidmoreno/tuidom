import logging
import retui
from .layout import Layout
from .text import LayoutText
from .flex_column import LayoutFlexColumn
from .flex_row import LayoutFlexRow
from .block import LayoutBlock
from .absolute import LayoutAbsolute

logger = logging.getLogger(__name__)


def create_layout(component: "retui.component.Component", display: str | None = None):
    """
    Creates a layout from the component.

    It may depend on the component display style, or by a forced one.

    The forced one is used at scrollables, to force  inner layout to be
    block layout
    """

    if component.name == "Text":
        return LayoutText(component)

    if not display:
        display = component.getStyle("display")

    layout = None
    match display:
        case "flex":
            direction = component.getStyle("flex-direction", "column")
            if direction == "column":
                layout = LayoutFlexColumn(component)
            else:
                layout = LayoutFlexRow(component)

    # default layout is block
    if not layout:
        layout = LayoutBlock(component)

    position = component.getStyle("position")
    match position:
        case "absolute":
            # position absolute makes a nested layout
            layout = LayoutAbsolute(component, layout)

    return layout

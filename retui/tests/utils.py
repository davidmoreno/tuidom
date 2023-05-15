from retui.component import Component


def printLayout(item: Component, indent=0):
    print(
        f"{' '*indent}{item.name}#{item.props.get('id')} {item.getStyle('flex-direction')} {item.layout}"
    )
    for child in item.children:
        printLayout(child, indent + 2)

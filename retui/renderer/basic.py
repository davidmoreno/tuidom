from dataclasses import dataclass


@dataclass
class Point:
    x: int
    y: int


@dataclass
class Size:
    width: int
    height: int


@dataclass
class Rect:
    position: Point
    size: Size

    @property
    def x(self):
        return self.position.x

    @property
    def y(self):
        return self.position.y

    @property
    def width(self):
        return self.size.width

    @property
    def height(self):
        return self.size.height

    @property
    def top(self):
        "Top, min y"
        return self.position.y

    @property
    def bottom(self):
        "Bottom, max y, not included in rect"
        return self.position.y + self.size.height

    @property
    def left(self):
        "Left, min x"
        return self.position.x

    @property
    def right(self):
        "Top, max x, not included in rect"
        return self.position.x + self.size.width

    def point_inside(self, point: Point):
        return (self.left <= point.x < self.right) and (
            self.top <= point.y < self.bottom
        )

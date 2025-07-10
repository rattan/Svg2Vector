from abc import *
from typing import Self

import math
# The {@code Point2D} class defines a point representing a location
# in {@code (x,y)} coordinate space.
# <p>
# This class is only the abstract superclass for all objects that
# store a 2D coordinate.
# The actual storage representation of the coordinates is left to
# the subclass.
# @author      Jim Graham
# @since 1.2
class Point2D(metaclass = ABCMeta):
    @abstractmethod
    def getX(self) -> float:
        pass

    @abstractmethod
    def getY(self) -> float:
        pass

    @abstractmethod
    def setLocation(self, x: float, y: float):
        pass

    # Sets the location of this {@code Point2D} to the same
    # coordinates as the specified {@code Point2D} object.
    # @param p the specified {@code Point2D} to which to set
    # this {@code Point2D}
    # @since 1.2
    def setLocation(p: Self):
        self.setLocation(p.getX(), p.getY())

    # Returns the square of the distance between two points.
    # @param x1 the X coordinate of the first specified point
    # @param y1 the Y coordinate of the first specified point
    # @param x2 the X coordinate of the second specified point
    # @param y2 the Y coordinate of the second specified point
    # @return the square of the distance between the two
    # sets of specified coordinates.
    # @since 1.2
    @classmethod
    def distanceSq(cls, x1, y1, x2, y2) -> float:
        x1 -= x2
        y1 -= y2
        return x1 * x1 + y1 * y1

    # Returns the square of the distance from this
    # {@code Point2D} to a specified point.
    # @param px the X coordinate of the specified point to be measured
    #           against this {@code Point2D}
    # @param py the Y coordinate of the specified point to be measured
    #           against this {@code Point2D}
    # @return the square of the distance between this
    # {@code Point2D} and the specified point.
    # @since 1.2
    def distanceSq(self, px: float, py: float) -> float:
        px -= self.getX()
        py -= self.getY()
        return px * px + py * py

    # Returns the square of the distance from this
    # {@code Point2D} to a specified {@code Point2D}.
    # @param pt the specified point to be measured
    #           against this {@code Point2D}
    # @return the square of the distance between this
    # {@code Point2D} to a specified {@code Point2D}.
    # @since 1.2
    def distanceSq(self, pt: Self) -> float:
        px = pt.getX() - self.getX()
        py = pt.getY() - self.getY()
        return px * px + py * py

    # Returns the distance from this {@code Point2D} to
    # a specified point.
    # @param px the X coordinate of the specified point to be measured
    #           against this {@code Point2D}
    # @param py the Y coordinate of the specified point to be measured
    #           against this {@code Point2D}
    # @return the distance between this {@code Point2D}
    # and a specified point.
    # @since 1.2
    def distance(self, px: float, py: float) -> float:
        px -= self.getX()
        py -= self.getY()
        return math.sqrt(px * px + py * py)

    # The {@code Float} class defines a point specified in float
    # precision.
    # @since 1.2

class Point2DF(Point2D):
    # Constructs and initializes a {@code Point2D} with
    # the specified coordinates.
    # @param x the X coordinate of the newly
    #          constructed {@code Point2D}
    # @param y the Y coordinate of the newly
    #          constructed {@code Point2D}
    # @since 1.2
    def __init__(self, x: float = 0.0, y: float = 0.0):
        # The X coordinate of this {@code Point2D}.
        # @since 1.2
        # @serial
        self.x = x

        # The Y coordinate of this {@code Point2D}.
        # @since 1.2
        # @serial
        self.y = y

    # @since 1.2
    #/
    def getX(self) -> float:
        return self.x

    # @since 1.2
    def getY(self) -> float:
        return self.y

    # Sets the location of this {@code Point2D} to the
    # specified {@code float} coordinates.
    # @param x the new X coordinate of this {@code Point2D}
    # @param y the new Y coordinate of this {@code Point2D}
    # @since 1.2
    def setLocation(self, x: float, y: float):
        self.x = x
        self.y = y

    # Returns a {@code String} that represents the value
    # of this {@code Point2D}.
    # @return a string representation of this {@code Point2D}.
    # @since 1.2
    def toString(self) -> str:
        return f'Point2D.Float[{x}, {y}]'

    # @Serial
    # private static final long serialVersionUID = -2870572449815403710L;
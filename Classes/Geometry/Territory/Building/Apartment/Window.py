from shapely.geometry import LineString
class Window:
    def __init__(self, line: LineString):
        if not isinstance(line, LineString):
            raise TypeError("Expected a LineString object for the window.")
        self.line = line

    def length(self):
        return self.line.length

    def midpoint(self):
        return self.line.interpolate(0.5, normalized=True)
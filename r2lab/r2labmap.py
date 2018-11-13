"""
The R2labMap class is a convenience for mapping node numbers to a
2-dimensional grid coordinates, and backwards.
"""

class R2labMapGeneric:
    """
    The most general form allows to specifiy
    mapper functions in both directions.
    Or to simply specify an integer offset and boolean swap.
    """

# pylint: disable=c0326
    POSITIONS = [
        [1,  6, 11, 16,   19,   23,   26, 31, None],
        [2,  7, 12, None, 20,   None, 27, 32, None],
        [3,  8, 13, 17,   21,   24,   28, 33, None],
        [4,  9, 14, 18,   22,   25,   29, 34, 36],
        [5, 10, 15, None, None, None, 30, 35, 37]
    ]
# pylint: enable=c0326

    @staticmethod
    def _width():
        return len(R2labMapGeneric.POSITIONS[0])

    @staticmethod
    def _height():
        return len(R2labMapGeneric.POSITIONS)

    def __init__(self, *,
                 offset_x=0, offset_y=0,
                 swap_x=False, swap_y=False,
                 map_x=None, map_y=None):
        """
        By default, node 1 is on coordinates (0, 0),
        and node 37 is at (8, 4).
        The parameters allow to implement other mappings.

        Parameters:
          map_x(function): function that maps integers to integers;
            if provided, the `swap_x` and `offset_x` are ignored;
          swap_x(bool): if set, the x axis is reversed; that is,
            with only swap_x set, node 1 becomes (8, 0) and
            node 37 becomes (0, 4)
          offset_x(int): added in the X direction

        And likewise in the Y dimension.

        Examples:
          This means that typically map functions need be something
          like:
            * ``map_x = lambda x: x+1`` if you want to start numbering at 1
            * map_y = lambda y: 4-x if you want to have y go upwards
            * map_y = lambda y: 5-y for same direction but start at 1
        """
        # most general form if for you to provide the map function
        if map_x:
            self.map_x = map_x
        # otherwise you can provide swap_x and/or offset_x
        elif swap_x:
            self.map_x = lambda x: offset_x + self._width() - 1 - x
        else:
            self.map_x = lambda x: offset_x + x

        # same in y
        if map_y:
            self.map_y = map_y
        elif swap_y:
            self.map_y = lambda y: offset_y + self._height() - 1 - y
        else:
            self.map_y = lambda y: offset_y + y

        # computes a dictionary that maps
        # a node_id to a tuple of coords (x, y)
        self.node_to_position = {
            node_id: (self.map_x(x), self.map_y(y))
            for y, line in enumerate(self.POSITIONS)
            for x, node_id in enumerate(line)
            if node_id
        }

        # reverse dict (x, y) -> node
        self.position_to_node = {
            (self.map_x(x), self.map_y(y)): node_id
            for (node_id, (x, y)) in self.node_to_position.items()
        }

    def indexes(self):
        """
        Object that can be used to create a pandas index
        on the nodes; essentially this is range(1, 38)
        """
        return sorted(self.node_to_position.keys())

    def position(self, node):
        """
        Returns a (x, y) tuple that is the position of node <node>

        Parameters:
          node: a node number - may be an int or a str
        Returns:
          (int, int): a position on the grid
        """
        node = int(node)
        return self.node_to_position[node]

    def node(self, x, y):
        """
        Finds about the node at that position

        Parameters:
          x: coordinate along the horizontal axis - int or str
          y: coordinate along the vertical axis - int or str
        Returns:
          int: a node number, in the range (1..37) - or None
        """
        return self.position_to_node.get((x, y), None)

    def iterate_nodes(self):
        """
        An iterator that yields 37 tuples of the form
        (node_id, (x, y))
        """
        return self.node_to_position.items()

    def iterate_holes(self):
        """
        An iterator that yields tuples of the form (x, y) for all the
        possible (x, y) that do not match a node
        """
        for y, line in enumerate(self.POSITIONS):
            for x, node_id in enumerate(line):
                if not node_id:
                    yield self.map_x(x), self.map_y(y)

class R2labMap(R2labMapGeneric):
    """
    Inherits :class:`~r2lab.r2labmap.R2labMapGeneric`

    A map object where coordinates start at 1,
    and where the Y coordinate goes upwards;
    so typically in this map node 1 is at (1, 5)
    and node 37 is at (9, 1).
    """
    def __init__(self):
        super().__init__(offset_x=1, offset_y=1, swap_y=True)

"""
basic tool to translate node ids into positions on a grid

depending on the underlying visual tool,
several orientations / numberings may be needed

"""

class R2labMap:

# pylint: disable=c0326
    POSITIONS = [
        [1,  6, 11, 16,   19,   23,   26, 31, None],
        [2,  7, 12, None, 20,   None, 27, 32, None],
        [3,  8, 13, 17,   21,   24,   28, 33, None],
        [4,  9, 14, 18,   22,   25,   29, 34, 36],
        [5, 10, 15, None, None, None, 30, 35, 37]
    ]
# pylint: enable=c0326

    WIDTH = len(POSITIONS[0])
    HEIGHT = len(POSITIONS)

    def __init__(self, *,
                 offset_x = 0, offset_y = 0,
                 swap_x=False, swap_y=False):
        """
        typically map functions need be something like
        sx = lambda x: x+1 if you want to start numbering at 1
        sy = lambda y: 4-x if you want to have low y numbered under
        sy = lambda y: 5-x for same direction but start at 0
        to the lower row above
        """
        self.map_x = lambda x: offset_x + x
        # if swap_x =
        if swap_x:
            self.map_x = lambda x: offset_x + self.WIDTH - 1 - x
        self.map_y = lambda y: offset_y + y
        if swap_y:
            self.map_y = lambda y: offset_y + self.HEIGHT - 1 - y

        print("()")

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
        Something that can be used to create a pandas index on the nodes
        essentially this is range(1, 38)
        """
        return self.node_to_position.keys()

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
          int: a node number, in the range (1..37)
        """
        return self.position_to_node[(x, y)]

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

class BokehR2labMap(R2labMap):

    def __init__(self):
        super().__init__(swap_y=True, offset_y=True)

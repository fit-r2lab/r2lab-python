"""
    The R2lab dataframe, that is a standard DataFrame
for storing results on a node by node basis together with their
map coordinates
"""

from pandas import DataFrame

class MapDataFrame(DataFrame):
    """

    A R2lab MapDataFrame is a dataframe that has one line per node, together with
    their x and y coordinates has specified in the map object, plus additional
    columns as specified in the constructor. Is is indexed by node numbers.

    Parameter:
      map: a Map object that primarily gives the nodes coordinates
      columns: an dictionary - preferrably ordered if using an older Python -
        that specifies the column name (key) and the initial value (value)
    """

    def __init__(self, r2labmap, columns=None):
        # the map object essentially carries the coordinates
        # system that you wish to use
        # for weird reasons related to pandas implementation,
        # we can't seem to do this:
        # self.r2labmap = r2labmap
        # as it triggers infinite recursion (go figure...)
        # turns out we don't absolutely need this apparently,
        # do let's proceed this way for now
        if columns is None:
            columns = dict()
        # ditto
        # self.columns = columns
        all_columns = ['x', 'y'] + list(columns.keys())
        DataFrame.__init__(self,
                           index=r2labmap.indexes(),
                           columns=all_columns)
        for node_id, (gridx, gridy) in r2labmap.iterate_nodes():
            self.loc[node_id]['x'] = gridx
            self.loc[node_id]['y'] = gridy
            for column, value in columns.items():
                self.loc[node_id][column] = value

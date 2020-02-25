"""
Module hexgrid provides functions for working with a hexagonal settlers of catan grid.
This module uses a non-rotatable 2-d representation of the hex grid.
This is so that the resulting representation is denser and more efficient to perform convolutions on.
Adapted from module https://github.com/rosshamish/hexgrid/.
Edge and Node representation changed so that edges and nodes can be held in a single 2-d array with some null spaces to
the left and right of each tile.
"""
import logging

EDGE = 0
NODE = 1
TILE = 2

_tile_id_to_coord = {
    # 1-19 counter-clockwise starting from Top-Left
                1: (9, 3), 12: (13, 3), 11: (17, 3),
          2: (7, 5), 13: (11, 5), 18: (15, 5), 10: (19, 5),
    3: (5, 7), 14: (9, 7), 19: (13, 7), 17: (17, 7), 9: (21, 7),
          4: (7, 9), 15: (11, 9), 16: (15, 9), 8: (19, 9),
                5: (9, 11), 6: (13, 11), 7: (17, 11)
}

_tile_tile_offsets = {
    # tile_coord - tile_coord
    (-2, -2): 'NW',
    (-4, 0): 'W',
    (-2, 2): 'SW',
    (2, 2): 'SE',
    (4, 0): 'E',
    (2, -2): 'NE',
}

_tile_node_offsets = {
    # node_coord - tile_coord
    (0, -1): 'N',
    (-2, -1): 'NW',
    (-2, 1): 'SW',
    (0, 1): 'S',
    (2, 1): 'SE',
    (2, -1): 'NE',
}

_tile_edge_offsets = {
    # edge_coord - tile_coord
    (-1, -1): 'NW',
    (-2, 0): 'W',
    (-1, 1): 'SW',
    (1, 1): 'SE',
    (2, 0): 'E',
    (1, -1): 'NE',
}


def from_location(hexgrid_type, tile_id, direction=None):
    """
    :param hexgrid_type: hexgrid.TILE, hexgrid.NODE, hexgrid.EDGE
    :param tile_id: tile identifier, int
    :param direction: str
    :return: integer coordinate in this module's hexadecimal coordinate system
    """
    if hexgrid_type == TILE:
        if direction is not None:
            raise ValueError('tiles do not have a direction')
        return tile_id_to_coord(tile_id)
    elif hexgrid_type == NODE:
        return node_coord_in_direction(tile_id, direction)
    elif hexgrid_type == EDGE:
        return edge_coord_in_direction(tile_id, direction)
    else:
        logging.warning('unsupported hexgrid_type={}'.format(hexgrid_type))
        return None


def coastal_tile_ids():
    """
    Returns a list of tile identifiers which lie on the border of the grid.
    """
    return list(filter(lambda tid: len(coastal_edges(tid)) > 0, legal_tile_ids()))


def coastal_coords():
    """
    A coastal coord is a 2-tuple: (tile id, direction).
    An edge is coastal if it is on the grid's border.
    :return: list( (tile_id, direction) )
    """
    coast = list()
    for tile_id in coastal_tile_ids():
        tile_coord = tile_id_to_coord(tile_id)
        for edge_coord in coastal_edges(tile_id):
            dirn = tile_edge_offset_to_direction(edge_coord - tile_coord)
            if tile_id_in_direction(tile_id, dirn) is None:
                coast.append((tile_id, dirn))
    # logging.debug('coast={}'.format(coast))
    return coast


def coastal_edges(tile_id):
    """
    Returns a list of coastal edge coordinate.
    An edge is coastal if it is on the grid's border.
    :return: list(int)
    """
    edges = list()
    tile_coord = tile_id_to_coord(tile_id)
    for edge_coord in edges_touching_tile(tile_id):
        dirn = tile_edge_offset_to_direction(edge_coord - tile_coord)
        if tile_id_in_direction(tile_id, dirn) is None:
            edges.append(edge_coord)
    return edges


def tile_id_in_direction(from_tile_id, direction):
    """
    Variant on direction_to_tile. Returns None if there's no tile there.
    :param from_tile_id: tile identifier, int
    :param direction: str
    :return: tile identifier, int or None
    """
    coord_from = tile_id_to_coord(from_tile_id)
    for offset, dirn in _tile_tile_offsets.items():
        if dirn == direction:
            coord_to = coord_from + offset
            if coord_to in legal_tile_coords():
                return tile_id_from_coord(coord_to)
    return None


def direction_to_tile(from_tile_id, to_tile_id):
    """
    Convenience method wrapping tile_tile_offset_to_direction. Used to get the direction
    of the offset between two tiles. The tiles must be adjacent.
    :param from_tile_id: tile identifier, int
    :param to_tile_id: tile identifier, int
    :return: direction from from_tile to to_tile, str
    """
    coord_from = tile_id_to_coord(from_tile_id)
    coord_to = tile_id_to_coord(to_tile_id)
    direction = tile_tile_offset_to_direction(coord_to - coord_from)
    return direction


def tile_tile_offset_to_direction(offset):
    """
    Get the cardinal direction of a tile-tile offset. The tiles must be adjacent.
    :param offset: tile_coord - tile_coord, int
    :return: direction of the offset, str
    """
    try:
        return _tile_tile_offsets[offset]
    except KeyError:
        logging.critical('Attempted getting direction of non-existent tile-tile offset={:x}'.format(offset))
        return 'ZZ'


def tile_node_offset_to_direction(offset):
    """
    Get the cardinal direction of a tile-node offset. The tile and node must be adjacent.
    :param offset: node_coord - tile_coord, int
    :return: direction of the offset, str
    """
    try:
        return _tile_node_offsets[offset]
    except KeyError:
        logging.critical('Attempted getting direction of non-existent tile-node offset={:x}'.format(offset))
        return 'ZZ'


def tile_edge_offset_to_direction(offset):
    """
    Get the cardinal direction of a tile-edge offset. The tile and edge must be adjacent.
    :param offset: edge_coord - tile_coord, int
    :return: direction of the offset, str
    """
    try:
        return _tile_edge_offsets[offset]
    except KeyError:
        logging.critical('Attempted getting direction of non-existent tile-edge offset={:x}'.format(offset))
        return 'ZZ'


def edge_coord_in_direction(tile_id, direction):
    """
    Returns the edge coordinate in the given direction at the given tile identifier.
    :param tile_id: tile identifier, int
    :param direction: direction, str
    :return: edge coord, int
    """
    tile_coord = tile_id_to_coord(tile_id)
    for edge_coord in edges_touching_tile(tile_id):
        if tile_edge_offset_to_direction(edge_coord - tile_coord) == direction:
            return edge_coord
    raise ValueError('No edge found in direction={} at tile_id={}'.format(
        direction,
        tile_id
    ))


def node_coord_in_direction(tile_id, direction):
    """
    Returns the node coordinate in the given direction at the given tile identifier.
    :param tile_id: tile identifier, int
    :param direction: direction, str
    :return: node coord, int
    """
    tile_coord = tile_id_to_coord(tile_id)
    for node_coord in nodes_touching_tile(tile_id):
        if tile_node_offset_to_direction(node_coord - tile_coord) == direction:
            return node_coord
    raise ValueError('No node found in direction={} at tile_id={}'.format(
        direction,
        tile_id
    ))


def tile_id_to_coord(tile_id):
    """
    Convert a tile identifier to its corresponding grid coordinate.
    :param tile_id: tile identifier, Tile.tile_id
    :return: coordinate of the tile, int
    """
    try:
        return _tile_id_to_coord[tile_id]
    except KeyError:
        logging.critical('Attempted conversion of non-existent tile_id={}'.format(tile_id))
        return -1


def tile_id_from_coord(coord):
    """
    Convert a tile coordinate to its corresponding tile identifier.
    :param coord: coordinate of the tile, int
    :return: tile identifier, Tile.tile_id
    """
    for i, c in _tile_id_to_coord.items():
        if c == coord:
            return i
    raise Exception('Tile id lookup failed, coord={} not found in map'.format(hex(coord)))


def nearest_tile_to_edge(edge_coord):
    """
    Convenience method wrapping nearest_tile_to_edge_using_tiles. Looks at all tiles in legal_tile_ids().
    Returns a tile identifier.
    :param edge_coord: edge coordinate to find an adjacent tile to, int
    :return: tile identifier of an adjacent tile, Tile.tile_id
    """
    return nearest_tile_to_edge_using_tiles(legal_tile_ids(), edge_coord)


def nearest_tile_to_edge_using_tiles(tile_ids, edge_coord):
    """
    Get the first tile found adjacent to the given edge. Returns a tile identifier.
    :param tile_ids: tiles to look at for adjacency, list(Tile.tile_id)
    :param edge_coord: edge coordinate to find an adjacent tile to, int
    :return: tile identifier of an adjacent tile, Tile.tile_id
    """
    for tile_id in tile_ids:
        if edge_coord - tile_id_to_coord(tile_id) in _tile_edge_offsets.keys():
            return tile_id
    logging.critical('Did not find a tile touching edge={}'.format(edge_coord))


def nearest_tile_to_node(node_coord):
    """
    Convenience method wrapping nearest_tile_to_node_using_tiles. Looks at all tiles in legal_tile_ids().
    Returns a tile identifier.
    :param node_coord: node coordinate to find an adjacent tile to, int
    :return: tile identifier of an adjacent tile, Tile.tile_id
    """
    return nearest_tile_to_node_using_tiles(legal_tile_ids(), node_coord)


def nearest_tile_to_node_using_tiles(tile_ids, node_coord):
    """
    Get the first tile found adjacent to the given node. Returns a tile identifier.
    :param tile_ids: tiles to look at for adjacency, list(Tile.tile_id)
    :param node_coord: node coordinate to find an adjacent tile to, int
    :return: tile identifier of an adjacent tile, Tile.tile_id
    """
    for tile_id in tile_ids:
        if node_coord - tile_id_to_coord(tile_id) in _tile_node_offsets.keys():
            return tile_id
    logging.critical('Did not find a tile touching node={}'.format(node_coord))


def edges_touching_tile(tile_id):
    """
    Get a list of edge coordinates touching the given tile.
    :param tile_id: tile identifier, Tile.tile_id
    :return: list of edge coordinates touching the given tile, list(int)
    """
    coord = tile_id_to_coord(tile_id)
    edges = []
    for offset in _tile_edge_offsets.keys():
        edges.append(coord + offset)
    # logging.debug('tile_id={}, edges touching={}'.format(tile_id, edges))
    return edges


def nodes_touching_tile(tile_id):
    """
    Get a list of node coordinates touching the given tile.
    :param tile_id: tile identifier, Tile.tile_id
    :return: list of node coordinates touching the given tile, list(int)
    """
    coord = tile_id_to_coord(tile_id)
    nodes = []
    for offset in _tile_node_offsets.keys():
        nodes.append(coord + offset)
    # logging.debug('tile_id={}, nodes touching={}'.format(tile_id, nodes))
    return nodes


def nodes_touching_edge(edge_coord):
    """
    Returns the two node coordinates which are on the given edge coordinate.
    :return: list of 2 node coordinates which are on the given edge coordinate, list(int)
    """
    a, b = edge_coord
    if a % 2 == 0:
        return [(a + 1, b), (a - 1, b)]
    else:
        return [(a, b - 1), (a, b + 1)]


def legal_edge_coords():
    """
    Return all legal edge coordinates on the grid.
    """
    edges = set()
    for tile_id in legal_tile_ids():
        for edge in edges_touching_tile(tile_id):
            edges.add(edge)
    logging.debug('Legal edge coords({})={}'.format(len(edges), edges))
    return edges


def legal_node_coords():
    """
    Return all legal node coordinates on the grid
    """
    nodes = set()
    for tile_id in legal_tile_ids():
        for node in nodes_touching_tile(tile_id):
            nodes.add(node)
    logging.debug('Legal node coords({})={}'.format(len(nodes), nodes))
    return nodes


def legal_tile_ids():
    """
    Return all legal tile identifiers on the grid. In the range [1,19] inclusive.
    """
    return set(_tile_id_to_coord.keys())


def legal_tile_coords():
    """
    Return all legal tile coordinates on the grid
    """
    return set(_tile_id_to_coord.values())

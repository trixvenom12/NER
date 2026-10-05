import networkx as nx

from api.services.routing_engine import route_single


def test_route_geometry_falls_back_to_node_coords_when_edge_geometry_is_missing():
    G = nx.MultiDiGraph()
    G.add_node(1, lat=25.0, lon=91.0)
    G.add_node(2, lat=25.1, lon=91.1)
    G.add_edge(1, 2, segment_id=1, length=1000, speed_kph=40, road_ref='NH-6', highway='trunk')

    result = route_single(G, 1, 2, 'balanced', {1: {'score': 10.0, 'band': 'safe', 'factors': {}}})

    assert result['path_found'] is True
    assert result['geometry']['coordinates']
    assert result['geometry']['coordinates'][0] == [91.0, 25.0]
    assert result['geometry']['coordinates'][-1] == [91.1, 25.1]


if __name__ == '__main__':
    test_route_geometry_falls_back_to_node_coords_when_edge_geometry_is_missing()
    print('route_geometry test passed')

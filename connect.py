import numpy as np

GRAPH_COMPLETE       = 'Complete'
GRAPH_STAR           = 'Star'
GRAPH_BINARY_TREE    = 'BinaryTree'
GRAPH_N_ARY_TREE     = 'NAryTree'
GRAPH_CLUSTERS       = 'Clusters'
GRAPH_N_ARY_CLUSTERS = 'NAryClusters'

def complete_connected(hid1, hid2):
    return True

def star_connected(hid1, hid2, branch):
    if hid2 > hid1:
        temp = hid2
        hid2 = hid1
        hid1 = temp
    
    if hid2 == 0 and hid1 < branch:
        return True

    return np.abs(hid1-hid2) == branch

def binary_tree_connected(hid1, hid2):
    if hid1 > hid2:
        return (hid1 // 2)  == hid2
    else:
        return (hid2 // 2)  == hid1

def n_ary_tree_connected(hid1, hid2, n):
    if hid1 > hid2:
        return (hid1 // n) == hid2
    else:
        return (hid2 // n) == hid1

def cluster_connected(hid1, hid2, c):
    if hid1 < c and hid2 < c:
        return True
    else:
        return (hid1 % c) == (hid2 % c)

def n_ary_cluster_connected(hid1, hid2, n):
    if hid2 > hid1:
        temp = hid2
        hid2 = hid1
        hid1 = temp

    if hid1 < n:
        return True
    elif (hid1 // n) == (hid2 // n) or (hid1 // n)-1 == hid2:
        return True
    else:
        return False 




def parse_graph(graphcfg, name):  # {{{
    #logging.info('%s: %s', name, json.dumps(graphcfg))
    if graphcfg['class'] == GRAPH_COMPLETE:
        fn = lambda h1, h2: complete_connected(h1, h2)
    elif graphcfg['class'] == GRAPH_STAR:
        assert len(graphcfg['params']) == 1
        fn = lambda h1, h2: star_connected(h1, h2, graphcfg['params'][0])
    elif graphcfg['class'] == GRAPH_BINARY_TREE:
        #assert len(graphcfg['params']) == 1
        fn = lambda h1, h2: binary_tree_connected(h1,h2)
    elif graphcfg['class'] == GRAPH_N_ARY_TREE:
        assert len(graphcfg['params']) == 1
        fn = lambda h1, h2: n_ary_tree_connected(h1, h2, graphcfg['params'][0])
    elif graphcfg['class'] == GRAPH_CLUSTERS:
        assert len(graphcfg['params']) == 1
        fn = lambda h1, h2: cluster_connected(h1, h2, graphcfg['params'][0])
    elif graphcfg['class'] == GRAPH_N_ARY_CLUSTERS:
        assert len(graphcfg['params']) == 1
        fn = lambda h1, h2: n_ary_cluster_connected(h1, h2, graphcfg['params'][0])
    else:
        pass
        #logging.fatal('error passing distribution %s', json.dumps(graphcfg))
        #raise ValueError('error parsing distribution %s' % json.dumps(graphcfg))
    #average = sum(fn() for _ in range(1000))/1000.0
    #logging.debug('    1000 samples with average %f', average)
    return fn
# }}}
import numpy as np

GRAPH_COMPLETE       = 'Complete'
GRAPH_STAR           = 'Star'
GRAPH_STARING        = 'Staring'
GRAPH_BINARY_TREE    = 'BinaryTree'
GRAPH_N_ARY_TREE     = 'NAryTree'
GRAPH_CLUSTERS       = 'Clusters'
GRAPH_N_ARY_CLUSTERS = 'NAryClusters'
GRAPH_BIPARTITE      = 'Bipartite'
GRAPH_BIPARTITE_D    = 'BipartiteD'

def complete_connected(hid1, hid2):
    if hid1 == hid2:
        return False
    return True

def star_connected(hid1, hid2):
    if hid1 == hid2:
        return False
    if hid1 == 0 or hid1 == 1 or hid2 == 1:
        return True
    else:
        return False

def staring_connected(hid1, hid2, branch):
    if hid1 == hid2:
        return False
    if hid1 == 0:
        return True

    if hid2 > hid1:
        temp = hid2
        hid2 = hid1
        hid1 = temp
    
    if branch < 1:
        return False

    if hid2 == 1 and hid1 <= (branch+1):
        return True

    return (hid1-hid2) == branch

def binary_tree_connected(hid1, hid2):
    if hid1 == hid2:
        return False
    if hid1 == 0:
        return True

    if hid2 > hid1:
        temp = hid2
        hid2 = hid1
        hid1 = temp

    return (hid1 // 2)  == hid2

def n_ary_tree_connected(hid1, hid2, n):
    if hid1 == hid2:
        return False
    if hid1 == 0:
        return True

    if hid2 > hid1:
        temp = hid2
        hid2 = hid1
        hid1 = temp

    return ((hid1+n-2)//n == hid2)

def cluster_connected(hid1, hid2, c):
    if hid1 == hid2:
        return False
    if hid1 == 0:
        return True

    return ((hid1-1) % c) == ((hid2-1) % c)

def n_ary_cluster_connected(hid1, hid2, n):
    if hid1 == hid2:
        return False
    if hid1 == 0:
        return True

    if hid2 > hid1:
        temp = hid2
        hid2 = hid1
        hid1 = temp

    # if there are same parent or are parent and child
    if ((hid1+n-2)//n == hid2) or ((hid1+n-2)//n == (hid2+n-2)//n):
        return True
    else:
        return False

def bipartite(hid1, hid2):
    if (hid1 % 2) == (hid2 % 2):
        return False
    else:
        return True

def bipartite_d(hid1, hid2, d):
    if (hid1 % 2) == (hid2 % 2):
        return False
    else:
        if (hid2 % 2) == 1:
            aux = hid2
            hid2 = hid1
            hid1 = aux
        
        resp = False
        acc  = 0
        for i in range(d):
            
            if (hid1 + 1) + 2 * (acc) == hid2:
                return True

            if i % 2 == 0:
                acc = -1 * (acc + 1)
            else:
                acc = -1 * acc

def parse_graph(graphcfg, name):  # {{{
    #logging.info('%s: %s', name, json.dumps(graphcfg))
    if graphcfg['class'] == GRAPH_COMPLETE:
        fn = lambda h1, h2: complete_connected(h1, h2)
    elif graphcfg['class'] == GRAPH_STAR:
        fn = lambda h1, h2: star_connected(h1, h2)
    elif graphcfg['class'] == GRAPH_STARING:
        assert len(graphcfg['params']) == 1
        fn = lambda h1, h2: staring_connected(h1, h2, graphcfg['params'][0])
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
    elif graphcfg['class'] == GRAPH_BIPARTITE:
        #assert len(graphcfg['params']) == 1
        fn = lambda h1, h2: bipartite(h1, h2)
    elif graphcfg['class'] == GRAPH_BIPARTITE_D:
        assert len(graphcfg['params']) == 1
        fn = lambda h1, h2: bipartite_d(h1, h2, graphcfg['params'][0])
    else:
        pass
        #logging.fatal('error passing distribution %s', json.dumps(graphcfg))
        #raise ValueError('error parsing distribution %s' % json.dumps(graphcfg))
    #average = sum(fn() for _ in range(1000))/1000.0
    #logging.debug('    1000 samples with average %f', average)
    return fn
# }}}
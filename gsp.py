import json
from igraph import *
from convert import convert

# Calcul support for itemset of size 1
def calc_support_1(transactions, item):
    counter = 0
    in_trans = False

    for transaction in transactions:
        for sub_transaction in transaction:
            if item in sub_transaction:
                in_trans = True
        if in_trans:
            counter+=1
        in_trans = False
    
    return counter   

# Check if item is a sub sequence
def is_it_sub_seq(item):
    if type(item) is int:
        return False
    if len(item) == 1:
        return False
    for element in item:
        if type(element) is not int:
            return False
    return True

# Check if item is in transaction
def is_subseq_in_trans(item, transaction): 
    for sub_transaction in transaction:
        if set(item).issubset(set(sub_transaction)):
            return True 
    return False

# Calcul support for itemset of size n
def calc_support_n(transactions, item):
    counter = 0
    in_trans = True
    sub_item_in_trans = False

    for transaction in transactions:       
        last_i = 0
        for sub_item in item:   
            start_i = last_i
            sub_item_in_trans = False
            for i_sub_trans in range(start_i, len(transaction)):
                sub_trans = transaction[i_sub_trans]
                if sub_item_in_trans == False and set(sub_item).issubset(set(sub_trans)):
                    last_i = i_sub_trans + 1
                    sub_item_in_trans = True
            
            if sub_item_in_trans == False:
                in_trans = False
            sub_item_in_trans = False

        if in_trans:
            counter +=1
        in_trans = True

    return counter

# convert transaction to simple array
def trans_to_simple_array(transaction):
    array = []
    for item in transaction:
        if type(item) is int:
            array.append(item)
        else:
            for sub_item in item:
                array.append(sub_item)
    
    return array

# Merge source with candidate if it's possible
# return empty array if it's impossible
def can_we_merge(source, candidate):
    source_2to_n = trans_to_simple_array(source)
    del source_2to_n[0]

    candidate_1to_n_min1 = trans_to_simple_array(candidate)
    del candidate_1to_n_min1[-1]

    if source_2to_n == candidate_1to_n_min1:
        if is_it_sub_seq(candidate[-1]): #=> last of candidate in subsequence
                source[-1].append(candidate[-1][-1])
        else: #=> last of candidate not in subsequence
            source.append(candidate[-1])
        return source
    else:
        return []

# Find itemset we have to check for pruning
def candidate_for_pruning(item):
    candidates = []
    sizeItem = len(trans_to_simple_array(item))
    for removed_element in range(2, sizeItem):
        candidate = item.copy()
        element_before_removed = 0
        candidate_found = False
        i_sub_item = 0
        while candidate_found == False:
            sub_item = candidate[i_sub_item].copy()
            if len(sub_item) + element_before_removed < removed_element:
                element_before_removed += len(sub_item)
                i_sub_item += 1
            else:
                if len(sub_item) == 1:
                    candidate.remove(sub_item)
                else:
                    for element in sub_item:
                        element_before_removed += 1
                        if element_before_removed == removed_element:
                            sub_item.remove(element)
                            candidate[i_sub_item] = sub_item
                candidates.append(candidate.copy())
                candidate.clear()
                candidate_found = True
                
    return candidates

# Can we pruned this nex item
def can_we_prune(item, supports_prec):
    candidates = candidate_for_pruning(item)
    pruned = False

    i = 0
    while pruned == False  and i<len(candidates):
        if repr(candidates[i]) not in supports_prec:
            pruned = True
        i+=1

    return pruned

print("min_support ? ")
min_support = int(input())

print("Test dataset or default dataset ?")
datasetChoice = input("0 for test, 1 for default\n")
items = {}
itemNames = {}
transactions = []
if int(datasetChoice) == 0:
    # default items and transactions
    items = {1, 2, 3, 4, 5, 6, 7, 8}
    itemNames = {1:"1", 2:"2", 3:"3", 4:"4", 5:"5", 6:"6", 7:"7", 8:"8"}
    transactions = [
        [[2,3],[3],[4],[1,3]],
        [[2,6],[3,5],[2],[6,7]],
        [[1,8],[2,6],[1],[2],[6]],
        [[2,5],[3,5],[4]],
        [[1],[2,4],[2],[3],[2],[1,4,5]]
    ]
else:
    #[transactions,items,itemNames] = convert("dataset-500.csv", 60*60, 4*60*60, 0)
    [transactions,items,itemNames] = convert("dataset-25k.csv",4*60*60,16*60*60,60*60)

vertices = []
edges = []
root = []

results = {}
# calcul support for itemset of size 1
actual_supports = {}
id_root = 0
for item in items:
    support = calc_support_1(transactions, item)
    if support >= min_support:
        actual_supports[item] = support
        vertices.append(repr(item))
        root.append(id_root)
    id_root+=1

all_supports = {k: v for k, v in actual_supports.items()}
supports_prec = {k: v for k, v in actual_supports.items()}

results.update(actual_supports)
actual_supports.clear()

# generate and calcul support for itemset of size 2
for item_source in range(1, len(supports_prec)+1):
    for item_candidate in range(1, len(supports_prec)+1):

        # we generate the item like: ab
        new_item = [[item_source], [item_candidate]]
        support = calc_support_n(transactions, new_item)
        if support >= min_support:
            actual_supports[repr(new_item)] = support
            vertices.append(repr(new_item))
            edges.append((vertices.index(repr(item_source)), vertices.index(repr(new_item))))
            edges.append((vertices.index(repr(item_candidate)), vertices.index(repr(new_item))))

        # we generate the item like: (ab)
        if item_source < item_candidate:
            new_item = [[item_source, item_candidate]]
            support = calc_support_n(transactions, new_item)
            if support >= min_support:
                actual_supports[repr(new_item)] = support
                vertices.append(repr(new_item))
                edges.append((vertices.index(repr(item_source)), vertices.index(repr(new_item))))
                edges.append((vertices.index(repr(item_candidate)), vertices.index(repr(new_item))))

results.update(actual_supports)

# generate and calcul support for itemset of size n
while True:
    all_supports.update(actual_supports)
    supports_prec = {k: v for k, v in actual_supports.items()}
    actual_supports.clear()
    
    for item_source in supports_prec:
        for item_candidate in supports_prec:
            new_item = can_we_merge(json.loads(item_source), json.loads(item_candidate))
            if len(new_item):
                if can_we_prune(new_item, supports_prec) == False:
                    support = calc_support_n(transactions, new_item)
                    if support >= min_support:
                        actual_supports[repr(new_item)] = support
                        vertices.append(repr(new_item))
                        edges.append((vertices.index(item_source), vertices.index(repr(new_item))))
                        edges.append((vertices.index(item_candidate), vertices.index(repr(new_item))))

    
    results.update(actual_supports)
    if not actual_supports:
        break

vertices_with_support = []
for vertice in vertices:
    if vertice[0] != "[":
        vertices_with_support.append(vertice + "\n" + str(all_supports[int(vertice)]))
    else:
        vertices_with_support.append(vertice + "\n" + str(all_supports[vertice]))


# Output with big dataset
for seq in results:
    if not isinstance(seq, int):
        seq = eval(seq)
        toprint = "["
        for el in seq:
            toprint2 = "("
            if not isinstance(el, int):
                for el2 in el:
                    toprint2 = toprint2 + itemNames[el2] + ", "
                toprint2 = toprint2[:-2]
                toprint2 = toprint2 + "), "
                toprint = toprint + toprint2
            else:
                toprint = toprint + itemNames[el]
        toprint = toprint[:-2]
        toprint = toprint + "]"
        print(toprint)

                
    else:
        print(itemNames[seq])

if int(datasetChoice) == 0 and len(vertices_with_support) > 0:
    if len(edges) > 0:
        g = Graph(vertex_attrs={"label": vertices_with_support}, edges=edges, directed=True)
        plot(g,layout=g.layout('rt',root=root),bbox=(1600,900),vertex_label_dist=1.5,margin=50)
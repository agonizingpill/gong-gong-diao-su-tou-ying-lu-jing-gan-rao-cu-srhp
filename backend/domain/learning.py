from hashlib import sha256
import json
from math import exp

import numpy as np
from sklearn.cluster import SpectralClustering

def calculate(data):
    band, points, groups = data['band'], data['points'], data['clusters']
    points = sorted(points,key=lambda point:(point['y'],point['x']))
    by_position = {(point['x'],point['y']):i for i,point in enumerate(points)}
    affinity = np.eye(len(points))
    links = []
    for i,point in enumerate(points):
        for dx,dy in ((1,0),(0,1)):
            j = by_position.get((point['x']+dx,point['y']+dy))
            if j is None:
                continue
            other = points[j]
            difference = (point['shade']-other['shade'])**2+(point['spill']-other['spill'])**2
            weight = exp(-difference/.04)
            links.append((i,j,weight))
            affinity[i,j]=affinity[j,i]=weight
    raw = SpectralClustering(n_clusters=groups,affinity='precomputed',assign_labels='cluster_qr',
                             random_state=1096).fit_predict(affinity)
    relabel = {}
    for label in raw:
        relabel.setdefault(label,len(relabel)+1)
    labels = [relabel[label] for label in raw]
    cut = [(i,j,weight) for i,j,weight in links if labels[i]!=labels[j]]
    layout = [{key:point[key] for key in ('code','x','y','shade','spill','protected')} | {'cluster':label}
              for point,label in zip(points,labels)]
    evidence = {'plots':len(points),'grid':[band['cols'],band['rows']],'edges':len(links),'cut_edges':len(cut),
                'cut_weight_share':round(sum(w for _,_,w in cut)/sum(w for _,_,w in links),5),
                'seed':1096,'input_hash':sha256(json.dumps(data,sort_keys=True).encode()).hexdigest()}
    return {'algorithm':'SpectralClustering','clusters':len(relabel),'layout':layout,'evidence':evidence}

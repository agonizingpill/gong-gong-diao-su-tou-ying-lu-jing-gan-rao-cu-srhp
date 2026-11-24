from hashlib import sha256
import json
from math import exp

import numpy as np
from sklearn.cluster import SpectralClustering

SEED = 1096


def spectral_layout(band, points, groups):
    """对一组观测格按四邻接构图做谱聚类，返回带簇号的布局与切边统计。"""
    points = sorted(points, key=lambda point: (point['y'], point['x']))
    by_position = {(point['x'], point['y']): i for i, point in enumerate(points)}
    affinity = np.eye(len(points))
    links = []
    for i, point in enumerate(points):
        for dx, dy in ((1, 0), (0, 1)):
            j = by_position.get((point['x'] + dx, point['y'] + dy))
            if j is None:
                continue
            other = points[j]
            difference = (point['shade'] - other['shade']) ** 2 + (point['spill'] - other['spill']) ** 2
            weight = exp(-difference / .04)
            links.append((i, j, weight))
            affinity[i, j] = affinity[j, i] = weight
    raw = SpectralClustering(n_clusters=groups, affinity='precomputed', assign_labels='cluster_qr',
                             random_state=SEED).fit_predict(affinity)
    relabel = {}
    for label in raw:
        relabel.setdefault(label, len(relabel) + 1)
    labels = [relabel[label] for label in raw]
    cut = [(i, j, weight) for i, j, weight in links if labels[i] != labels[j]]
    return points, labels, links, cut


def calculate(data):
    band, points, groups = data['band'], data['points'], data['clusters']
    points, labels, links, cut = spectral_layout(band, points, groups)
    layout = [{key: point[key] for key in ('code', 'x', 'y', 'shade', 'spill', 'protected')} | {'cluster': label}
              for point, label in zip(points, labels)]
    evidence = {'plots': len(points), 'grid': [band['cols'], band['rows']], 'edges': len(links), 'cut_edges': len(cut),
                'cut_weight_share': round(sum(w for _, _, w in cut) / sum(w for _, _, w in links), 5),
                'seed': SEED, 'input_hash': sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()}
    return {'algorithm': 'SpectralClustering', 'clusters': len(set(labels)), 'layout': layout, 'evidence': evidence}


def calculate_trial(data):
    """单队试投网格的谱聚类。不含保护位，布局仅保留读数与簇号。"""
    band, points, groups, team = data['band'], data['points'], data['clusters'], data['team']
    points, labels, links, cut = spectral_layout(band, points, groups)
    layout = [{key: point[key] for key in ('code', 'x', 'y', 'shade', 'spill')} | {'cluster': label}
              for point, label in zip(points, labels)]
    evidence = {'team': team, 'plots': len(points), 'grid': [band['cols'], band['rows']],
                'edges': len(links), 'cut_edges': len(cut),
                'cut_weight_share': round(sum(w for _, _, w in cut) / sum(w for _, _, w in links), 5),
                'seed': SEED, 'input_hash': sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()}
    return {'algorithm': 'SpectralClustering', 'team': team, 'clusters': len(set(labels)),
            'layout': layout, 'evidence': evidence}


def calculate_job(data):
    """worker 入口：按任务类型分派。普通底图划分沿用旧结构，双队试投走 trial。"""
    if data.get('kind') == 'trial':
        return calculate_trial(data)
    return calculate(data)

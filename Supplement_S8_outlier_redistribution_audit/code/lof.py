"""LOF with exact k-distance neighborhoods (ties at the k-distance included), query point excluded."""
import numpy as np


def knn_graph(X, kmax, chunk=256, margin=40):
    """Exact sorted neighbor distances and indices (query excluded) for kmax + margin neighbors."""
    n = X.shape[0]
    m = min(n - 1, kmax + margin)
    sq = np.einsum("ij,ij->i", X, X)
    D_out = np.empty((n, m))
    I_out = np.empty((n, m), dtype=np.int64)
    for s in range(0, n, chunk):
        e = min(n, s + chunk)
        D = sq[s:e, None] + sq[None, :] - 2.0 * (X[s:e] @ X.T)
        D[np.arange(e - s), np.arange(s, e)] = np.inf
        idx = np.argpartition(D, m - 1, axis=1)[:, :m] if m < n - 1 else np.argsort(D, axis=1)[:, :m]
        diff = X[idx] - X[s:e, None, :]
        d = np.sqrt(np.einsum("ijk,ijk->ij", diff, diff))
        o = np.lexsort((idx, d), axis=1)
        D_out[s:e] = np.take_along_axis(d, o, 1)
        I_out[s:e] = np.take_along_axis(idx, o, 1)
    return D_out, I_out


def lof(D, I, k):
    """Breunig et al. LOF; the k-distance neighborhood includes all points tied with the k-th distance
    that lie inside the computed candidate list."""
    kdist = D[:, k - 1]
    n = D.shape[0]
    mask = D <= kdist[:, None]
    reach = np.maximum(D, kdist[I])
    with np.errstate(divide="ignore", invalid="ignore"):
        lrd = mask.sum(1) / np.where(mask, reach, 0.0).sum(1)
        ratio = np.where(mask, lrd[I], 0.0).sum(1) / mask.sum(1) / lrd
    return ratio

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script to generate synthetic data that follows a VAR process with a lag
"""

import numpy as np
from scipy.linalg import cholesky


#  Auxiliar Functions
def tcrossprod(A, B):
    # Matricial product A*t(B)
    return np.matmul(A, B.T)


def solve(A, b=None):
    # Solve linear problems: A*x = b. For b = None, it solves A*x = I
    if b is None:
        b = np.identity(len(A))
    return np.linalg.solve(A, b)


# -- Coefficients' random generation
def random_coef_VAR(n_lags, n_agents, ar_scale=5, sparse_proportion=0.5):
    # Tis function generates coefficients to simulate stationary VAR data.
    # Algorithm based on "Ansley C.F., Kohn R. 1986. A note on
    # reparameterizing a vector autoregressive moving average model to
    # enforce stationarity.
    assert ar_scale > 0
    Id = np.identity(n_agents)
    ini_coefs = np.zeros((n_agents, n_agents, n_lags))
    for i1 in range(n_lags):  # for each lag, generate coefficients
        np.random.seed(i1)
        A = np.random.normal(0, ar_scale, (n_agents, n_agents))
        # introduce sparsity
        grid = np.random.binomial(1, sparse_proportion,
                                  size=(n_agents, n_agents))
        A[grid == 1] = 0
        B = cholesky(Id + tcrossprod(A, A)).T
        ini_coefs[:, :, i1] = solve(B, A)
    all_phi = np.zeros((n_agents, n_agents, n_lags, n_lags))
    all_phi_star = np.zeros((n_agents, n_agents, n_lags, n_lags))

    # Set initial values
    L = L_star = Sigma = Sigma_star = Id

    # Recursion algorithm (Ansley and Kohn 1986, lemma 2.1)
    for s in range(-1, n_lags - 1):
        all_phi[:, :, s + 1, s + 1] = np.matmul(
            np.matmul(L, ini_coefs[:, :, s + 1]), solve(L_star))
        all_phi_star[:, :, s + 1, s + 1] = np.matmul(
            tcrossprod(L_star, ini_coefs[:, :, s + 1]), solve(L))

        if s >= 0:
            for k in range(s + 1):
                all_phi[:, :, s + 1, k] = all_phi[:, :, s, k] - np.matmul(all_phi[:, :, s + 1, s + 1], all_phi_star[:, :, s, s - k])  # noqa
                all_phi_star[:, :, s + 1, k] = all_phi_star[:, :, s,k] - np.matmul(all_phi_star[:, :, s + 1, s + 1], all_phi[:, :, s, s - k])  # noqa

        # These are not needed in the last round because only coefficient
        # matrices will be returned.
        if s < n_lags - 2:
            Sigma_next = Sigma - np.matmul(all_phi[:, :, s + 1, s + 1], tcrossprod(Sigma_star, all_phi[:, :, s + 1, s + 1]))  # noqa
            if s - 1 < n_lags + 1:
                Sigma_star = Sigma_star - np.matmul(
                    all_phi_star[:, :, s + 1, s + 1],
                    tcrossprod(Sigma, all_phi_star[:, :, s + 1, s + 1]))
                L_star = cholesky(Sigma_star).T
            Sigma = Sigma_next
            L = cholesky(Sigma).T
    coefs_var = all_phi[:, :, -1].flatten(order='F').reshape(
        (n_agents, n_lags * n_agents)).T
    return coefs_var

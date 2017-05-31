#!/usr/bin/env python
# -*- coding: utf-8 -*-

# #########################################################################
# Copyright (c) 2016, UChicago Argonne, LLC. All rights reserved.         #
#                                                                         #
# Copyright 2016. UChicago Argonne, LLC. This software was produced       #
# under U.S. Government contract DE-AC02-06CH11357 for Argonne National   #
# Laboratory (ANL), which is operated by UChicago Argonne, LLC for the    #
# U.S. Department of Energy. The U.S. Government has rights to use,       #
# reproduce, and distribute this software.  NEITHER THE GOVERNMENT NOR    #
# UChicago Argonne, LLC MAKES ANY WARRANTY, EXPRESS OR IMPLIED, OR        #
# ASSUMES ANY LIABILITY FOR THE USE OF THIS SOFTWARE.  If software is     #
# modified to produce derivative works, such modified software should     #
# be clearly marked, so as not to confuse it with the version available   #
# from ANL.                                                               #
#                                                                         #
# Additionally, redistribution and use in source and binary forms, with   #
# or without modification, are permitted provided that the following      #
# conditions are met:                                                     #
#                                                                         #
#     * Redistributions of source code must retain the above copyright    #
#       notice, this list of conditions and the following disclaimer.     #
#                                                                         #
#     * Redistributions in binary form must reproduce the above copyright #
#       notice, this list of conditions and the following disclaimer in   #
#       the documentation and/or other materials provided with the        #
#       distribution.                                                     #
#                                                                         #
#     * Neither the name of UChicago Argonne, LLC, Argonne National       #
#       Laboratory, ANL, the U.S. Government, nor the names of its        #
#       contributors may be used to endorse or promote products derived   #
#       from this software without specific prior written permission.     #
#                                                                         #
# THIS SOFTWARE IS PROVIDED BY UChicago Argonne, LLC AND CONTRIBUTORS     #
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT       #
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS       #
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL UChicago     #
# Argonne, LLC OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,        #
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,    #
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;        #
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER        #
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT      #
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN       #
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE         #
# POSSIBILITY OF SUCH DAMAGE.                                             #
# #########################################################################

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import time
import sys

import numpy as np
import scipy.ndimage
import logging
import warnings
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from xdesign.grid import *
from xdesign.util import gen_mesh
from numpy.fft import fft2, fftn, ifftn, fftshift, ifftshift

logger = logging.getLogger(__name__)


__author__ = "Daniel Ching, Doga Gursoy"
__copyright__ = "Copyright (c) 2016, UChicago Argonne, LLC."
__docformat__ = 'restructuredtext en'
__all__ = ['multislice_propagate',
           'plot_wavefront',
           'initialize_wavefront']





def initialize_wavefront(grid, type, **kwargs):
    """Initialize wavefront.

    Parameters:
    -----------
    wvfnt_width : int
        Pixel width of wavefront.
    """
    wave_shape = grid.grid_delta.shape[1:]
    if type == 'plane':
        wavefront = np.ones(wave_shape).astype('complex64')
    elif type == 'point':
        wid = kwargs['width']
        wavefront = np.zeros(wave_shape).astype('complex64')
        center = int(wave_shape / 2)
        radius = int(wid / 2)
        wavefront[:wid] = 1.
        wavefront = np.roll(wavefront, int((wave_shape - wid) / 2))
    elif type == 'point_projection_lens':
        f = kwargs['focal_length']
        s = kwargs['lens_sample_dist']
        xx = grid.xx[0, :, :]
        yy = grid.yy[0, :, :]
        r = np.sqrt(xx ** 2 + yy ** 2)
        dxchange.write_tiff(r, 'tmp/r', dtype=np.float32, overwrite=True)
        dxchange.write_tiff(np.mod(r, 1), 'tmp/shit', dtype=np.float32, overwrite=True)

        theta = np.arctan(r / (s - f))
        dxchange.write_tiff(theta, 'tmp/theta', dtype=np.float32, overwrite=True)
        path = np.mod(s / np.cos(theta), grid.lmbda_nm)
        dxchange.write_tiff(path, 'tmp/path', dtype=np.float32, overwrite=True)
        phase = path * 2 * np.pi
        dxchange.write_tiff(phase, 'tmp/phase', dtype=np.float32, overwrite=True)
        wavefront = np.ones(wave_shape).astype('complex64')
        wavefront = wavefront + 1j * np.tan(phase)
        wavefront = wavefront / np.abs(wavefront)

    return wavefront


def _extract_slice(delta_grid, beta_grid, islice):
    """Extract a specified slice from the grid.

    Parameters:
    -----------
    delta_grid : ndarray
        As-constructed grid with defined phantoms filled with material delta values.
    beta_grid : ndarray
        As-constructed grid with defined phantoms filled with material beta values.
    islice : int
        Index of slice to be extracted.
    """
    pass


def slice_modify(grid, delta_slice, beta_slice, wavefront):
    """Modify wavefront within a slice.

    Parameters:
    -----------
    delta_slice : ndarray
        Extracted slice filled with material delta values.
    beta_slice : ndarray
        Extracted slice filled with material beta values.
    wavefront : ndarray
        Wavefront.
    delta_nm : float
        Slice thickness in nm.
    lmda : float
        Wavelength in nm.
    """
    delta_nm = grid.voxel_z
    kz = 2 * np.pi * delta_nm / grid.lmbda_nm
    wavefront = wavefront * np.exp((kz * delta_slice) * 1j) * np.exp(-kz * beta_slice)

    return wavefront


def slice_propagate(grid, wavefront):

    delta_nm = grid.voxel_z
    wavefront = free_propagate(grid, wavefront, delta_nm)
    return wavefront


def free_propagate(grid, wavefront, dist_nm):
    """Free space propagation using convolutional algorithm.
    """
    lmbda_nm = grid.lmbda_nm
    u_max = 1. / (2. * grid.voxel_x)
    v_max = 1. / (2. * grid.voxel_y)
    u, v = gen_mesh([v_max, u_max], grid.grid_delta.shape[1:3])
    # x = grid.xx[0, :, :]
    # y = grid.yy[0, :, :]
    # h = np.exp(-1j * np.pi / (lmbda_nm * dist_nm) * (x ** 2 + y ** 2))
    # H = fftshift(fft2(h))
    # H = np.exp(-1j * 2 * np.pi * dist_nm / lmbda_nm * np.sqrt(1. - lmbda_nm ** 2 * u ** 2 - lmbda_nm ** 2 * v ** 2))
    H = np.exp(-1j * np.pi * dist_nm * lmbda_nm * (u ** 2 + v ** 2))
    # print(1)
    # x = grid.xx[0, :, :]
    # y = grid.yy[0, :, :]
    # print(u)
    # print(v)
    # h = np.exp(-1j * np.pi / (lmbda_nm * dist_nm) * (x ** 2 + y ** 2))
    # H2 = fftshift(fftn(h))
    # print(2)
    # plt.figure()
    # plt.imshow(np.abs(H))
    # plt.figure()
    # plt.imshow(np.abs(H2))
    # plt.show()

    # time.sleep(999)

    wavefront = ifftn(ifftshift(fftshift(fftn(wavefront)) * H))
    # H = np.exp(-1j * 2 * np.pi * delta_nm / lmda_nm * np.sqrt(1. - lmda_nm ** 2 * u ** 2))
    # wavefront = np.fft.ifftn(np.fft.fftn(wavefront) * np.fft.fftshift(H))
    return wavefront


def far_propagate(grid, wavefront, dist_nm):
    """Free space propagation using product Fourier algorithm. Suitable for far field propagation.
    """
    assert isinstance(grid, Grid3d)
    lmbda_nm = grid.lmbda_nm
    u_max = 1. / (2. * grid.voxel_x)
    v_max = 1. / (2. * grid.voxel_y)
    u, v = gen_mesh([v_max, u_max], grid.grid_delta.shape[1:3])
    x = grid.xx[0, :, :] * grid.voxel_x
    y = grid.yy[0, :, :] * grid.voxel_y
    x_max = grid.size[0] * grid.voxel_x
    y_max = grid.size[1] * grid.voxel_y
    # h = np.exp(-1j * 2 * np.pi / lmbda_nm * np.sqrt(dist_nm ** 2 + x ** 2 + y ** 2))
    # wavefront = fftshift(fft2(wavefront * h))
    # wavefront = wavefront * \
    #             np.exp(-1j * dist_nm / lmbda_nm * np.sqrt(4 * np.pi ** 2 + lmbda_nm ** 2 * (u ** 2 + v ** 2))) * \
    #             4 * np.pi / (x_max ** 2 + y_max ** 2) / (lmbda_nm * dist_nm) * 1j

    h = np.exp(-1j * np.pi * (x ** 2 + y ** 2) / (lmbda_nm * dist_nm))
    wavefront = fftshift(fft2(wavefront * h))
    wavefront = wavefront * np.exp(-1j * np.pi * lmbda_nm * dist_nm * (u ** 2 + v ** 2))
    wavefront = wavefront * 1j / (lmbda_nm * dist_nm)

    print(u)
    print(lmbda_nm, dist_nm)
    print(u * lmbda_nm * dist_nm)

    # y0 = grid.yy[0, :, :]
    # x0 = grid.xx[0, :, :]
    # y = y0 * (lmda * z) * (grid.size[1] * grid.voxel_y) ** 2
    # x = x0 * (lmda * z) * (grid.size[0] * grid.voxel_x) ** 2
    # wavefront = fftshift(fftn(wavefront * np.exp(-1j * 2 * np.pi / lmda * np.sqrt(z ** 2 + x0 ** 2 + y0 ** 2))))
    # wavefront = wavefront * np.exp(-1j * 2 * np.pi / lmda * np.sqrt(z ** 2 + x ** 2 + y ** 2))
    return wavefront


def _far_propagate_2(grid, wavefront, lmd, z_um):
    """Free space propagation using product Fourier algorithm.
    """
    assert isinstance(grid, Grid3d)

    N = grid.size[1]
    M = grid.size[2]
    D = N * grid.voxel_y
    H = M * grid.voxel_x
    f1 = wavefront

    V = N/D
    U = M/H
    d = np.arange(-(N-1)/2,(N-1)/2+1,1)*D/N
    h = np.arange(-(M-1)/2,(M-1)/2+1,1)*H/M
    v = np.arange(-(N-1)/2,(N-1)/2+1,1)*V/N
    u = np.arange(-(M-1)/2,(M-1)/2+1,1)*U/M

    f2 = np.fft.fftshift(np.fft.fft2(f1*np.exp(-1j*2*np.pi/lmd*np.sqrt(z_um**2+d**2+h[:,np.newaxis]**2))))*np.exp(-1j*2*np.pi*z_um/lmd*np.sqrt(1.+lmd**2*(v**2+u[:,np.newaxis]**2)))/U/V/(lmd*z_um)*(-np.sqrt(1j))
    d2,h2=v*lmd*z_um,u*lmd*z_um
    return f2


def plot_wavefront(wavefront, grid, save_folder='simulation', fname='exiting_wave'):
    """Plot wavefront intensity.

    Parameters:
    -----------
    wavefront : ndarray
        Complex wavefront.
    lat_nm : float
        Lateral pixel length in nm.
    """
    i = np.abs(wavefront * np.conjugate(wavefront))

    fig = plt.figure(figsize=[9, 9])
    plt.imshow(np.log(i), cmap='gray')
    plt.xlabel('x (nm)')
    plt.ylabel('y (nm)')
    plt.show()
    #fig.savefig(save_folder+'/'+fname+'.png', type='png')


def multislice_propagate(grid, wavefront, free_prop_dist=None):
    """Do multislice propagation for wave with specified properties in the constructed grid.

    Parameters:
    -----------
    delta_grid : ndarray
        As-constructed grid with defined phantoms filled with material delta values.
    beta_grid : ndarray
        As-constructed grid with defined phantoms filled with material beta values.
    probe : instance
        Probe beam instance.
    delta_nm : float
        Slice thickness in nm.
    lat_nm : float
        Lateral pixel size in nm.
    """
    # 2d array should be reshaped to 3d.
    assert isinstance(grid, Grid3d)
    delta_grid = grid.grid_delta
    beta_grid = grid.grid_beta

    n_slice = delta_grid.shape[0]
    for i_slice in range(n_slice):
        print('\rSlice: {:d}'.format(i_slice), end=' ')
        sys.stdout.flush()
        delta_slice = delta_grid[i_slice, :, :]
        beta_slice = beta_grid[i_slice, :, :]
        wavefront = slice_modify(grid, delta_slice, beta_slice, wavefront)
        wavefront = slice_propagate(grid, wavefront)
    # print(wavefront)
    if free_prop_dist is not None:
        # wavefront = free_propagate(grid, wavefront, free_prop_dist)
        wavefront = far_propagate(grid, wavefront, free_prop_dist)
    # print(wavefront)
    return wavefront
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

import numpy as np
import scipy.ndimage
import logging
import warnings
import matplotlib.pyplot as plt

logger = logging.getLogger(__name__)


__author__ = "Daniel Ching, Doga Gursoy"
__copyright__ = "Copyright (c) 2016, UChicago Argonne, LLC."
__docformat__ = 'restructuredtext en'
__all__ = ['multislice_propagate',
           'plot_wavefront']


def _gen_mesh(lengths, shape):
    """Generate mesh grid.

    Parameters:
    -----------
    lengths : ndarray
        Half-lengths of axes in nm or nm^-1.
    shape : ndarray
        Number of pixels in each dimension.
    """
    dim = len(lengths)
    axes = np.array([np.linspace(-lengths[0], lengths[0], shape[0])])
    for i in range(1, dim):
        np.append(axes, np.linspace(-lengths[i], lengths[i], shape[i]), axis=0)
    res = np.meshgrid(*axes)
    return res


def initialize_wavefront(wvfnt_width, **kwargs):
    """Initialize wavefront.

    Parameters:
    -----------
    wvfnt_width : int
        Pixel width of wavefront.
    """
    type = kwargs['type']
    if type == 'plane':
        wavefront = np.ones(wvfnt_width).astype('complex64')
    if type == 'point':
        wid = kwargs['width']
        wavefront = np.zeros(wvfnt_width).astype('complex64')
        center = int(wvfnt_width / 2)
        radius = int(wid / 2)
        wavefront[:wid] = 1.
        wavefront = np.roll(wavefront, int((wvfnt_width - wid) / 2))
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


def _slice_modify(delta_slice, beta_slice, wavefront, delta_nm, lmda):
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
    kz = 2 * np.pi * delta_nm / lmda
    wavefront = wavefront * np.exp((kz * delta_slice) * 1j) * np.exp(-kz * beta_slice)

    return wavefront


def _slice_propagate(wavefront, delta_nm, lat_nm, wvfnt_width, lmda):
    """Free space propagation.

    Parameters:
    -----------
    wavefront : ndarray
        Wavefront.
    delta_nm : float
        Slice thickness in nm.
    lat_nm : float
        Lateral pixel length in nm.
    wvfnt_width : int
        Pixel width of wavefront.
    lmda : float
        Wavelength in nm.
    """
    u_max = 1. / (2. * lat_nm)
    u = _gen_mesh([u_max], [wvfnt_width])
    u = u[0]
    H = np.exp(-1j * 2 * np.pi * delta_nm / lmda * np.sqrt(1. - lmda ** 2 * u ** 2))
    wavefront = np.fft.ifftn(np.fft.ifftshift(np.fft.fftshift(np.fft.fftn(wavefront)) * H))
    # H = np.exp(-1j * 2 * np.pi * delta_nm / lmda * np.sqrt(1. - lmda ** 2 * u ** 2))
    # wavefront = np.fft.ifftn(np.fft.fftn(wavefront) * np.fft.fftshift(H))
    return wavefront


def plot_wavefront(wavefront, lat_nm, save_folder, fname):
    """Plot wavefront intensity.

    Parameters:
    -----------
    wavefront : ndarray
        Complex wavefront.
    lat_nm : float
        Lateral pixel length in nm.
    """
    i = wavefront * np.conjugate(wavefront)
    shape = len(wavefront)
    half_len = lat_nm * shape / 2
    x = np.linspace(-half_len, half_len, shape)
    fig = plt.figure(figsize=[9, 5])
    plt.plot(x, i)
    plt.xlabel('Position (nm)')
    plt.ylabel('Intensity')
    plt.show()
    fig.savefig(save_folder+'/'+fname+'.png', type='png')


def multislice_propagate(delta_grid, beta_grid, probe, delta_nm, lat_nm, wavefront):
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
    field_shape = delta_grid.shape
    # wavelength in nm
    lmda = probe.wavelength
    # I assume Probe class has an attribute wavelength. E.g.:
    # class Probe:
    #     def __init__(self, energy):
    #         self.energy = energy
    #         self.wavelength = 1.23984/energy
    n_slice = delta_grid.shape[0]
    for i_slice in range(n_slice):
        delta_slice = delta_grid[i_slice, :]
        beta_slice = beta_grid[i_slice, :]
        wavefront = _slice_modify(delta_slice, beta_slice, wavefront, delta_nm, lmda)
        wavefront = _slice_propagate(wavefront, delta_nm, lat_nm, len(delta_slice), lmda)

    return wavefront
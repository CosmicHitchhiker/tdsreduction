#! /usr/bin/env python3

import numpy as np
from matplotlib import pyplot as plt
from matplotlib.patches import Polygon
from astropy.coordinates import Angle
from astropy import units as u
from astropy.io import fits
from astropy.wcs import WCS


class mySlit(Polygon):
    """
    Create a patch representing a latitude-longitude quadrangle rotated by
    given angle.

    See astropy.visualization.wcsaxes.Quadrangle for details.

    Parameters
    ----------
    anchor : tuple or `~astropy.units.Quantity` ['angle']
        Center of slit.
        This can be either a tuple of two `~astropy.units.Quantity` objects, or
        a single `~astropy.units.Quantity` array with two elements.
    width : `~astropy.units.Quantity` ['angle'], default=1.5*u.arcsec
        The width of the slit.
    height : `~astropy.units.Quantity` ['angle'], default=3*u.arcmin
        The lenght of the slit.
    theta : `~astropy.units.Quantity` ['angle'], default=0*u.deg
        PA of the slit.
    resolution : int, optional
        The number of points that make up each side of the quadrangle -
        increase this to get a smoother quadrangle.
    vertex_unit : `~astropy.units.Unit` ['angle'], default=u.deg
        The units in which the resulting polygon should be defined - this
        should match the unit that the transformation (e.g. the WCS
        transformation) expects as input.

    Notes
    -----
    Additional keyword arguments are passed to `~matplotlib.patches.Polygon`
    """

    def __init__(self, anchor, width=1.5*u.arcsec, height=3*u.arcmin,
                 theta=0*u.deg, resolution=100, vertex_unit=u.deg, **kwargs):

        # Extract longitude/latitude, either from a tuple of two quantities, or
        # a single 2-element Quantity.
        lon_c, lat_c = u.Quantity(anchor).to_value(vertex_unit)
        center = np.array([[lon_c, lat_c]])

        theta = u.Quantity(theta).to_value(u.rad)

        # Convert the quadrangle dimensions to the appropriate units
        width = width.to_value(vertex_unit)
        height = height.to_value(vertex_unit)

        # Corner coordinates
        longitude = lon_c - width * 0.5
        latitude = lat_c - height * 0.5

        # Create progressions in longitude and latitude
        lon_seq = longitude + np.linspace(0, width, resolution + 1)
        lat_seq = latitude + np.linspace(0, height, resolution + 1)

        # Trace the path of the quadrangle
        lon = np.concatenate([lon_seq[:-1],
                              np.repeat(lon_seq[-1], resolution),
                              np.flip(lon_seq[1:]),
                              np.repeat(lon_seq[0], resolution)])
        lat = np.concatenate([np.repeat(lat_seq[0], resolution),
                              lat_seq[:-1],
                              np.repeat(lat_seq[-1], resolution),
                              np.flip(lat_seq[1:])])

        # Create polygon vertices
        vertices = np.array([lon, lat])

        # Rotation matrix
        rot_matrix = np.array([[np.cos(theta), np.sin(theta)],
                               [-np.sin(theta), np.cos(theta)]])

        # Rotate Quadrangle
        vertices = vertices - center.T
        vertices = rot_matrix @ vertices
        vertices = vertices + center.T
        vertices = vertices.T

        super().__init__(vertices, **kwargs)


def main(args=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('image',
                        help='''fits file with object image and
                                valid WCS keys in header''')
    parser.add_argument('spectrum',
                        help='''fits file with object spectrum and
                                valid poosition keys in header''')
    parser.add_argument('--ra-corr', type=float, default=0.0,
                        help='''right acession correction for the center
                        of the slit in arcsec''')
    parser.add_argument('--dec-corr', type=float, default=0.0,
                        help='''declination correction for the center
                        of the slit in arcsec''')
    pargs = parser.parse_args(args[1:])

    print(pargs.image)
    image = fits.open(pargs.image)[0]
    wcs = WCS(image.header)
    hdr = fits.getheader(pargs.spectrum)

    radec_slit = [Angle(hdr['RA'] + ' hours'), Angle(hdr['DEC'] + ' degrees')]
    radec_slit[1] += pargs.ra_corr*u.arcsec
    radec_slit[0] += pargs.dec_corr*u.arcsec

    ax = plt.subplot(projection=wcs)
    ax.set_title(hdr['OBJECT'])
    ax.imshow(image.data, cmap='bone')

    # plt.grid(color='white', ls='solid')

    PA = hdr['POSANG']
    s = mySlit(radec_slit, 1.0*u.arcsec, 3.0*u.arcmin, theta=PA*u.deg,
               edgecolor='tab:olive', facecolor='none', lw='0.5',
               transform=ax.get_transform('icrs'))
    ax.add_patch(s)
    c = mySlit(radec_slit, 0.1*u.arcsec, 0.1*u.arcmin, theta=(PA+90)*u.deg,
               edgecolor='red', facecolor='none',
               transform=ax.get_transform('icrs'))
    ax.add_patch(c)
    plt.show()
    return 0


if __name__ == '__main__':
    import sys
    import argparse
    sys.exit(main(sys.argv))
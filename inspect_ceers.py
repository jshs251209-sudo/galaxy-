import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
from astropy.io import fits
import pandas as pd
import numpy as np

with fits.open('ceers_cat_v1.0.fits') as hdul:
    hdr = hdul[1].header
    data = hdul[1].data
    
    print("=== Header information for key columns ===")
    cols_to_check = ['STAR_FLAG', 'BAD_REGION_FLAG', 'A_IMAGE', 'B_IMAGE', 'KRON_RADIUS', 
                     'F150W_FLUX_RADIUS', 'F200W_FLUX_RADIUS', 'F444W_FLUX_RADIUS',
                     'LP_Z_BEST', 'LP_Z_MED', 'LP_MASS_BEST', 'LP_MASS_MED', 'DB_MASS', 'CI_MASS']
    for key in cols_to_check:
        for card in hdr.cards:
            if card.keyword.startswith('TTYPE') and card.value == key:
                num = card.keyword[5:]
                unit = hdr.get('TUNIT' + num, 'No unit')
                print(f"Col {key:>20} (Col #{num:>3}): Unit={unit:<15}")
    
    print("\n=== Statistics across all 87,345 rows ===")
    for key in cols_to_check:
        arr = np.array(data[key])
        finite = np.isfinite(arr)
        # also check for fill values like -99 or <= 0
        valid = finite & (arr > -90)
        print(f"  {key:>20}: Finite={finite.sum():>6} ({finite.sum()/len(arr)*100:5.1f}%), Valid(>-90)={valid.sum():>6} ({valid.sum()/len(arr)*100:5.1f}%), Min={arr[valid].min() if valid.any() else np.nan:.3f}, Max={arr[valid].max() if valid.any() else np.nan:.3f}, Median={np.median(arr[valid]) if valid.any() else np.nan:.3f}")

    # Check pixel scale of CEERS NIRCam detection image
    # usually 0.031 arcsec/pixel for short wavelength or 0.03 arcsec/pixel (resampled mosaic)
    print("\n=== Detection image pixel scale check ===")
    for card in hdr.cards:
        if any(term in card.keyword.upper() for term in ['PIX', 'SCALE', 'WCS', 'RESOL']):
            print(f"  {card.keyword}: {card.value} / {card.comment}")

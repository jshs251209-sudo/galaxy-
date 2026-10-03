"""
스펙트럼 추출, 파장 교정, 방출선 피팅 및 가상 스펙트럼 생성을 위한 핵심 엔진 모듈입니다.
UI (Streamlit 등) 독립적으로 작동하며 순수 연산 함수를 제공합니다.

v3 강화 사항
- 방출선 12종 (Balmer, [OII], [OIII], [NII], [SII], HeI) + 흡수선 목록
- Hα+[NII] / [SII] 이중선 블렌드 동시 피팅 (다중 가우시안 deblending)
- 강건한 잡음 추정 (MAD), 스펙트럼 길이에 비례하는 연속선 창 크기
- 등가폭(EW, SDSS 부호 규약: 방출 = 음수), 선별 S/N, 플럭스 오차
- D4000 (Balogh 1999 narrow) 지수
- 적색편이 자동 추정 (방출선 패턴 매칭)
- 2점/다점 다항식 파장 교정, FITS 헤더(CRVAL/CDELT/CRPIX) 파장해
- 모의 스펙트럼 + 모의 '분광 사진' 이미지 생성 (ROI 기능 시연용)
"""

import warnings
import numpy as np
import pandas as pd
from scipy import signal, optimize, ndimage
from PIL import Image


# ═══════════════════════════════════════════════════════
#                     선 목록
# ═══════════════════════════════════════════════════════
LINE_LIST = {
    # name: (rest wavelength Å, 표시명)
    'OII_3727': (3727.42, '[OII]3727'),
    'H_delta': (4101.74, 'Hδ'),
    'H_gamma': (4340.47, 'Hγ'),
    'H_beta': (4861.33, 'Hβ'),
    'OIII_4959': (4958.91, '[OIII]4959'),
    'OIII_5007': (5006.84, '[OIII]5007'),
    'HeI_5876': (5875.62, 'HeI5876'),
    'OI_6300': (6300.30, '[OI]6300'),
    'NII_6548': (6548.03, '[NII]6548'),
    'H_alpha': (6562.82, 'Hα'),
    'NII_6584': (6583.41, '[NII]6584'),
    'SII_6717': (6716.47, '[SII]6717'),
    'SII_6731': (6730.85, '[SII]6731'),
}

ABSORPTION_LIST = {
    'CaII_K': (3933.66, 'Ca K'),
    'CaII_H': (3968.47, 'Ca H'),
    'G_band': (4304.40, 'G-band'),
    'Mg_b': (5175.36, 'Mg b'),
    'Na_D': (5892.90, 'Na D'),
}

# 블렌드 그룹: 함께 피팅해야 하는 근접 선
BLEND_GROUPS = [
    ('NII_6548', 'H_alpha', 'NII_6584'),
    ('SII_6717', 'SII_6731'),
    ('OIII_4959', 'OIII_5007'),
]


def robust_std(x):
    """MAD 기반 강건한 표준편차"""
    x = np.asarray(x, dtype=float)
    x = x[np.isfinite(x)]
    if len(x) == 0:
        return 1.0
    mad = np.median(np.abs(x - np.median(x)))
    s = 1.4826 * mad
    if s <= 0:
        s = np.std(x) if np.std(x) > 0 else 1.0
    return float(s)


class SpectrumROIExtractor:
    """이미지에서 1D 스펙트럼 프로파일을 추출하는 클래스입니다."""

    @staticmethod
    def _to_gray(arr):
        if arr.ndim == 3:
            return np.mean(arr[..., :3].astype(float), axis=2)
        return arr.astype(float)

    def extract_from_rect(self, image_array: np.ndarray, x1: int, y1: int, x2: int, y2: int,
                          axis: str = 'auto') -> tuple:
        """직사각형 ROI에서 스펙트럼을 추출합니다.

        Args:
            image_array: 2D 또는 3D 이미지 배열
            x1, y1, x2, y2: 직사각형 ROI의 좌상단 및 우하단 좌표
            axis: 'auto', 'horizontal', 또는 'vertical'

        Returns:
            pixel_positions, flux_values
        """
        try:
            y_min, y_max = min(y1, y2), max(y1, y2)
            x_min, x_max = min(x1, x2), max(x1, x2)
            y_min = max(0, y_min)
            y_max = min(image_array.shape[0], y_max + 1)
            x_min = max(0, x_min)
            x_max = min(image_array.shape[1], x_max + 1)

            cropped = image_array[y_min:y_max, x_min:x_max]
            if cropped.size == 0:
                raise ValueError("ROI 크롭 결과가 비어있습니다.")

            cropped_gray = self._to_gray(cropped)

            if axis == 'auto':
                # 분광 띠는 보통 길쭉함 → 긴 축을 분산 방향으로 간주,
                # 정사각형에 가까우면 분산(variance) 비교로 결정
                h, w = cropped_gray.shape
                if w >= 1.5 * h:
                    axis = 'horizontal'
                elif h >= 1.5 * w:
                    axis = 'vertical'
                else:
                    var_x = np.var(np.sum(cropped_gray, axis=0))
                    var_y = np.var(np.sum(cropped_gray, axis=1))
                    axis = 'horizontal' if var_x > var_y else 'vertical'

            if axis == 'horizontal':
                flux = np.sum(cropped_gray, axis=0)
            else:
                flux = np.sum(cropped_gray, axis=1)

            pixels = np.arange(len(flux))
            return pixels, flux
        except Exception:
            return np.array([]), np.array([])

    def extract_from_line(self, image_array: np.ndarray, x1: int, y1: int, x2: int, y2: int,
                          width: int = 10) -> tuple:
        """주어진 선분을 따라 스펙트럼을 추출합니다 (선분 수직 방향 width 픽셀 적분)."""
        try:
            length = int(np.hypot(x2 - x1, y2 - y1))
            if length == 0:
                length = 1
            x_line = np.linspace(x1, x2, length)
            y_line = np.linspace(y1, y2, length)
            img = self._to_gray(image_array)

            dx, dy = x2 - x1, y2 - y1
            norm = np.hypot(dx, dy)
            if norm == 0:
                yy = int(np.clip(y1, 0, img.shape[0] - 1))
                xx = int(np.clip(x1, 0, img.shape[1] - 1))
                return np.array([0]), np.array([img[yy, xx]])

            nx, ny = -dy / norm, dx / norm
            width = max(1, int(width))
            fluxes = []
            for w in range(-(width // 2), width // 2 + 1):
                cur_x = x_line + nx * w
                cur_y = y_line + ny * w
                profile = ndimage.map_coordinates(img, [cur_y, cur_x], order=1, mode='nearest')
                fluxes.append(profile)

            flux = np.sum(fluxes, axis=0)
            pixels = np.arange(len(flux))
            return pixels, flux
        except Exception:
            return np.array([]), np.array([])

    def extract_from_mask(self, image_array: np.ndarray, mask: np.ndarray, axis: str = 'auto') -> tuple:
        """자유형 이진 마스크에서 스펙트럼을 추출합니다 (마스크 바운딩 박스 범위만 사용)."""
        try:
            img = self._to_gray(image_array)
            mask = mask.astype(bool)
            if not mask.any():
                return np.array([]), np.array([])
            masked = img * mask

            ys, xs = np.where(mask)
            y0, y1_ = ys.min(), ys.max() + 1
            x0, x1_ = xs.min(), xs.max() + 1
            sub = masked[y0:y1_, x0:x1_]
            submask = mask[y0:y1_, x0:x1_]

            if axis == 'auto':
                h, w = sub.shape
                if w >= 1.5 * h:
                    axis = 'horizontal'
                elif h >= 1.5 * w:
                    axis = 'vertical'
                else:
                    var_x = np.var(np.sum(sub, axis=0))
                    var_y = np.var(np.sum(sub, axis=1))
                    axis = 'horizontal' if var_x > var_y else 'vertical'

            if axis == 'horizontal':
                s = np.sum(sub, axis=0)
                n = np.sum(submask, axis=0)
            else:
                s = np.sum(sub, axis=1)
                n = np.sum(submask, axis=1)
            # 열마다 마스크 픽셀 수가 다르므로 평균 × 최대 폭으로 정규화
            n_safe = np.where(n > 0, n, 1)
            flux = s / n_safe * max(1, n.max())
            pixels = np.arange(len(flux))
            return pixels, flux
        except Exception:
            return np.array([]), np.array([])

    def extract_full_image(self, image_array: np.ndarray) -> tuple:
        """전체 이미지에서 스펙트럼을 추출합니다 (Fallback)."""
        h, w = image_array.shape[:2]
        return self.extract_from_rect(image_array, 0, 0, w - 1, h - 1)


class WavelengthCalibrator:
    """픽셀-파장 변환을 담당하는 클래스입니다."""

    def __init__(self):
        self.reference_lines = {k: v[0] for k, v in LINE_LIST.items()}
        self.reference_lines.update({k: v[0] for k, v in ABSORPTION_LIST.items()})
        # 분광기 교정용 대표 램프/하늘선 (형광등 Hg 등)
        self.lamp_lines = {
            'Hg 4047': 4046.56, 'Hg 4358': 4358.33, 'Tb 4878 (형광등)': 4878.0,
            'Hg 5461': 5460.74, 'Hg 5770': 5769.60, 'Hg 5791': 5790.66,
            'Eu 6112 (형광등)': 6112.0, 'Eu 6313 (형광등)': 6313.0,
            'Na D 5893': 5892.94, 'Hα 6563': 6562.82, 'Hβ 4861': 4861.33,
        }

    def calibrate_linear(self, pixel1: float, wave1: float, pixel2: float, wave2: float,
                         n_pixels: int) -> np.ndarray:
        """두 기준점을 이용한 선형 파장 교정(Linear wavelength solution)을 수행합니다."""
        if pixel1 == pixel2:
            raise ValueError("픽셀 기준점은 서로 달라야 합니다.")
        slope = (wave2 - wave1) / (pixel2 - pixel1)
        intercept = wave1 - slope * pixel1
        pixels = np.arange(n_pixels)
        return slope * pixels + intercept

    def calibrate_poly(self, pixels_ref, waves_ref, n_pixels: int, degree: int = None):
        """다점 다항식 파장 교정. Returns (wavelengths, rms_residual, coeffs)"""
        p = np.asarray(pixels_ref, dtype=float)
        w = np.asarray(waves_ref, dtype=float)
        if len(p) < 2:
            raise ValueError("기준점이 최소 2개 필요합니다.")
        if degree is None:
            degree = 1 if len(p) < 4 else 2
        degree = min(degree, len(p) - 1)
        coeffs = np.polyfit(p, w, degree)
        resid = w - np.polyval(coeffs, p)
        rms = float(np.sqrt(np.mean(resid ** 2))) if len(p) > degree + 1 else 0.0
        return np.polyval(coeffs, np.arange(n_pixels)), rms, coeffs

    def calibrate_from_range(self, n_pixels: int, min_wave: float = 4000, max_wave: float = 7000) -> np.ndarray:
        """간단한 최소/최대 파장 범위를 이용해 선형 교정을 수행합니다."""
        return np.linspace(min_wave, max_wave, n_pixels)

    @staticmethod
    def calibrate_from_fits_header(header, n_pixels: int):
        """FITS 헤더의 선형 WCS (CRVAL1, CDELT1/CD1_1, CRPIX1) 로 파장해 계산.
        SDSS 형식 (COEFF0, COEFF1: log10 λ) 도 지원. 실패 시 None."""
        if header is None:
            return None
        try:
            if 'COEFF0' in header and 'COEFF1' in header:
                loglam = header['COEFF0'] + header['COEFF1'] * np.arange(n_pixels)
                return 10 ** loglam
            crval = header.get('CRVAL1')
            cdelt = header.get('CDELT1', header.get('CD1_1'))
            crpix = header.get('CRPIX1', 1.0)
            if crval is None or cdelt is None:
                return None
            wav = crval + (np.arange(n_pixels) + 1 - crpix) * cdelt
            ctype = str(header.get('CTYPE1', '')).upper()
            if 'LOG' in ctype or (wav.max() < 10 and wav.min() > 3):
                wav = 10 ** wav
            cunit = str(header.get('CUNIT1', '')).lower()
            if cunit in ('nm', 'nanometer'):
                wav = wav * 10.0
            elif cunit in ('m', 'meter'):
                wav = wav * 1e10
            elif cunit in ('um', 'micron'):
                wav = wav * 1e4
            return wav
        except Exception:
            return None


class EmissionLineFitter:
    """스펙트럼 방출선의 연속선(Continuum) 맞춤, 피크 탐지 및 가우시안 피팅을 수행하는 클래스입니다."""

    # 하위 호환: 기본 4대 진단선
    EMISSION_LINES = {
        'H_beta': 4861.33,
        'OIII_5007': 5006.84,
        'H_alpha': 6562.82,
        'NII_6584': 6583.41,
    }
    ALL_LINES = {k: v[0] for k, v in LINE_LIST.items()}

    # ── 연속선 ────────────────────────────────────────────
    def _window_size(self, wavelength, width_angstrom=150.0):
        n = len(wavelength)
        if n < 5:
            return 3
        disp = np.abs(np.median(np.diff(wavelength))) or 1.0
        size = int(width_angstrom / disp)
        size = max(5, min(size, max(5, n // 3)))
        if size % 2 == 0:
            size += 1
        return size

    def fit_continuum(self, wavelength: np.ndarray, flux: np.ndarray, method: str = 'median') -> np.ndarray:
        """연속선(Continuum)을 피팅합니다. method: 'median' | 'poly'"""
        try:
            wavelength = np.asarray(wavelength, dtype=float)
            flux = np.asarray(flux, dtype=float)
            if method == 'median':
                size = self._window_size(wavelength)
                cont = ndimage.median_filter(flux, size=size, mode='nearest')
                # 반복적 sigma-clip 으로 방출선 영향 제거 후 평활화
                resid = flux - cont
                s = robust_std(resid)
                clipped = np.where(resid > 2.5 * s, cont, flux)
                cont = ndimage.median_filter(clipped, size=size, mode='nearest')
                cont = ndimage.uniform_filter1d(cont, size=max(3, size // 3), mode='nearest')
                return cont
            elif method == 'poly':
                threshold = np.percentile(flux, 60)
                mask = flux < threshold
                if np.sum(mask) < 5:
                    mask = np.ones_like(flux, dtype=bool)
                x = (wavelength - wavelength.mean()) / (np.ptp(wavelength) or 1.0)
                coeffs = np.polyfit(x[mask], flux[mask], 3)
                return np.polyval(coeffs, x)
            else:
                return np.zeros_like(flux)
        except Exception:
            return np.full_like(np.asarray(flux, dtype=float), np.median(flux))

    def subtract_continuum(self, wavelength: np.ndarray, flux: np.ndarray, continuum: np.ndarray) -> np.ndarray:
        """스펙트럼 플럭스에서 연속선을 뺍니다."""
        return np.asarray(flux, dtype=float) - np.asarray(continuum, dtype=float)

    @staticmethod
    def smooth(flux, window: int = 7, method: str = 'savgol'):
        """스펙트럼 평활화 (savgol | boxcar | gaussian)"""
        flux = np.asarray(flux, dtype=float)
        if window <= 1 or len(flux) < 5:
            return flux
        window = int(window)
        if method == 'savgol':
            w = window if window % 2 == 1 else window + 1
            w = min(w, len(flux) - (1 - len(flux) % 2))
            if w < 5:
                return flux
            return signal.savgol_filter(flux, w, 3)
        if method == 'gaussian':
            return ndimage.gaussian_filter1d(flux, window / 2.355)
        return ndimage.uniform_filter1d(flux, window)

    # ── 피크 탐지 ─────────────────────────────────────────
    def detect_peaks(self, wavelength: np.ndarray, flux: np.ndarray, snr_threshold: float = 3.0,
                     prominence: float = None, line_list: dict = None, tolerance: float = None) -> dict:
        """방출선 피크를 탐지하고 알려진 방출선과 매칭합니다."""
        line_list = line_list or self.EMISSION_LINES
        noise = robust_std(flux)
        prominence = prominence if prominence is not None else snr_threshold * noise
        peaks, _ = signal.find_peaks(flux, prominence=prominence)

        disp = np.abs(np.median(np.diff(wavelength))) if len(wavelength) > 1 else 1.0
        if tolerance is None:
            tolerance = max(8.0, 3 * disp)

        detected = {}
        for p in peaks:
            w = wavelength[p]
            f = flux[p]
            snr = f / noise
            best_match, min_dist = None, tolerance
            for name, ref_w in line_list.items():
                dist = abs(w - ref_w)
                if dist < min_dist:
                    min_dist = dist
                    best_match = name
            if best_match:
                if best_match not in detected or f > detected[best_match]['flux']:
                    detected[best_match] = {'wavelength': float(w), 'flux': float(f), 'snr': float(snr)}
        return detected if detected else None

    # ── 가우시안 ─────────────────────────────────────────
    def _gaussian(self, x, a, x0, sigma):
        return a * np.exp(-(x - x0) ** 2 / (2 * sigma ** 2))

    def fit_gaussian(self, wavelength: np.ndarray, flux: np.ndarray, center: float, window: float = 20) -> dict:
        """단일 방출선에 대해 가우시안 피팅을 수행합니다."""
        mask = (wavelength >= center - window) & (wavelength <= center + window)
        w_window = wavelength[mask]
        f_window = flux[mask]
        if len(w_window) < 5:
            return None
        try:
            disp = np.abs(np.median(np.diff(w_window))) or 1.0
            a_guess = max(np.max(f_window), 1e-12)
            sigma_guess = max(2.0, 1.5 * disp)
            p0 = [a_guess, center, sigma_guess]
            bounds = ([0, center - window, 0.3 * disp], [np.inf, center + window, window])
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", optimize.OptimizeWarning)
                popt, pcov = optimize.curve_fit(self._gaussian, w_window, f_window, p0=p0,
                                                bounds=bounds, maxfev=4000)
            a, x0, sigma = popt
            perr = np.sqrt(np.clip(np.diag(pcov), 0, None)) if np.all(np.isfinite(pcov)) else [np.nan] * 3
            integrated_flux = a * sigma * np.sqrt(2 * np.pi)
            flux_err = integrated_flux * np.sqrt((perr[0] / a) ** 2 + (perr[2] / sigma) ** 2) if a > 0 else np.nan
            return {
                'amplitude': float(a), 'center': float(x0), 'sigma': float(abs(sigma)),
                'integrated_flux': float(integrated_flux), 'flux_err': float(flux_err),
                'fwhm': float(2.355 * abs(sigma)),
            }
        except Exception:
            return None

    def _fit_blend(self, wavelength, flux, names, z_rest_centers, noise):
        """근접 선 그룹을 공통 폭/공통 속도 이동 다중 가우시안으로 동시 피팅"""
        centers = np.array([z_rest_centers[n] for n in names])
        lo, hi = centers.min() - 25, centers.max() + 25
        m = (wavelength >= lo) & (wavelength <= hi)
        w, f = wavelength[m], flux[m]
        if len(w) < len(names) * 2 + 3:
            return {}
        disp = np.abs(np.median(np.diff(w))) or 1.0

        def model(x, shift, sigma, *amps):
            y = np.zeros_like(x)
            for c, a in zip(centers, amps):
                y += a * np.exp(-(x - (c + shift)) ** 2 / (2 * sigma ** 2))
            return y

        amps0 = []
        for c in centers:
            idx = np.argmin(np.abs(w - c))
            amps0.append(max(f[max(0, idx - 1):idx + 2].max(), 0.0) + 1e-9)
        p0 = [0.0, max(2.0, 1.5 * disp)] + amps0
        lower = [-8.0, 0.3 * disp] + [0.0] * len(names)
        upper = [8.0, 20.0] + [np.inf] * len(names)
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                popt, pcov = optimize.curve_fit(model, w, f, p0=p0, bounds=(lower, upper), maxfev=6000)
        except Exception:
            return {}
        shift, sigma = popt[0], abs(popt[1])
        perr = np.sqrt(np.clip(np.diag(pcov), 0, None)) if np.all(np.isfinite(pcov)) else np.full(len(popt), np.nan)
        out = {}
        for i, n in enumerate(names):
            a = popt[2 + i]
            a_err = perr[2 + i]
            flux_int = a * sigma * np.sqrt(2 * np.pi)
            snr = a / noise if noise > 0 else np.nan
            out[n] = {
                'amplitude': float(a), 'center': float(centers[i] + shift), 'sigma': float(sigma),
                'integrated_flux': float(flux_int),
                'flux_err': float(flux_int * (a_err / a)) if a > 0 and np.isfinite(a_err) else np.nan,
                'fwhm': float(2.355 * sigma), 'snr': float(snr), 'blend': True,
            }
        return out

    # ── 지수 ─────────────────────────────────────────────
    @staticmethod
    def equivalent_width(line_flux, wavelength, continuum, center):
        """등가폭 EW (Å). SDSS 규약: 방출선은 음수."""
        try:
            idx = np.argmin(np.abs(wavelength - center))
            c = np.median(continuum[max(0, idx - 3): idx + 4])
            if c is None or c <= 0 or not np.isfinite(c):
                return None
            return float(-line_flux / c)
        except Exception:
            return None

    @staticmethod
    def d4000(rest_wave, flux):
        """D4000_n (Balogh 1999): <F_ν>[4000-4100] / <F_ν>[3850-3950]"""
        try:
            fnu = flux * rest_wave ** 2
            blue = (rest_wave >= 3850) & (rest_wave <= 3950)
            red = (rest_wave >= 4000) & (rest_wave <= 4100)
            if blue.sum() < 3 or red.sum() < 3:
                return None
            b = np.mean(fnu[blue])
            r = np.mean(fnu[red])
            if b <= 0:
                return None
            return float(r / b)
        except Exception:
            return None

    def estimate_redshift(self, wavelength, flux, z_min=0.0, z_max=0.5, n_grid=2000):
        """방출선 패턴 매칭으로 적색편이 추정. Returns dict(z, score, n_matched) or None"""
        try:
            wavelength = np.asarray(wavelength, dtype=float)
            flux = np.asarray(flux, dtype=float)
            cont = self.fit_continuum(wavelength, flux)
            sub = flux - cont
            noise = robust_std(sub)
            disp0 = np.abs(np.median(np.diff(wavelength))) or 1.0
            # 연속선 위로 4σ 이상 + 방출선처럼 좁은 봉우리만 (4000Å break·흡수선 가장자리의 넓은 잔차 제외)
            peaks, props = signal.find_peaks(sub, height=4 * noise, prominence=3 * noise,
                                             width=(None, max(3.0, 30.0 / disp0)))
            if len(peaks) < 2:
                return None
            pw = wavelength[peaks]
            pf = np.clip(sub[peaks] / noise, 0, None)
            strong = {'H_alpha': 3.0, 'OIII_5007': 2.0, 'H_beta': 1.5, 'NII_6584': 1.0,
                      'OII_3727': 1.5, 'SII_6717': 0.7, 'SII_6731': 0.7, 'OIII_4959': 0.8,
                      'H_gamma': 0.6}
            disp = np.abs(np.median(np.diff(wavelength))) or 1.0
            tol = max(4.0, 2.5 * disp)
            best = (None, 0.0, 0)
            for z in np.linspace(z_min, z_max, n_grid):
                score, nmatch, sigs = 0.0, 0, []
                for name, wgt in strong.items():
                    obs = LINE_LIST[name][0] * (1 + z)
                    if obs < wavelength.min() or obs > wavelength.max():
                        continue
                    d = np.abs(pw - obs)
                    j = np.argmin(d)
                    if d[j] < tol:
                        score += wgt * np.log1p(pf[j]) * (1 - d[j] / tol)
                        nmatch += 1
                        sigs.append(pf[j])
                # 잡음 봉우리 우연 일치 방지: 3개 이상 일치, 또는 2개가 모두 매우 강할 때만 인정
                ok = nmatch >= 3 or (nmatch == 2 and min(sigs) >= 8)
                if ok and score > best[1]:
                    best = (z, score, nmatch)
            if best[0] is None:
                return None
            return {'z': float(best[0]), 'score': float(best[1]), 'n_matched': int(best[2])}
        except Exception:
            return None

    # ── 메인 파이프라인 ──────────────────────────────────
    def fit_all_lines(self, wavelength: np.ndarray, flux: np.ndarray, z: float = 0.0,
                      continuum_method: str = 'median', snr_threshold: float = 3.0) -> dict:
        """연속선 차감, 피크 탐지, 블렌드/단일 가우시안 피팅, EW, D4000 전체 파이프라인.

        Returns dict:
            continuum, subtracted_flux, rest_wavelength, noise,
            peaks (기존 호환: 4대 진단선), fits (검출된 모든 선),
            line_table (DataFrame), d4000
        """
        results = {}
        try:
            wavelength = np.asarray(wavelength, dtype=float)
            flux = np.asarray(flux, dtype=float)
            order = np.argsort(wavelength)
            wavelength, flux = wavelength[order], flux[order]
            rest_wave = wavelength / (1 + z)

            continuum = self.fit_continuum(rest_wave, flux, method=continuum_method)
            sub_flux = self.subtract_continuum(rest_wave, flux, continuum)
            noise = robust_std(sub_flux)

            peaks = self.detect_peaks(rest_wave, sub_flux, snr_threshold=snr_threshold)
            all_peaks = self.detect_peaks(rest_wave, sub_flux, snr_threshold=snr_threshold,
                                          line_list=self.ALL_LINES) or {}

            results.update({
                'continuum': continuum, 'subtracted_flux': sub_flux,
                'rest_wavelength': rest_wave, 'noise': noise,
                'peaks': peaks, 'fits': {},
            })

            covered = {n: c for n, c in self.ALL_LINES.items()
                       if rest_wave.min() + 5 < c < rest_wave.max() - 5}
            fits = {}

            # 1) 블렌드 그룹 동시 피팅
            for group in BLEND_GROUPS:
                names = [n for n in group if n in covered]
                if len(names) < 2:
                    continue
                if not any(n in all_peaks for n in names):
                    continue
                res = self._fit_blend(rest_wave, sub_flux, names, covered, noise)
                for n, info in res.items():
                    if info['snr'] >= snr_threshold * 0.8 or n in all_peaks:
                        fits[n] = info

            # 2) 나머지 단일선
            for n, info in all_peaks.items():
                if n in fits:
                    continue
                fr = self.fit_gaussian(rest_wave, sub_flux, info['wavelength'], window=15)
                if fr:
                    fr['snr'] = fr['amplitude'] / noise if noise > 0 else np.nan
                    fr['blend'] = False
                    fits[n] = fr

            # 3) 4대 진단선이 피크로는 안 잡혔지만 다른 선이 잡혔다면 고정 위치에서 강제 측정 (상한값 대용)
            for n in ['H_beta', 'OIII_5007', 'H_alpha', 'NII_6584']:
                if n in fits or n not in covered or not fits:
                    continue
                fr = self.fit_gaussian(rest_wave, sub_flux, covered[n], window=8)
                if fr and fr['amplitude'] > 1.5 * noise:
                    fr['snr'] = fr['amplitude'] / noise
                    fr['blend'] = False
                    fr['forced'] = True
                    fits[n] = fr

            # 신뢰도 필터: 잡음성 가짜 검출 제거
            min_snr = max(2.0, 0.8 * snr_threshold)
            fits = {n: i for n, i in fits.items()
                    if i.get('integrated_flux', 0) > 0 and np.isfinite(i.get('snr', np.nan))
                    and i['snr'] >= (2.0 if i.get('forced') else min_snr)
                    and not (np.isfinite(i.get('flux_err', np.nan))
                             and i['flux_err'] > i['integrated_flux'] / 1.5)}

            # EW
            for n, info in fits.items():
                info['ew'] = self.equivalent_width(info['integrated_flux'], rest_wave, continuum, info['center'])
                info['rest_wavelength'] = LINE_LIST[n][0]
                info['label'] = LINE_LIST[n][1]

            results['fits'] = fits
            results['d4000'] = self.d4000(rest_wave, flux)

            rows = []
            for n in sorted(fits, key=lambda k: LINE_LIST[k][0]):
                i = fits[n]
                rows.append({
                    '선': i['label'], 'key': n, '정지파장(Å)': i['rest_wavelength'],
                    '측정중심(Å)': round(i['center'], 2), 'FWHM(Å)': round(i['fwhm'], 2),
                    '적분플럭스': i['integrated_flux'], '오차': i.get('flux_err'),
                    'S/N': round(i.get('snr', np.nan), 1) if i.get('snr') is not None else None,
                    'EW(Å)': round(i['ew'], 2) if i.get('ew') is not None else None,
                    '블렌드': '예' if i.get('blend') else '',
                })
            results['line_table'] = pd.DataFrame(rows)
            return results
        except Exception as e:
            results['error'] = str(e)
            results.setdefault('fits', {})
            results.setdefault('peaks', None)
            return results

    @staticmethod
    def extract_line_fluxes(result: dict) -> dict:
        """fit_all_lines 결과에서 {선 이름: 적분플럭스} 딕셔너리 추출"""
        out = {}
        if not result:
            return out
        for n, info in (result.get('fits') or {}).items():
            if info and info.get('integrated_flux') is not None and info['integrated_flux'] > 0:
                out[n] = float(info['integrated_flux'])
        return out


class MockSpectrumGenerator:
    """테스트용 가상 스펙트럼을 생성하는 클래스입니다."""

    def _create_base(self, min_wave=3600, max_wave=7400, n_pts=4000):
        wavelength = np.linspace(min_wave, max_wave, n_pts)
        return wavelength, np.zeros_like(wavelength)

    def _add_gaussian(self, x, y, center, amp, sigma):
        y += amp * np.exp(-(x - center) ** 2 / (2 * sigma ** 2))
        return y

    def _lines(self, wave, flux, spec, sigma):
        for name, amp in spec.items():
            self._add_gaussian(wave, flux, LINE_LIST[name][0], amp, sigma)

    def generate_star_forming(self) -> pd.DataFrame:
        """강한 Hα, 중간 [OIII], 약한 [NII]"""
        wave, flux = self._create_base()
        flux += 10.0 * (wave / 5000) ** (-1.5)
        self._lines(wave, flux, {
            'OII_3727': 40.0, 'H_gamma': 9.0, 'H_beta': 20.0, 'OIII_4959': 5.0,
            'OIII_5007': 15.0, 'NII_6548': 5.0, 'H_alpha': 100.0, 'NII_6584': 15.0,
            'SII_6717': 12.0, 'SII_6731': 9.0,
        }, 3.0)
        flux += np.random.normal(0, 1.0, len(wave))
        return pd.DataFrame({'wavelength': wave, 'flux': flux})

    def generate_agn_seyfert(self) -> pd.DataFrame:
        """전형적 세이퍼트 2: 강한 [OIII] (log[OIII]/Hβ≈1.0), 강한 [NII] (log[NII]/Hα≈0), Hα/Hβ≈3.5"""
        wave, flux = self._create_base()
        flux += 15.0 * (wave / 5000) ** (-1.0)
        self._lines(wave, flux, {
            'OII_3727': 60.0, 'H_beta': 20.0, 'OIII_4959': 67.0, 'OIII_5007': 200.0,
            'OI_6300': 18.0, 'NII_6548': 25.0, 'H_alpha': 70.0, 'NII_6584': 75.0,
            'SII_6717': 30.0, 'SII_6731': 28.0,
        }, 5.0)
        flux += np.random.normal(0, 1.5, len(wave))
        return pd.DataFrame({'wavelength': wave, 'flux': flux})

    def generate_elliptical(self) -> pd.DataFrame:
        """약한 방출선, 강한 연속선, D4000 break, 흡수선"""
        wave, flux = self._create_base()
        flux[:] = np.where(wave < 4000, 6.0 * (wave / 4000) ** 3, 12.0 * (wave / 4000) ** (-0.5))
        for name, depth in {'CaII_K': 3.0, 'CaII_H': 2.5, 'G_band': 1.5, 'Mg_b': 2.0, 'Na_D': 1.5}.items():
            self._add_gaussian(wave, flux, ABSORPTION_LIST[name][0], -depth, 6.0)
        self._add_gaussian(wave, flux, LINE_LIST['NII_6584'][0], 1.2, 4.0)
        self._add_gaussian(wave, flux, LINE_LIST['H_alpha'][0], 0.8, 4.0)
        flux += np.random.normal(0, 0.3, len(wave))
        return pd.DataFrame({'wavelength': wave, 'flux': flux})

    def generate(self, galaxy_type: str = 'star_forming', z: float = 0.0) -> pd.DataFrame:
        """지정된 유형의 가상 스펙트럼을 생성합니다 (z > 0 이면 관측 파장으로 적색편이)."""
        if galaxy_type == 'star_forming':
            df = self.generate_star_forming()
        elif galaxy_type in ['agn', 'agn_seyfert']:
            df = self.generate_agn_seyfert()
        elif galaxy_type == 'elliptical':
            df = self.generate_elliptical()
        else:
            df = self.generate_star_forming()
        if z and z > 0:
            df['wavelength'] = df['wavelength'] * (1 + z)
        return df

    @staticmethod
    def wavelength_to_rgb(wl):
        """파장(Å) → 근사 RGB (가시광 3800–7500Å)"""
        w = wl / 10.0  # nm
        if 380 <= w < 440:
            r, g, b = -(w - 440) / 60, 0.0, 1.0
        elif 440 <= w < 490:
            r, g, b = 0.0, (w - 440) / 50, 1.0
        elif 490 <= w < 510:
            r, g, b = 0.0, 1.0, -(w - 510) / 20
        elif 510 <= w < 580:
            r, g, b = (w - 510) / 70, 1.0, 0.0
        elif 580 <= w < 645:
            r, g, b = 1.0, -(w - 645) / 65, 0.0
        elif 645 <= w <= 780:
            r, g, b = 1.0, 0.0, 0.0
        else:
            r, g, b = 0.3, 0.3, 0.3
        if 380 <= w < 420:
            f = 0.3 + 0.7 * (w - 380) / 40
        elif 700 < w <= 780:
            f = 0.3 + 0.7 * (780 - w) / 80
        else:
            f = 1.0
        return np.array([r * f, g * f, b * f])

    def generate_spectrum_image(self, galaxy_type: str = 'star_forming', width: int = 900,
                                height: int = 360, band_height: int = 70) -> tuple:
        """ROI 시연용 '분광 사진' 생성: 가로 방향 무지개 띠 위에 방출선이 밝게 표시됨.
        - 채널 평균 밝기가 플럭스에 정확히 비례(평탄한 감도의 이상적 센서)
        - 실제 사진처럼 sRGB 감마(1/2.2)로 인코딩 → 앱의 감마 보정으로 선형 플럭스 복원
        Returns (PIL.Image, min_wave, max_wave)"""
        df = self.generate(galaxy_type)
        wmin, wmax = 3800.0, 7200.0
        xs = np.linspace(wmin, wmax, width)
        f = np.interp(xs, df['wavelength'], df['flux'])
        f = np.clip(f, 0, None)
        f = f / (f.max() or 1.0)                       # 강한 선도 포화되지 않도록 최댓값 정규화
        img = np.zeros((height, width, 3), dtype=float)
        rng = np.random.default_rng(1)
        img += np.abs(rng.normal(0.002, 0.001, img.shape))
        y0 = height // 2 - band_height // 2
        profile = np.exp(-((np.arange(band_height) - band_height / 2) ** 2) / (2 * (band_height / 4) ** 2))
        for i, wl in enumerate(xs):
            rgb = self.wavelength_to_rgb(wl)
            col = rgb / (rgb.mean() or 1.0) / 3.0 * f[i]   # 채널 평균 = f/3, 각 채널 ≤ 1
            img[y0:y0 + band_height, i, :] += profile[:, None] * col[None, :]
        img = np.clip(img, 0, 1) ** (1 / 2.2)
        return Image.fromarray(np.round(img * 255).astype(np.uint8)), wmin, wmax

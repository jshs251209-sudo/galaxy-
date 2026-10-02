"""
스펙트럼 추출, 파장 교정, 방출선 피팅 및 가상 스펙트럼 생성을 위한 핵심 엔진 모듈입니다.
UI (Streamlit 등) 독립적으로 작동하며 순수 연산 함수를 제공합니다.
"""

import numpy as np
import pandas as pd
from scipy import signal, optimize, ndimage, stats
from PIL import Image

class SpectrumROIExtractor:
    """이미지에서 1D 스펙트럼 프로파일을 추출하는 클래스입니다."""
    
    def extract_from_rect(self, image_array: np.ndarray, x1: int, y1: int, x2: int, y2: int, axis: str = 'auto') -> tuple[np.ndarray, np.ndarray]:
        """직사각형 ROI에서 스펙트럼을 추출합니다.
        
        Args:
            image_array: 2D 또는 3D 이미지 배열
            x1, y1, x2, y2: 직사각형 ROI의 좌상단 및 우하단 좌표
            axis: 'auto', 'horizontal', 또는 'vertical'
            
        Returns:
            pixel_positions, flux_values
        """
        try:
            # 1. 크롭
            y_min, y_max = min(y1, y2), max(y1, y2)
            x_min, x_max = min(x1, x2), max(x1, x2)
            
            # 인덱스 범위 확인
            y_min = max(0, y_min)
            y_max = min(image_array.shape[0], y_max + 1)
            x_min = max(0, x_min)
            x_max = min(image_array.shape[1], x_max + 1)
            
            cropped = image_array[y_min:y_max, x_min:x_max]
            
            if cropped.size == 0:
                raise ValueError("ROI 크롭 결과가 비어있습니다.")
            
            # 2. 흑백 변환
            if cropped.ndim == 3:
                cropped_gray = np.mean(cropped, axis=2)
            else:
                cropped_gray = cropped
                
            # 3. 축 감지
            if axis == 'auto':
                var_x = np.var(np.sum(cropped_gray, axis=0))
                var_y = np.var(np.sum(cropped_gray, axis=1))
                axis = 'horizontal' if var_x > var_y else 'vertical'
                
            # 4. 프로파일 추출
            if axis == 'horizontal':
                flux = np.sum(cropped_gray, axis=0)
            else:
                flux = np.sum(cropped_gray, axis=1)
                
            pixels = np.arange(len(flux))
            return pixels, flux
            
        except Exception as e:
            return np.array([]), np.array([])

    def extract_from_line(self, image_array: np.ndarray, x1: int, y1: int, x2: int, y2: int, width: int = 10) -> tuple[np.ndarray, np.ndarray]:
        """주어진 선분을 따라 스펙트럼을 추출합니다.
        
        Args:
            image_array: 2D 또는 3D 이미지 배열
            x1, y1, x2, y2: 선분의 양 끝점 좌표
            width: 수직 방향으로 적분할 폭 픽셀 수
            
        Returns:
            pixel_positions, flux_values
        """
        try:
            length = int(np.hypot(x2-x1, y2-y1))
            if length == 0:
                length = 1
                
            x_line = np.linspace(x1, x2, length)
            y_line = np.linspace(y1, y2, length)
            
            if image_array.ndim == 3:
                img = np.mean(image_array, axis=2)
            else:
                img = image_array
                
            # 수직 방향 벡터 계산
            dx = x2 - x1
            dy = y2 - y1
            norm = np.hypot(dx, dy)
            if norm == 0:
                return np.array([0]), np.array([img[y1, x1]])
                
            nx = -dy / norm
            ny = dx / norm
            
            fluxes = []
            for w in range(-width//2, width//2 + 1):
                cur_x = x_line + nx * w
                cur_y = y_line + ny * w
                profile = ndimage.map_coordinates(img, [cur_y, cur_x], order=1, mode='nearest')
                fluxes.append(profile)
                
            flux = np.mean(fluxes, axis=0) * width
            pixels = np.arange(len(flux))
            return pixels, flux
            
        except Exception as e:
            return np.array([]), np.array([])
        
    def extract_from_mask(self, image_array: np.ndarray, mask: np.ndarray, axis: str = 'auto') -> tuple[np.ndarray, np.ndarray]:
        """자유형 이진 마스크에서 스펙트럼을 추출합니다.
        
        Args:
            image_array: 2D 또는 3D 이미지 배열
            mask: image_array와 동일한 (height, width) 크기의 이진 마스크
            axis: 'auto', 'horizontal', 또는 'vertical'
            
        Returns:
            pixel_positions, flux_values
        """
        try:
            if image_array.ndim == 3:
                img = np.mean(image_array, axis=2)
            else:
                img = image_array
                
            masked = img * mask
            
            if axis == 'auto':
                var_x = np.var(np.sum(masked, axis=0))
                var_y = np.var(np.sum(masked, axis=1))
                axis = 'horizontal' if var_x > var_y else 'vertical'
                
            if axis == 'horizontal':
                flux = np.sum(masked, axis=0)
            else:
                flux = np.sum(masked, axis=1)
                
            pixels = np.arange(len(flux))
            return pixels, flux
            
        except Exception as e:
            return np.array([]), np.array([])
        
    def extract_full_image(self, image_array: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """전체 이미지에서 스펙트럼을 추출합니다 (Fallback)."""
        try:
            if image_array.ndim == 3:
                img = np.mean(image_array, axis=2)
            else:
                img = image_array
                
            var_x = np.var(np.sum(img, axis=0))
            var_y = np.var(np.sum(img, axis=1))
            
            if var_x > var_y:
                flux = np.sum(img, axis=0)
            else:
                flux = np.sum(img, axis=1)
                
            pixels = np.arange(len(flux))
            return pixels, flux
            
        except Exception as e:
            return np.array([]), np.array([])

class WavelengthCalibrator:
    """픽셀-파장 변환을 담당하는 클래스입니다."""
    def __init__(self):
        self.reference_lines = {
            'H_beta': 4861.33,
            'OIII_4959': 4958.91,
            'OIII_5007': 5006.84,
            'NII_6548': 6548.03,
            'H_alpha': 6562.82,
            'NII_6584': 6583.41,
            'SII_6717': 6716.47,
            'SII_6731': 6730.85,
        }
        
    def calibrate_linear(self, pixel1: float, wave1: float, pixel2: float, wave2: float, n_pixels: int) -> np.ndarray:
        """두 기준점을 이용한 선형 파장 교정(Linear wavelength solution)을 수행합니다."""
        if pixel1 == pixel2:
            raise ValueError("픽셀 기준점은 서로 달라야 합니다.")
        slope = (wave2 - wave1) / (pixel2 - pixel1)
        intercept = wave1 - slope * pixel1
        
        pixels = np.arange(n_pixels)
        wavelengths = slope * pixels + intercept
        return wavelengths
        
    def calibrate_from_range(self, n_pixels: int, min_wave: float = 4000, max_wave: float = 7000) -> np.ndarray:
        """간단한 최소/최대 파장 범위를 이용해 선형 교정을 수행합니다."""
        return np.linspace(min_wave, max_wave, n_pixels)


class EmissionLineFitter:
    """스펙트럼 방출선의 연속선(Continuum) 맞춤, 피크 탐지 및 가우시안 피팅을 수행하는 클래스입니다."""
    
    EMISSION_LINES = {
        'H_beta': 4861.33,
        'OIII_5007': 5006.84,
        'H_alpha': 6562.82,
        'NII_6584': 6583.41,
    }
    
    def fit_continuum(self, wavelength: np.ndarray, flux: np.ndarray, method: str = 'median') -> np.ndarray:
        """연속선(Continuum)을 피팅합니다.
        
        Args:
            wavelength: 파장 배열
            flux: 플럭스 배열
            method: 'median' 또는 'poly'
            
        Returns:
            연속선 배열
        """
        try:
            if method == 'median':
                return ndimage.median_filter(flux, size=101)
            elif method == 'poly':
                threshold = np.percentile(flux, 30)
                mask = flux < threshold
                if np.sum(mask) < 5:
                    mask = np.ones_like(flux, dtype=bool)
                coeffs = np.polyfit(wavelength[mask], flux[mask], 3)
                return np.polyval(coeffs, wavelength)
            else:
                return np.zeros_like(flux)
        except Exception:
            return np.full_like(flux, np.median(flux))
            
    def subtract_continuum(self, wavelength: np.ndarray, flux: np.ndarray, continuum: np.ndarray) -> np.ndarray:
        """스펙트럼 플럭스에서 연속선을 뺍니다."""
        return flux - continuum
        
    def detect_peaks(self, wavelength: np.ndarray, flux: np.ndarray, snr_threshold: float = 3.0, prominence: float = None) -> dict:
        """방출선 피크를 탐지하고 알려진 방출선과 매칭합니다."""
        noise = np.std(flux) if np.std(flux) > 0 else 1.0
        prominence = prominence if prominence is not None else snr_threshold * noise
        
        peaks, properties = signal.find_peaks(flux, prominence=prominence)
        
        detected = {}
        tolerance = 20.0 # 파장 오차 허용 범위
        
        for p in peaks:
            w = wavelength[p]
            f = flux[p]
            snr = f / noise
            
            best_match = None
            min_dist = tolerance
            for name, ref_w in self.EMISSION_LINES.items():
                dist = abs(w - ref_w)
                if dist < min_dist:
                    min_dist = dist
                    best_match = name
                    
            if best_match:
                if best_match in detected:
                    if f > detected[best_match]['flux']:
                        detected[best_match] = {'wavelength': w, 'flux': f, 'snr': snr}
                else:
                    detected[best_match] = {'wavelength': w, 'flux': f, 'snr': snr}
                    
        return detected if detected else None
        
    def _gaussian(self, x, a, x0, sigma):
        return a * np.exp(-(x - x0)**2 / (2 * sigma**2))
        
    def fit_gaussian(self, wavelength: np.ndarray, flux: np.ndarray, center: float, window: float = 20) -> dict:
        """단일 방출선에 대해 가우시안 피팅을 수행합니다."""
        mask = (wavelength >= center - window) & (wavelength <= center + window)
        w_window = wavelength[mask]
        f_window = flux[mask]
        
        if len(w_window) < 5:
            return None
            
        try:
            a_guess = np.max(f_window)
            sigma_guess = 2.0
            p0 = [a_guess, center, sigma_guess]
            
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", optimize.OptimizeWarning)
                popt, pcov = optimize.curve_fit(self._gaussian, w_window, f_window, p0=p0, maxfev=2000)
            a, x0, sigma = popt
            
            integrated_flux = a * sigma * np.sqrt(2 * np.pi)
            fwhm = 2.355 * abs(sigma)
            
            return {
                'amplitude': float(a),
                'center': float(x0),
                'sigma': float(abs(sigma)),
                'integrated_flux': float(integrated_flux),
                'fwhm': float(fwhm)
            }
        except Exception:
            return None
            
    def fit_all_lines(self, wavelength: np.ndarray, flux: np.ndarray, z: float = 0.0) -> dict:
        """연속선 차감, 피크 탐지, 가우시안 피팅을 포함한 전체 파이프라인을 수행합니다."""
        results = {}
        try:
            rest_wave = wavelength / (1 + z)
            
            continuum = self.fit_continuum(rest_wave, flux)
            sub_flux = self.subtract_continuum(rest_wave, flux, continuum)
            
            peaks = self.detect_peaks(rest_wave, sub_flux)
            results['continuum'] = continuum
            results['subtracted_flux'] = sub_flux
            results['peaks'] = peaks
            results['fits'] = {}
            
            if peaks:
                for line, info in peaks.items():
                    fit_res = self.fit_gaussian(rest_wave, sub_flux, info['wavelength'])
                    if fit_res:
                        results['fits'][line] = fit_res
            
            return results
        except Exception as e:
            return {'error': str(e)}

class MockSpectrumGenerator:
    """테스트용 가상 스펙트럼을 생성하는 클래스입니다."""
    
    def _create_base(self, min_wave=3500, max_wave=7500, n_pts=4000):
        wavelength = np.linspace(min_wave, max_wave, n_pts)
        return wavelength, np.zeros_like(wavelength)
        
    def _add_gaussian(self, x, y, center, amp, sigma):
        y += amp * np.exp(-(x - center)**2 / (2 * sigma**2))
        return y
        
    def generate_star_forming(self) -> pd.DataFrame:
        """Strong Halpha, moderate OIII, weak NII"""
        wave, flux = self._create_base()
        flux += 10.0 * (wave/5000)**(-1.5)
        
        self._add_gaussian(wave, flux, 4861.33, 20.0, 3.0) # H beta
        self._add_gaussian(wave, flux, 5006.84, 15.0, 3.0) # OIII
        self._add_gaussian(wave, flux, 6548.03, 5.0, 3.0) # NII
        self._add_gaussian(wave, flux, 6562.82, 100.0, 3.5) # H alpha
        self._add_gaussian(wave, flux, 6583.41, 15.0, 3.0) # NII
        
        flux += np.random.normal(0, 1.0, len(wave))
        return pd.DataFrame({'wavelength': wave, 'flux': flux})
        
    def generate_agn_seyfert(self) -> pd.DataFrame:
        """Strong OIII, strong NII, moderate Halpha"""
        wave, flux = self._create_base()
        flux += 15.0 * (wave/5000)**(-1.0)
        
        self._add_gaussian(wave, flux, 4861.33, 30.0, 5.0) # H beta
        self._add_gaussian(wave, flux, 5006.84, 120.0, 5.0) # OIII
        self._add_gaussian(wave, flux, 6548.03, 30.0, 5.0) # NII
        self._add_gaussian(wave, flux, 6562.82, 60.0, 8.0) # H alpha 
        self._add_gaussian(wave, flux, 6583.41, 90.0, 5.0) # NII
        
        flux += np.random.normal(0, 1.5, len(wave))
        return pd.DataFrame({'wavelength': wave, 'flux': flux})
        
    def generate_elliptical(self) -> pd.DataFrame:
        """Weak emission, strong continuum, D4000 break"""
        wave, flux = self._create_base()
        
        for i, w in enumerate(wave):
            if w < 4000:
                flux[i] = 5.0 * (w/4000)**2
            else:
                flux[i] = 12.0 * (w/4000)**(-0.5)
                
        flux += np.random.normal(0, 0.5, len(wave))
        return pd.DataFrame({'wavelength': wave, 'flux': flux})
        
    def generate(self, galaxy_type: str = 'star_forming') -> pd.DataFrame:
        """지정된 유형의 가상 스펙트럼을 생성합니다."""
        if galaxy_type == 'star_forming':
            return self.generate_star_forming()
        elif galaxy_type in ['agn', 'agn_seyfert']:
            return self.generate_agn_seyfert()
        elif galaxy_type == 'elliptical':
            return self.generate_elliptical()
        else:
            return self.generate_star_forming()

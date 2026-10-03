# -*- coding: utf-8 -*-
"""
streamlit-drawable-canvas 호환 패치
==================================
streamlit-drawable-canvas 0.9.x 는 배경 이미지를 표시할 때
`streamlit.elements.image.image_to_url(image, width, clamp, channels, format, id)`
를 호출합니다. Streamlit 1.4x 이후 이 함수는
`streamlit.elements.lib.image_utils.image_to_url(image, layout_config, ...)` 로
이동/변경되어 사진 위 그리기 화면이 AttributeError 로 깨집니다.

이 모듈을 st_canvas 사용 전에 import 하면 구버전 시그니처의 shim 을 주입합니다.
"""

import streamlit.elements.image as _st_image


def _install_shim():
    if hasattr(_st_image, "image_to_url"):
        return "native"

    try:
        from streamlit.elements.lib.image_utils import image_to_url as _new_image_to_url
    except Exception:  # pragma: no cover
        return "unavailable"

    try:
        from streamlit.elements.lib.layout_utils import LayoutConfig
    except Exception:  # pragma: no cover
        LayoutConfig = None

    def image_to_url(image, width, clamp, channels, output_format, image_id):
        if LayoutConfig is not None:
            try:
                layout = LayoutConfig(width=int(width) if width else None)
            except Exception:
                layout = LayoutConfig()
            return _new_image_to_url(image, layout, clamp, channels, output_format, image_id)
        # 아주 오래된/새로운 버전 대비 — 위치 인자로 시도
        return _new_image_to_url(image, width, clamp, channels, output_format, image_id)

    _st_image.image_to_url = image_to_url
    return "shimmed"


SHIM_STATUS = _install_shim()

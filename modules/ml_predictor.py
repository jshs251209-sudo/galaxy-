import os
import logging
import numpy as np
import pandas as pd
import joblib
import plotly.graph_objects as go


# 앱/모듈 곳곳에서 쓰는 다양한 이름 → 학습 특성 이름
FEATURE_ALIASES = {
    'log_stellar_mass': ['log_stellar_mass', 'log_mass', 'lgm_tot_p50'],
    'log_sfr': ['log_sfr', 'sfr_tot_p50'],
    'log_ssfr': ['log_ssfr'],
    'metallicity_oh': ['metallicity_oh', 'metallicity', 'oh_p50'],
    'd4000_n': ['d4000_n', 'd4000'],
    'velDisp': ['velDisp', 'vel_disp'],
    'z': ['z', 'redshift'],
    'color_u_r': ['color_u_r', 'color_ur'],
    'log_nii_ha': ['log_nii_ha'],
    'log_oiii_hb': ['log_oiii_hb'],
    'log_sii_ha': ['log_sii_ha'],
    'dust_ebv': ['dust_ebv', 'ebv'],
    'h_alpha_eqw': ['h_alpha_eqw', 'ew_halpha'],
    'oiii_5007_eqw': ['oiii_5007_eqw', 'ew_oiii'],
}

FEATURE_LABELS_KO = {
    'log_stellar_mass': '항성질량', 'log_sfr': '별생성률', 'log_ssfr': '비별생성률',
    'metallicity_oh': '금속량', 'd4000_n': 'D4000', 'velDisp': '속도분산', 'z': '적색편이',
    'color_u_r': 'u−r 색', 'concentration_index_r': '집중도', 'petroR50_r': 'R50',
    'petroR90_r': 'R90', 'fracDeV_r': 'deV 비율', 'log_nii_ha': '[NII]/Hα',
    'log_oiii_hb': '[OIII]/Hβ', 'log_sii_ha': '[SII]/Hα', 'dust_ebv': '먼지 E(B−V)',
    'gz_p_el': '타원 확률', 'gz_p_cs': '나선 확률', 'gz_p_mg': '병합 확률',
    'gz2_bar_prob': '막대 확률', 'gz2_ring_prob': '고리 확률', 'first_radio_flux': '전파 플럭스',
    'h_alpha_eqw': 'Hα 등가폭', 'oiii_5007_eqw': '[OIII] 등가폭',
}


def _valid(v):
    if v is None:
        return False
    try:
        f = float(v)
    except (TypeError, ValueError):
        return False
    return np.isfinite(f)


def resolve_features(properties: dict, feature_names) -> dict:
    """속성 dict 에서 학습 특성 이름별 값을 별칭까지 고려해 추출 (없으면 키 생략)"""
    out = {}
    for feat in feature_names:
        for key in FEATURE_ALIASES.get(feat, [feat]):
            if key in properties and _valid(properties[key]):
                out[feat] = float(properties[key])
                break
    if 'log_ssfr' in feature_names and 'log_ssfr' not in out \
            and 'log_sfr' in out and 'log_stellar_mass' in out:
        out['log_ssfr'] = out['log_sfr'] - out['log_stellar_mass']
    return out


class GalaxyPredictor:
    CLUSTER_NAMES = {
        0: '저질량 젊은별생성 (Low-mass Young Star-Forming)',
        1: '중간형/전이은하 (Intermediate/Transition)',
        2: '고질량 나선/원반 (High-mass Spiral/Disk)',
        3: '진화완료 적색타원 (Fully Evolved Red Elliptical)',
    }

    CLUSTER_COLORS = {0: '#3b82f6', 1: '#22c55e', 2: '#f59e0b', 3: '#ef4444'}

    CLASS_COLORS = {
        '나선은하 (Spiral Galaxy)': '#3b82f6',
        '막대나선은하 (Barred Spiral Galaxy)': '#60a5fa',
        '타원은하 (Elliptical Galaxy)': '#ef4444',
        '렌즈형은하 (Lenticular Galaxy)': '#f97316',
        '마젤란형 은하 (Magellanic Galaxy)': '#8b5cf6',
        '고리은하 (Ring Galaxy)': '#eab308',
        '전파은하 (Radio Galaxy)': '#d946ef',
        '퀘이사 (Quasar)': '#06b6d4',
        '세이퍼트은하 (Seyfert Galaxy)': '#14b8a6',
        '불규칙은하 (Irregular Galaxy)': '#84cc16',
        '병합은하 (Merger Galaxy)': '#f43f5e'
    }

    def __init__(self, model_dir: str, master_csv: str = None):
        self.model_dir = model_dir
        self.master_csv = master_csv
        self.is_loaded = False
        self.is_fallback = False
        self.rf_model = None
        self.scaler = None
        self.kmeans_model = None
        self.class_labels = None
        self.trained_features = None
        self.load_error = None

        self._load_models()
        if not self.is_loaded and master_csv:
            self._train_fallback(master_csv)

    # ── 로딩 ─────────────────────────────────────────────
    def _load_models(self):
        try:
            self.rf_model = joblib.load(os.path.join(self.model_dir, 'rf_galaxy_classifier_11class.pkl'))
            self.scaler = joblib.load(os.path.join(self.model_dir, 'feature_scaler.pkl'))
            self.kmeans_model = joblib.load(os.path.join(self.model_dir, 'kmeans_model.pkl'))
            self.class_labels = list(joblib.load(os.path.join(self.model_dir, 'class_labels.pkl')))
            self.trained_features = list(joblib.load(os.path.join(self.model_dir, 'trained_features.pkl')))
            self.is_loaded = True
            logging.info("모든 머신러닝 모델이 성공적으로 로드되었습니다.")
        except FileNotFoundError as e:
            self.load_error = str(e)
            logging.warning("모델 파일을 찾을 수 없습니다: %s", e)
            self.is_loaded = False
        except Exception as e:
            self.load_error = str(e)
            logging.error("모델 로드 중 오류 발생: %s", e)
            self.is_loaded = False

    def _train_fallback(self, master_csv):
        """사전학습 모델이 없을 때 마스터 CSV 로 경량 대체 모델 학습 (class_detail 라벨)"""
        try:
            from sklearn.ensemble import RandomForestClassifier
            from sklearn.preprocessing import StandardScaler
            from sklearn.cluster import KMeans
            df = pd.read_csv(master_csv)
            colmap = {'lgm_tot_p50': 'log_stellar_mass', 'sfr_tot_p50': 'log_sfr',
                      'oh_p50': 'metallicity_oh'}
            df = df.rename(columns=colmap)
            feats = [c for c in ['log_stellar_mass', 'log_sfr', 'log_ssfr', 'metallicity_oh', 'd4000_n',
                                 'velDisp', 'z', 'color_u_r', 'log_nii_ha', 'log_oiii_hb', 'petroR50_r']
                     if c in df.columns]
            label_col = 'class_detail' if 'class_detail' in df.columns else 'class_morphology'
            d = df[feats + [label_col]].dropna()
            if len(d) > 30000:
                d = d.sample(30000, random_state=42)
            self.scaler = StandardScaler().fit(d[feats])
            X = self.scaler.transform(d[feats])
            self.rf_model = RandomForestClassifier(n_estimators=60, max_depth=14, n_jobs=-1,
                                                   random_state=42).fit(X, d[label_col].astype(str))
            self.kmeans_model = KMeans(n_clusters=4, n_init=5, random_state=42).fit(X)
            self.class_labels = list(self.rf_model.classes_)
            self.trained_features = feats
            self.is_loaded = True
            self.is_fallback = True
            logging.info("대체 모델 학습 완료 (%d 샘플, %d 특성)", len(d), len(feats))
        except Exception as e:
            self.load_error = (self.load_error or '') + ' / fallback: %s' % e
            self.is_loaded = False

    # ── 특성 ─────────────────────────────────────────────
    def feature_coverage(self, properties: dict) -> dict:
        """입력 특성 커버리지 (중요도 가중) — 예측 신뢰성 지표"""
        if not self.is_loaded:
            return {'n_provided': 0, 'n_total': 0, 'weighted': 0.0, 'provided': [], 'missing': []}
        got = resolve_features(properties, self.trained_features)
        imp = getattr(self.rf_model, 'feature_importances_', np.ones(len(self.trained_features)))
        imp = np.asarray(imp) / (np.sum(imp) or 1.0)
        weighted = float(sum(w for f, w in zip(self.trained_features, imp) if f in got))
        return {
            'n_provided': len(got), 'n_total': len(self.trained_features), 'weighted': weighted,
            'provided': [f for f in self.trained_features if f in got],
            'missing': [f for f in self.trained_features if f not in got],
        }

    def _prepare_features(self, properties: dict) -> np.ndarray:
        """누락 특성은 학습 평균(=표준화 후 0)으로 대체 → 분포 밖 값(0.0) 주입 방지"""
        if not self.is_loaded or not self.trained_features:
            return np.array([])
        got = resolve_features(properties, self.trained_features)
        means = getattr(self.scaler, 'mean_', np.zeros(len(self.trained_features)))
        values = [got.get(f, float(m)) for f, m in zip(self.trained_features, means)]
        X_df = pd.DataFrame([values], columns=self.trained_features)
        return self.scaler.transform(X_df)

    # ── 예측 ─────────────────────────────────────────────
    def predict_galaxy_type(self, properties: dict) -> dict:
        default_result = {
            'predicted_class': '알 수 없음 (Unknown)',
            'confidence': 0.0,
            'probabilities': {},
            'top_3': []
        }
        if not self.is_loaded:
            return default_result
        try:
            X_scaled = self._prepare_features(properties)
            if len(X_scaled) == 0:
                return default_result
            probs = self.rf_model.predict_proba(X_scaled)[0]
            labels = list(self.rf_model.classes_) if self.is_fallback else self.class_labels
            prob_dict = {label: float(prob) for label, prob in zip(labels, probs)}
            sorted_probs = sorted(prob_dict.items(), key=lambda x: x[1], reverse=True)
            cov = self.feature_coverage(properties)
            return {
                'predicted_class': sorted_probs[0][0],
                'confidence': sorted_probs[0][1],
                'probabilities': prob_dict,
                'top_3': sorted_probs[:3],
                'coverage': cov,
            }
        except Exception as e:
            logging.error("분류 예측 중 오류: %s", e)
            return default_result

    def predict_evolution_cluster(self, properties: dict) -> dict:
        default_result = {
            'cluster_id': -1,
            'cluster_name': '알 수 없음',
            'cluster_color': '#808080',
            'distances': []
        }
        if not self.is_loaded:
            return default_result
        try:
            X_scaled = self._prepare_features(properties)
            if len(X_scaled) == 0:
                return default_result
            cluster_id = int(self.kmeans_model.predict(X_scaled)[0])
            distances = self.kmeans_model.transform(X_scaled)[0].tolist()
            d = np.asarray(distances)
            # 거리 기반 소속 확률 (softmax of -d)
            w = np.exp(-(d - d.min()))
            memb = (w / w.sum()).tolist()
            return {
                'cluster_id': cluster_id,
                'cluster_name': self.CLUSTER_NAMES.get(cluster_id, '군집 %d' % cluster_id),
                'cluster_color': self.CLUSTER_COLORS.get(cluster_id, '#808080'),
                'distances': distances,
                'membership': memb,
            }
        except Exception as e:
            logging.error("진화 단계 군집 예측 중 오류: %s", e)
            return default_result

    def get_feature_importance(self, properties: dict) -> dict:
        default_result = {'global_importance': [], 'top_features': []}
        if not self.is_loaded:
            return default_result
        try:
            importances = self.rf_model.feature_importances_
            global_imp = list(zip(self.trained_features, importances))
            global_imp.sort(key=lambda x: x[1], reverse=True)
            got = resolve_features(properties, self.trained_features)
            top_features = [(feat, imp, got.get(feat)) for feat, imp in global_imp[:10]]
            return {'global_importance': global_imp, 'top_features': top_features}
        except Exception as e:
            logging.error("특성 중요도 계산 중 오류: %s", e)
            return default_result

    def explain_local(self, properties: dict, top_k: int = 10) -> list:
        """개별 천체 XAI: 입력된 각 특성을 학습 평균으로 되돌렸을 때 예측 클래스 확률 변화량.
        양수 = 그 특성이 현재 예측을 지지함. Returns [(feature, delta_prob, value)]"""
        if not self.is_loaded:
            return []
        try:
            got = resolve_features(properties, self.trained_features)
            if not got:
                return []
            base_X = self._prepare_features(properties)
            base_p = self.rf_model.predict_proba(base_X)[0]
            k = int(np.argmax(base_p))
            rows = []
            idx = {f: i for i, f in enumerate(self.trained_features)}
            batch = []
            names = []
            for f in got:
                X = base_X.copy()
                X[0, idx[f]] = 0.0  # 표준화 공간의 평균
                batch.append(X[0])
                names.append(f)
            probs = self.rf_model.predict_proba(np.vstack(batch))[:, k]
            for f, p in zip(names, probs):
                rows.append((f, float(base_p[k] - p), got[f]))
            rows.sort(key=lambda r: abs(r[1]), reverse=True)
            return rows[:top_k]
        except Exception as e:
            logging.error("로컬 설명 계산 오류: %s", e)
            return []

    # ── 차트 ─────────────────────────────────────────────
    def create_probability_chart(self, probabilities: dict) -> go.Figure:
        fig = go.Figure()
        if not probabilities:
            fig.update_layout(template='plotly_dark', title="확률 데이터 없음")
            return fig
        sorted_probs = sorted(probabilities.items(), key=lambda x: x[1], reverse=False)
        labels = [item[0] for item in sorted_probs]
        values = [item[1] * 100 for item in sorted_probs]
        colors = [self.CLASS_COLORS.get(label, '#64748b') for label in labels]
        fig.add_trace(go.Bar(
            y=labels, x=values, orientation='h', marker_color=colors,
            text=["%.1f%%" % v for v in values], textposition='auto',
        ))
        fig.update_layout(
            template='plotly_dark', title='은하 유형 예측 확률',
            xaxis_title='확률 (%)', height=420, margin=dict(l=20, r=20, t=40, b=20)
        )
        return fig

    def create_feature_importance_chart(self, importance_data: dict) -> go.Figure:
        fig = go.Figure()
        top_features = importance_data.get('top_features', [])
        if not top_features:
            fig.update_layout(template='plotly_dark', title="특성 중요도 데이터 없음")
            return fig
        top_features = top_features[::-1]
        labels = ["%s%s" % (FEATURE_LABELS_KO.get(item[0], item[0]), '' if item[2] is not None else ' (미입력)')
                  for item in top_features]
        values = [item[1] for item in top_features]
        colors = ['#60a5fa' if item[2] is not None else '#475569' for item in top_features]
        fig.add_trace(go.Bar(
            y=labels, x=values, orientation='h', marker_color=colors,
            text=["%.3f" % v for v in values], textposition='outside',
        ))
        fig.update_layout(
            template='plotly_dark', title='전역 특성 중요도 (파랑=입력됨, 회색=평균대체)',
            xaxis_title='중요도', height=420, margin=dict(l=20, r=20, t=40, b=20)
        )
        return fig

    def create_local_explanation_chart(self, rows: list, predicted_class: str = '') -> go.Figure:
        fig = go.Figure()
        if not rows:
            fig.update_layout(template='plotly_dark', title='개별 설명 데이터 없음 (입력 특성 부족)', height=300)
            return fig
        rows = rows[::-1]
        labels = ["%s = %.2f" % (FEATURE_LABELS_KO.get(f, f), v) for f, d, v in rows]
        vals = [d * 100 for f, d, v in rows]
        fig.add_trace(go.Bar(
            y=labels, x=vals, orientation='h',
            marker_color=['#22c55e' if v >= 0 else '#ef4444' for v in vals],
            text=["%+.1f%%p" % v for v in vals], textposition='outside',
        ))
        fig.update_layout(
            template='plotly_dark',
            title='이 천체의 예측 근거 — "%s" 확률 기여도' % predicted_class.split(' (')[0],
            xaxis_title='기여도 (%p, 초록=지지 / 빨강=반대)', height=max(300, 40 * len(rows) + 80),
            margin=dict(l=20, r=40, t=50, b=20)
        )
        return fig

    def create_evolution_gauge(self, gei_score: float) -> go.Figure:
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=gei_score,
            title={'text': "은하 진화 지수 (GEI)"},
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {'color': "white"},
                'steps': [
                    {'range': [0, 25], 'color': "#1d4ed8"},
                    {'range': [25, 45], 'color': "#0ea5e9"},
                    {'range': [45, 65], 'color': "#22c55e"},
                    {'range': [65, 85], 'color': "#f59e0b"},
                    {'range': [85, 100], 'color': "#dc2626"}
                ],
            }
        ))
        fig.update_layout(template='plotly_dark', height=280, margin=dict(l=20, r=20, t=50, b=20))
        return fig

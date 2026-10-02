import os
import numpy as np
import pandas as pd
import joblib
import plotly.graph_objects as go
import logging

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

    def __init__(self, model_dir: str):
        self.model_dir = model_dir
        self.is_loaded = False
        self.rf_model = None
        self.scaler = None
        self.kmeans_model = None
        self.class_labels = None
        self.trained_features = None
        
        self._load_models()
        
    def _load_models(self):
        try:
            self.rf_model = joblib.load(os.path.join(self.model_dir, 'rf_galaxy_classifier_11class.pkl'))
            self.scaler = joblib.load(os.path.join(self.model_dir, 'feature_scaler.pkl'))
            self.kmeans_model = joblib.load(os.path.join(self.model_dir, 'kmeans_model.pkl'))
            self.class_labels = joblib.load(os.path.join(self.model_dir, 'class_labels.pkl'))
            self.trained_features = joblib.load(os.path.join(self.model_dir, 'trained_features.pkl'))
            self.is_loaded = True
            logging.info("모든 머신러닝 모델이 성공적으로 로드되었습니다.")
        except FileNotFoundError as e:
            logging.warning(f"모델 파일을 찾을 수 없습니다: {e}")
            self.is_loaded = False
        except Exception as e:
            logging.error(f"모델 로드 중 오류 발생: {e}")
            self.is_loaded = False

    def _prepare_features(self, properties: dict) -> np.ndarray:
        if not self.is_loaded or not self.trained_features:
            return np.array([])
            
        feature_values = []
        for feature in self.trained_features:
            # 기본값은 0.0으로 처리 (누락된 특성 처리)
            val = properties.get(feature, 0.0)
            if val is None or (isinstance(val, float) and np.isnan(val)):
                val = 0.0
            feature_values.append(float(val))
            
        # DataFrame으로 변환하여 feature name 경고 방지
        X_df = pd.DataFrame([feature_values], columns=self.trained_features)
        X_scaled = self.scaler.transform(X_df)
        return X_scaled

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
            
            prob_dict = {label: prob for label, prob in zip(self.class_labels, probs)}
            
            # 확률순 정렬
            sorted_probs = sorted(prob_dict.items(), key=lambda x: x[1], reverse=True)
            
            top_class = sorted_probs[0][0]
            confidence = sorted_probs[0][1]
            top_3 = sorted_probs[:3]
            
            return {
                'predicted_class': top_class,
                'confidence': confidence,
                'probabilities': prob_dict,
                'top_3': top_3
            }
        except Exception as e:
            logging.error(f"분류 예측 중 오류: {e}")
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
            
            return {
                'cluster_id': cluster_id,
                'cluster_name': self.CLUSTER_NAMES.get(cluster_id, '알 수 없음'),
                'cluster_color': self.CLUSTER_COLORS.get(cluster_id, '#808080'),
                'distances': distances
            }
        except Exception as e:
            logging.error(f"진화 단계 군집 예측 중 오류: {e}")
            return default_result

    def get_feature_importance(self, properties: dict) -> dict:
        default_result = {
            'global_importance': [],
            'top_features': []
        }
        
        if not self.is_loaded:
            return default_result
            
        try:
            importances = self.rf_model.feature_importances_
            
            global_imp = [
                (feat, imp) for feat, imp in zip(self.trained_features, importances)
            ]
            global_imp.sort(key=lambda x: x[1], reverse=True)
            
            # 입력 값에 따른 상위 10개 특성 추출
            top_features = []
            for feat, imp in global_imp[:10]:
                val = properties.get(feat, 0.0)
                top_features.append((feat, imp, val))
                
            return {
                'global_importance': global_imp,
                'top_features': top_features
            }
        except Exception as e:
            logging.error(f"특성 중요도 계산 중 오류: {e}")
            return default_result

    def create_probability_chart(self, probabilities: dict) -> go.Figure:
        fig = go.Figure()
        if not probabilities:
            fig.update_layout(template='plotly_dark', title="확률 데이터 없음")
            return fig
            
        sorted_probs = sorted(probabilities.items(), key=lambda x: x[1], reverse=False)
        labels = [item[0] for item in sorted_probs]
        values = [item[1] * 100 for item in sorted_probs]  # 백분율 변환
        
        colors = [self.CLASS_COLORS.get(label, '#808080') for label in labels]
        
        fig.add_trace(go.Bar(
            y=labels,
            x=values,
            orientation='h',
            marker_color=colors,
            text=[f"{v:.1f}%" for v in values],
            textposition='auto',
        ))
        
        fig.update_layout(
            template='plotly_dark',
            title='은하 형태 예측 확률 (Galaxy Classification Probabilities)',
            xaxis_title='확률 (%)',
            yaxis_title='은하 분류',
            height=400,
            margin=dict(l=20, r=20, t=40, b=20)
        )
        return fig

    def create_feature_importance_chart(self, importance_data: dict) -> go.Figure:
        fig = go.Figure()
        top_features = importance_data.get('top_features', [])
        
        if not top_features:
            fig.update_layout(template='plotly_dark', title="특성 중요도 데이터 없음")
            return fig
            
        # 가로 막대 그래프를 위해 역순 정렬 (높은 값이 위로 오도록)
        top_features = top_features[::-1]
        
        labels = [item[0] for item in top_features]
        values = [item[1] for item in top_features]
        
        fig.add_trace(go.Bar(
            y=labels,
            x=values,
            orientation='h',
            marker=dict(
                color=values,
                colorscale='Viridis',
                showscale=True
            ),
            text=[f"{v:.4f}" for v in values],
            textposition='outside',
        ))
        
        fig.update_layout(
            template='plotly_dark',
            title='주요 예측 기여 특성 (Top Feature Importances)',
            xaxis_title='중요도 (Importance Score)',
            yaxis_title='특성 (Feature)',
            height=400,
            margin=dict(l=20, r=20, t=40, b=20)
        )
        return fig

    def create_evolution_gauge(self, gei_score: float) -> go.Figure:
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=gei_score,
            title={'text': "은하 진화 지수 (GEI)"},
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {'color': "white"},
                'steps': [
                    {'range': [0, 25], 'color': "blue"},
                    {'range': [25, 45], 'color': "green"},
                    {'range': [45, 65], 'color': "yellow"},
                    {'range': [65, 85], 'color': "orange"},
                    {'range': [85, 100], 'color': "red"}
                ],
            }
        ))
        
        fig.update_layout(
            template='plotly_dark',
            height=300,
            margin=dict(l=20, r=20, t=50, b=20)
        )
        return fig

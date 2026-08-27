import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix, roc_curve, auc
from sklearn.preprocessing import label_binarize
import joblib
import config

# 한글 폰트 설정
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

def run_clustering_and_classification():
    print("--- 머신러닝 파이프라인 시작 ---")
    
    # 1. 데이터 로드
    if not os.path.exists(config.MASTER_DATASET_FILE):
        print(f"데이터 파일이 존재하지 않습니다: {config.MASTER_DATASET_FILE}")
        return
        
    df = pd.read_csv(config.MASTER_DATASET_FILE)
    print(f"데이터 로드 완료: {len(df)}개")
    
    # 방어코드: 필요한 피처들이 없을 수도 있음. 방출선 비율이 없을 수 있으니 확인
    if 'log_nii_ha' not in df.columns:
        df['log_nii_ha'] = np.where((df['nii_6584_flux'] > 0) & (df['h_alpha_flux'] > 0), 
                                    np.log10(df['nii_6584_flux'] / df['h_alpha_flux']), np.nan)
    if 'log_oiii_hb' not in df.columns:
        df['log_oiii_hb'] = np.where((df['oiii_5007_flux'] > 0) & (df['h_beta_flux'] > 0), 
                                     np.log10(df['oiii_5007_flux'] / df['h_beta_flux']), np.nan)
    
    # 2. Features 선택 (물리, 화학적 주요 변수)
    features = ['log_stellar_mass', 'log_sfr', 'u_g', 'g_r', 'log_nii_ha', 'log_oiii_hb', 'veldisp']
    available_features = [f for f in features if f in df.columns]
    
    # 누락된 데이터 제거
    ml_df = df.dropna(subset=available_features).copy()
    print(f"결측치 제거 후 모델링용 데이터: {len(ml_df)}개")
    
    if len(ml_df) < 100:
        print("데이터가 부족하여 ML 파이프라인을 실행할 수 없습니다.")
        return
        
    X = ml_df[available_features]
    
    # 3. 정규화
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # 4. K-Means 군집화 (특이 은하 군집 4개)
    n_clusters = 4
    print(f"K-Means 군집화 진행 중... (군집 수: {n_clusters})")
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    ml_df['ml_cluster_id'] = kmeans.fit_predict(X_scaled)
    
    # 군집 라벨을 직관적으로 변경 (크기에 따라 분류)
    cluster_centers = pd.DataFrame(scaler.inverse_transform(kmeans.cluster_centers_), columns=available_features)
    # 질량 기준으로 정렬하여 이름 부여 (간이 방식)
    sorted_idx = cluster_centers['log_stellar_mass'].sort_values().index if 'log_stellar_mass' in cluster_centers else cluster_centers.index
    cluster_mapping = {idx: f"군집 {i}" for i, idx in enumerate(sorted_idx)}
    ml_df['cluster_name'] = ml_df['ml_cluster_id'].map(cluster_mapping)
    
    # 마스터 데이터셋 업데이트
    # ml_df의 ml_cluster_id를 원본 df에 결합
    if 'ml_cluster_id' in df.columns:
        df = df.drop(columns=['ml_cluster_id', 'cluster_name'], errors='ignore')
    
    # 인덱스 유지하면서 결합
    df = df.join(ml_df[['ml_cluster_id', 'cluster_name']])
    df.to_csv(config.MASTER_DATASET_FILE, index=False)
    print("군집화 결과를 마스터 데이터셋에 업데이트 완료.")
    
    # 5. Random Forest 분류기 훈련
    print("Random Forest 군집 분류 모델 학습 중...")
    y = ml_df['ml_cluster_id']
    X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)
    
    rf_model = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
    rf_model.fit(X_train, y_train)
    
    y_pred = rf_model.predict(X_test)
    
    # 6. 결과 평가 및 시각화
    print("모델 평가 중...")
    
    # Feature Importance
    importances = rf_model.feature_importances_
    indices = np.argsort(importances)[::-1]
    
    plt.figure(figsize=(10, 6))
    plt.title("Random Forest - 특징 중요도 (Feature Importances)")
    plt.bar(range(X.shape[1]), importances[indices], align="center", color='skyblue')
    plt.xticks(range(X.shape[1]), [available_features[i] for i in indices], rotation=45)
    plt.tight_layout()
    plt.savefig(os.path.join(config.PLOT_DIR, "feature_importance.png"), dpi=300)
    plt.close()
    
    # Confusion Matrix
    cm = confusion_matrix(y_test, y_pred)
    plt.figure(figsize=(8, 6))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues')
    plt.title('혼동 행렬 (Confusion Matrix)')
    plt.xlabel('예측된 군집')
    plt.ylabel('실제 군집')
    plt.tight_layout()
    plt.savefig(os.path.join(config.PLOT_DIR, "confusion_matrix.png"), dpi=300)
    plt.close()
    
    # ROC Curve
    y_test_bin = label_binarize(y_test, classes=[0, 1, 2, 3])
    y_score = rf_model.predict_proba(X_test)
    
    plt.figure(figsize=(8, 6))
    for i in range(n_clusters):
        # 방어코드: 테스트 셋에 특정 클래스가 없을 수 있음
        if np.sum(y_test_bin[:, i]) > 0:
            fpr, tpr, _ = roc_curve(y_test_bin[:, i], y_score[:, i])
            roc_auc = auc(fpr, tpr)
            plt.plot(fpr, tpr, lw=2, label=f'Cluster {i} (AUC = {roc_auc:.2f})')
        
    plt.plot([0, 1], [0, 1], 'k--', lw=2)
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel('거짓 양성 비율 (False Positive Rate)')
    plt.ylabel('참 양성 비율 (True Positive Rate)')
    plt.title('ROC 곡선 (다중 클래스)')
    plt.legend(loc="lower right")
    plt.tight_layout()
    plt.savefig(os.path.join(config.PLOT_DIR, "roc_curve.png"), dpi=300)
    plt.close()
    
    # 7. 모델 저장
    print("학습된 모델 및 스케일러 저장 중...")
    os.makedirs(config.MODEL_DIR, exist_ok=True)
    joblib.dump(rf_model, os.path.join(config.MODEL_DIR, "rf_cluster_model.pkl"))
    joblib.dump(scaler, os.path.join(config.MODEL_DIR, "feature_scaler.pkl"))
    joblib.dump(kmeans, os.path.join(config.MODEL_DIR, "kmeans_model.pkl"))
    
    print("--- 머신러닝 파이프라인 완료 ---")

if __name__ == "__main__":
    run_clustering_and_classification()

import os
import sys
import io
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import StandardScaler, label_binarize
from sklearn.cluster import KMeans
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix, roc_curve, auc, accuracy_score
import joblib

# UTF-8 설정 및 한글 폰트 설정
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

sys.path.append(r"c:\Users\neato\Desktop\정현\03_과학탐구_대회\YSC_대회")
import config

def run_clustering_and_classification():
    print("="*60)
    print("--- 200개 물리량 기반 11대 은하 분류 머신러닝 파이프라인 시작 ---")
    print("="*60)
    
    # 1. 데이터 로드
    if not os.path.exists(config.MASTER_DATASET_FILE):
        print(f"데이터 파일이 존재하지 않습니다: {config.MASTER_DATASET_FILE}")
        return
        
    df = pd.read_csv(config.MASTER_DATASET_FILE)
    print(f"데이터 로드 완료: 총 {len(df):,}개 은하")
    print(f"포함된 은하 분류: {df['galaxy_type'].nunique()}개 분류")
    
    # 2. 모델 학습용 핵심 물리량 피처 선정
    feature_candidates = [
        'log_stellar_mass', 'log_sfr', 'log_ssfr', 'metallicity_oh', 'd4000_n',
        'velDisp', 'z', 'color_u_r', 'concentration_index_r',
        'petroMag_u', 'petroMag_g', 'petroMag_r', 'petroMag_i', 'petroMag_z',
        'petroR50_r', 'petroR90_r', 'fracDeV_r', 'deVAB_r', 'expAB_r',
        'log_nii_ha', 'log_oiii_hb', 'log_sii_ha', 'dust_ebv',
        'gz_p_el', 'gz_p_cs', 'gz_p_mg', 'gz2_bar_prob', 'gz2_ring_prob',
        'first_radio_flux', 'h_alpha_eqw', 'oiii_5007_eqw'
    ]
    
    features = [f for f in feature_candidates if f in df.columns]
    print(f"학습에 사용할 핵심 물리량 피처: {len(features)}개")
    
    # 결측치 처리 및 정제
    ml_df = df.copy()
    ml_df = ml_df.replace([np.inf, -np.inf], np.nan).dropna(subset=features + ['galaxy_type'])
    print(f"정제 후 학습 데이터: {len(ml_df):,}개")
    
    X = ml_df[features]
    y_raw = ml_df['galaxy_type']
    
    # 라벨 인코딩
    classes = sorted(y_raw.unique())
    label_to_idx = {c: i for i, c in enumerate(classes)}
    y = y_raw.map(label_to_idx)
    
    # 3. 데이터 정규화
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # 4. K-Means 비지도 군집화 (4대 진화 군집)
    n_clusters = 4
    print(f"\n[1] K-Means 다차원 군집화 진행 중... (군집 수: {n_clusters})")
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    ml_df['ml_cluster_id'] = kmeans.fit_predict(X_scaled)
    cluster_mapping = {0: "군집 0 (저질량 젊은별생성)", 1: "군집 1 (중간형/전이은하)", 2: "군집 2 (고질량 나선/원반)", 3: "군집 3 (진화완료 적색타원)"}
    ml_df['cluster_name'] = ml_df['ml_cluster_id'].map(cluster_mapping)
    
    # 5. 지도학습: 11개 은하 분류 Random Forest 학습
    print("\n[2] Random Forest 11대 은하 분류 모델 학습 중...")
    X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42, stratify=y)
    
    rf_model = RandomForestClassifier(n_estimators=120, max_depth=20, random_state=42, n_jobs=-1)
    rf_model.fit(X_train, y_train)
    
    y_pred = rf_model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    print(f"[검증 결과] 모델 검증 정확도 (Accuracy): {acc*100:.2f}%")
    print("\n[분류 성능 상세 보고서]")
    print(classification_report(y_test, y_pred, target_names=classes))
    
    # 6. 시각화 및 평가 도표 생성
    os.makedirs(config.PLOT_DIR, exist_ok=True)
    
    # ① Feature Importance
    importances = rf_model.feature_importances_
    indices = np.argsort(importances)[::-1][:20]
    
    plt.figure(figsize=(12, 7))
    plt.title("200개 물리량 기반 Random Forest - 은하 분류 핵심 피처 중요도 (Top 20)", fontsize=14, pad=15)
    plt.bar(range(len(indices)), importances[indices], align="center", color='#3b82f6', edgecolor='#1d4ed8')
    plt.xticks(range(len(indices)), [features[i] for i in indices], rotation=45, ha='right', fontsize=10)
    plt.ylabel("상대적 중요도 (Gini Importance)", fontsize=12)
    plt.grid(axis='y', linestyle='--', alpha=0.5)
    plt.tight_layout()
    feat_path = os.path.join(config.PLOT_DIR, "feature_importance.png")
    plt.savefig(feat_path, dpi=300)
    plt.close()
    print(f" - 피처 중요도 도표 저장: {feat_path}")
    
    # ② Confusion Matrix (11개 클래스)
    cm = confusion_matrix(y_test, y_pred)
    plt.figure(figsize=(11, 9))
    short_classes = [c.split(" (")[0] for c in classes]
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=short_classes, yticklabels=short_classes)
    plt.title(f'11대 은하 분류 혼동 행렬 (Confusion Matrix, 정확도: {acc*100:.1f}%)', fontsize=14, pad=15)
    plt.xlabel('예측된 은하 분류', fontsize=12)
    plt.ylabel('실제 은하 분류', fontsize=12)
    plt.xticks(rotation=45, ha='right')
    plt.yticks(rotation=0)
    plt.tight_layout()
    cm_path = os.path.join(config.PLOT_DIR, "confusion_matrix.png")
    plt.savefig(cm_path, dpi=300)
    plt.close()
    print(f" - 혼동 행렬 도표 저장: {cm_path}")
    
    # ③ ROC Curve
    y_test_bin = label_binarize(y_test, classes=list(range(len(classes))))
    y_score = rf_model.predict_proba(X_test)
    
    plt.figure(figsize=(10, 8))
    for i in range(len(classes)):
        fpr, tpr, _ = roc_curve(y_test_bin[:, i], y_score[:, i])
        roc_auc = auc(fpr, tpr)
        plt.plot(fpr, tpr, lw=2, label=f'{short_classes[i]} (AUC = {roc_auc:.3f})')
        
    plt.plot([0, 1], [0, 1], 'k--', lw=1.5)
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel('거짓 양성 비율 (False Positive Rate)', fontsize=12)
    plt.ylabel('참 양성 비율 (True Positive Rate)', fontsize=12)
    plt.title('11대 은하 분류 다중 클래스 ROC 곡선 (Multi-Class ROC)', fontsize=14, pad=15)
    plt.legend(loc="lower right", fontsize=9)
    plt.grid(True, linestyle='--', alpha=0.4)
    plt.tight_layout()
    roc_path = os.path.join(config.PLOT_DIR, "roc_curve.png")
    plt.savefig(roc_path, dpi=300)
    plt.close()
    print(f" - ROC 곡선 도표 저장: {roc_path}")
    
    # 7. 모델 및 스케일러 저장
    os.makedirs(config.MODEL_DIR, exist_ok=True)
    joblib.dump(rf_model, os.path.join(config.MODEL_DIR, "rf_galaxy_classifier_11class.pkl"))
    joblib.dump(scaler, os.path.join(config.MODEL_DIR, "feature_scaler.pkl"))
    joblib.dump(kmeans, os.path.join(config.MODEL_DIR, "kmeans_model.pkl"))
    joblib.dump(classes, os.path.join(config.MODEL_DIR, "class_labels.pkl"))
    joblib.dump(features, os.path.join(config.MODEL_DIR, "trained_features.pkl"))
    
    print("\n[완료] 모든 신규 모델 및 스케일러 저장 완료!")
    print(f" - 모델 저장 위치: {config.MODEL_DIR}")
    print("="*60)

if __name__ == "__main__":
    run_clustering_and_classification()

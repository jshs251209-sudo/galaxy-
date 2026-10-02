"""
다차원 위상공간 매핑 모듈 — SDSS 배경 데이터 위에 대상 천체를 오버레이
BPT 진단도, 별생성 주계열(SFMS), 질량-금속량(MZR), 색-질량 도표, 3D FMR
"""
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os


class PhaseSpaceMapper:
    """SDSS 배경 데이터 위에 대상 천체를 오버레이하는 위상공간 시각화 엔진"""

    # BPT 분류 색상 (숫자 → 문자열 매핑용)
    BPT_MAP = {1: 'Star-Forming', 2: 'Low S/N SF', 3: 'Composite',
               4: 'Seyfert', 5: 'LINER', -1: 'Unclassified'}
    BPT_COLORS = {
        'Star-Forming': '#3b82f6', 'Composite': '#22c55e',
        'Seyfert': '#ef4444', 'LINER': '#f97316',
        'Low S/N SF': '#93c5fd', 'Unclassified': '#6b7280'
    }

    # class_detail 색상 (실제 데이터의 분류 컬럼)
    DETAIL_COLORS = {
        '나선은하': '#2563eb',
        '타원은하': '#dc2626',
        '막대나선은하': '#0284c7',
        '불규칙은하': '#10b981',
        '불규칙 은하': '#10b981',
        '일반 원반/타원 은하 (Standard Disk/Spheroid)': '#94a3b8',
        '렌즈형은하': '#ea580c',
    }

    # class_morphology 색상 (더 거친 4분류)
    MORPH_COLORS = {
        '나선': '#2563eb', '타원': '#dc2626',
        '불규칙은하': '#10b981', '렌즈': '#ea580c',
    }

    def __init__(self, master_csv_path: str):
        """마스터 데이터셋 로드. 성능을 위해 20,000개 이하로 샘플링."""
        self.df = self._load_data(master_csv_path)

    def _load_data(self, path: str) -> pd.DataFrame:
        """데이터 로드 및 전처리"""
        if not os.path.exists(path):
            return pd.DataFrame()

        try:
            df = pd.read_csv(path)

            # BPT 문자열 레이블 생성
            if 'bptclass' in df.columns:
                df['bpt_label'] = df['bptclass'].map(self.BPT_MAP).fillna('Unclassified')
            else:
                df['bpt_label'] = 'Unclassified'

            # 분류 컬럼 결정 (class_detail > class_morphology > bpt_label 순)
            if 'class_detail' in df.columns:
                self._color_col = 'class_detail'
                self._color_map = self.DETAIL_COLORS
            elif 'class_morphology' in df.columns:
                self._color_col = 'class_morphology'
                self._color_map = self.MORPH_COLORS
            else:
                self._color_col = 'bpt_label'
                self._color_map = self.BPT_COLORS

            # 20,000개 이하로 샘플링 (성층 표본)
            if len(df) > 20000:
                df = df.sample(n=20000, random_state=42).reset_index(drop=True)

            return df
        except Exception as e:
            print("데이터 로드 오류: %s" % str(e))
            return pd.DataFrame()

    def _empty_figure(self, message: str) -> go.Figure:
        """빈 데이터 시 표시할 기본 Figure"""
        fig = go.Figure()
        fig.add_annotation(
            text=message, xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False, font=dict(size=16, color='#94a3b8')
        )
        fig.update_layout(template='plotly_dark', height=400)
        return fig

    def _add_scatter_by_category(self, fig, x_col, y_col, size=2, opacity=0.3):
        """분류 컬럼별로 색상을 분리해서 배경 산점도 추가"""
        if x_col not in self.df.columns or y_col not in self.df.columns:
            return

        valid = self.df[[x_col, y_col, self._color_col]].dropna()

        for cat_val in valid[self._color_col].unique():
            color = self._color_map.get(cat_val, '#6b7280')
            mask = valid[self._color_col] == cat_val
            subset = valid[mask]
            if len(subset) == 0:
                continue
            label = str(cat_val)
            if len(label) > 15:
                label = label[:15] + '…'
            fig.add_trace(go.Scatter(
                x=subset[x_col], y=subset[y_col],
                mode='markers',
                marker=dict(color=color, size=size, opacity=opacity),
                name=label
            ))

    def _add_target_star(self, fig, x_val, y_val):
        """대상 천체를 붉은 별표로 오버레이"""
        if x_val is not None and y_val is not None:
            fig.add_trace(go.Scatter(
                x=[x_val], y=[y_val],
                mode='markers',
                marker=dict(
                    color='red', size=16, symbol='star',
                    line=dict(color='white', width=1.5)
                ),
                name='★ 대상 천체'
            ))

    # ── BPT 진단 도표 ──────────────────────────────────────
    def plot_bpt(self, target_log_nii_ha=None, target_log_oiii_hb=None) -> go.Figure:
        """BPT 진단 도표 (Baldwin, Phillips & Terlevich 1981)"""
        if self.df.empty:
            return self._empty_figure("데이터 없음")

        fig = go.Figure()

        # 배경 데이터 — BPT 분류별 색상
        if 'log_nii_ha' in self.df.columns and 'log_oiii_hb' in self.df.columns:
            valid = self.df[['log_nii_ha', 'log_oiii_hb', 'bpt_label']].dropna()
            for bpt_val, color in self.BPT_COLORS.items():
                mask = valid['bpt_label'] == bpt_val
                if mask.sum() == 0:
                    continue
                fig.add_trace(go.Scatter(
                    x=valid[mask]['log_nii_ha'],
                    y=valid[mask]['log_oiii_hb'],
                    mode='markers',
                    marker=dict(color=color, size=3, opacity=0.4),
                    name=bpt_val
                ))

        # Kauffmann (2003) 경계선
        x_k = np.linspace(-2.0, 0.04, 100)
        y_k = 0.61 / (x_k - 0.05) + 1.3
        y_k = np.clip(y_k, -2, 2)
        fig.add_trace(go.Scatter(
            x=x_k, y=y_k, mode='lines',
            line=dict(color='cyan', dash='dash', width=1.5),
            name='Kauffmann (2003)'
        ))

        # Kewley (2001) 경계선
        x_kw = np.linspace(-2.0, 0.46, 100)
        y_kw = 0.61 / (x_kw - 0.47) + 1.19
        y_kw = np.clip(y_kw, -2, 2)
        fig.add_trace(go.Scatter(
            x=x_kw, y=y_kw, mode='lines',
            line=dict(color='yellow', dash='dot', width=1.5),
            name='Kewley (2001)'
        ))

        self._add_target_star(fig, target_log_nii_ha, target_log_oiii_hb)

        fig.update_layout(
            title='BPT 진단 도표 (BPT Diagnostic Diagram)',
            xaxis_title='log([N II] / Hα)',
            yaxis_title='log([O III] / Hβ)',
            xaxis_range=[-2, 1], yaxis_range=[-1.5, 1.5],
            template='plotly_dark', height=500
        )
        return fig

    # ── 별생성 주계열 (SFMS) ──────────────────────────────
    def plot_sfms(self, target_log_mass=None, target_log_sfr=None) -> go.Figure:
        """별생성 주계열 (Star-Forming Main Sequence)"""
        if self.df.empty:
            return self._empty_figure("데이터 없음")

        fig = go.Figure()
        self._add_scatter_by_category(fig, 'lgm_tot_p50', 'sfr_tot_p50')

        # 중앙값 추세선
        if 'lgm_tot_p50' in self.df.columns and 'sfr_tot_p50' in self.df.columns:
            try:
                valid = self.df[['lgm_tot_p50', 'sfr_tot_p50']].dropna()
                bins = np.linspace(8, 12, 16)
                centers = 0.5 * (bins[:-1] + bins[1:])
                bin_idx = np.digitize(valid['lgm_tot_p50'], bins) - 1
                medians = []
                for i in range(len(bins) - 1):
                    vals = valid.loc[bin_idx == i, 'sfr_tot_p50']
                    medians.append(vals.median() if len(vals) > 5 else np.nan)
                med_arr = np.array(medians)
                mask = ~np.isnan(med_arr)
                if mask.sum() > 2:
                    fig.add_trace(go.Scatter(
                        x=centers[mask], y=med_arr[mask],
                        mode='lines', line=dict(color='white', width=2.5),
                        name='중앙값 (Median)'
                    ))
            except Exception:
                pass

        self._add_target_star(fig, target_log_mass, target_log_sfr)

        fig.update_layout(
            title='별생성 주계열 (Star-Forming Main Sequence)',
            xaxis_title='항성 질량 log(M★/M☉)',
            yaxis_title='별생성률 log(SFR)',
            xaxis_range=[7, 13], yaxis_range=[-4, 3],
            template='plotly_dark', height=500
        )
        return fig

    # ── 질량-금속량 관계 (MZR) ─────────────────────────────
    def plot_mzr(self, target_log_mass=None, target_metallicity=None) -> go.Figure:
        """질량-금속량 관계 (Mass-Metallicity Relation)"""
        if self.df.empty:
            return self._empty_figure("데이터 없음")

        fig = go.Figure()
        self._add_scatter_by_category(fig, 'lgm_tot_p50', 'oh_p50')

        # Tremonti (2004) 이론 곡선
        x_t04 = np.linspace(8.5, 11.5, 50)
        y_t04 = -1.492 + 1.847 * x_t04 - 0.08026 * (x_t04 ** 2)
        fig.add_trace(go.Scatter(
            x=x_t04, y=y_t04, mode='lines',
            line=dict(color='white', dash='dash', width=2),
            name='Tremonti (2004)'
        ))

        self._add_target_star(fig, target_log_mass, target_metallicity)

        fig.update_layout(
            title='질량-금속량 관계 (Mass-Metallicity Relation)',
            xaxis_title='항성 질량 log(M★/M☉)',
            yaxis_title='금속량 12+log(O/H)',
            xaxis_range=[7, 13], yaxis_range=[7.5, 9.5],
            template='plotly_dark', height=500
        )
        return fig

    # ── 색-질량 이분성 ─────────────────────────────────────
    def plot_color_mass(self, target_log_mass=None, target_color_ur=None) -> go.Figure:
        """색-질량 이분성 도표 (Color-Mass Diagram)"""
        if self.df.empty:
            return self._empty_figure("데이터 없음")

        fig = go.Figure()
        self._add_scatter_by_category(fig, 'lgm_tot_p50', 'color_u_r')

        # Red Sequence / Blue Cloud / Green Valley 경계
        fig.add_hline(y=2.2, line_dash="dash", line_color="red",
                      annotation_text="적색 계열 (Red Sequence)")
        fig.add_hline(y=1.8, line_dash="dash", line_color="deepskyblue",
                      annotation_text="청색 구름 (Blue Cloud)")
        fig.add_hrect(y0=1.8, y1=2.2, line_width=0,
                      fillcolor="green", opacity=0.08)

        self._add_target_star(fig, target_log_mass, target_color_ur)

        fig.update_layout(
            title='색-질량 도표 (Color-Mass Diagram)',
            xaxis_title='항성 질량 log(M★/M☉)',
            yaxis_title='색지수 (u-r)',
            xaxis_range=[7, 13], yaxis_range=[0, 4],
            template='plotly_dark', height=500
        )
        return fig

    # ── 3D 기본금속량관계 (FMR) ────────────────────────────
    def plot_3d_fmr(self, target_mass=None, target_sfr=None, target_z=None) -> go.Figure:
        """3D 기본금속량관계 (Fundamental Metallicity Relation)"""
        if self.df.empty:
            return self._empty_figure("데이터 없음")

        fig = go.Figure()

        cols_needed = ['lgm_tot_p50', 'sfr_tot_p50', 'oh_p50']
        if all(c in self.df.columns for c in cols_needed):
            valid = self.df[cols_needed + (['GEI'] if 'GEI' in self.df.columns else [])].dropna()
            color_vals = valid['GEI'] if 'GEI' in valid.columns else valid['lgm_tot_p50']
            cbar_title = 'GEI' if 'GEI' in valid.columns else '질량'

            fig.add_trace(go.Scatter3d(
                x=valid['lgm_tot_p50'],
                y=valid['sfr_tot_p50'],
                z=valid['oh_p50'],
                mode='markers',
                marker=dict(
                    size=2, color=color_vals, colorscale='Viridis',
                    opacity=0.3, colorbar=dict(title=cbar_title)
                ),
                name='배경 은하'
            ))

        if target_mass is not None and target_sfr is not None and target_z is not None:
            fig.add_trace(go.Scatter3d(
                x=[target_mass], y=[target_sfr], z=[target_z],
                mode='markers',
                marker=dict(color='red', size=8,
                            line=dict(color='white', width=2)),
                name='★ 대상 천체'
            ))

        fig.update_layout(
            title='3D 기본금속량관계 (Fundamental Metallicity Relation)',
            scene=dict(
                xaxis_title='log(M★/M☉)',
                yaxis_title='log(SFR)',
                zaxis_title='12+log(O/H)',
                xaxis=dict(range=[7, 13]),
                yaxis=dict(range=[-4, 3]),
                zaxis=dict(range=[7.5, 9.5])
            ),
            template='plotly_dark',
            margin=dict(l=0, r=0, b=0, t=40),
            height=550
        )
        return fig

    # ── 2×2 종합 패널 ──────────────────────────────────────
    def plot_summary_4panel(self, target_props=None) -> go.Figure:
        """2×2 종합 패널: BPT, SFMS, MZR, Color-Mass"""
        if self.df.empty:
            return self._empty_figure("데이터 없음")

        target = target_props or {}

        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                'BPT 진단 도표', '별생성 주계열 (SFMS)',
                '질량-금속량 관계 (MZR)', '색-질량 도표'
            ),
            horizontal_spacing=0.1, vertical_spacing=0.12
        )

        # 각 서브플롯의 데이터를 직접 추가 (중첩 호출 대신)
        panels = [
            (1, 1, 'log_nii_ha', 'log_oiii_hb', 'bpt_label', self.BPT_COLORS,
             target.get('log_nii_ha'), target.get('log_oiii_hb')),
            (1, 2, 'lgm_tot_p50', 'sfr_tot_p50', self._color_col, self._color_map,
             target.get('log_mass'), target.get('log_sfr')),
            (2, 1, 'lgm_tot_p50', 'oh_p50', self._color_col, self._color_map,
             target.get('log_mass'), target.get('metallicity')),
            (2, 2, 'lgm_tot_p50', 'color_u_r', self._color_col, self._color_map,
             target.get('log_mass'), target.get('color_ur')),
        ]

        for row, col, xcol, ycol, cat_col, cmap, tx, ty in panels:
            if xcol in self.df.columns and ycol in self.df.columns and cat_col in self.df.columns:
                valid = self.df[[xcol, ycol, cat_col]].dropna()
                for cat_val in valid[cat_col].unique():
                    color = cmap.get(cat_val, '#6b7280')
                    subset = valid[valid[cat_col] == cat_val]
                    if len(subset) == 0:
                        continue
                    fig.add_trace(go.Scatter(
                        x=subset[xcol], y=subset[ycol],
                        mode='markers',
                        marker=dict(color=color, size=2, opacity=0.3),
                        showlegend=False
                    ), row=row, col=col)

            # 대상 천체 오버레이
            if tx is not None and ty is not None:
                fig.add_trace(go.Scatter(
                    x=[tx], y=[ty], mode='markers',
                    marker=dict(color='red', size=14, symbol='star',
                                line=dict(color='white', width=1.5)),
                    name='★ 대상', showlegend=(row == 1 and col == 1)
                ), row=row, col=col)

        # BPT 경계선 (패널 1,1)
        x_k = np.linspace(-2.0, 0.04, 50)
        y_k = np.clip(0.61 / (x_k - 0.05) + 1.3, -2, 2)
        fig.add_trace(go.Scatter(
            x=x_k, y=y_k, mode='lines',
            line=dict(color='cyan', dash='dash', width=1),
            showlegend=False
        ), row=1, col=1)

        x_kw = np.linspace(-2.0, 0.46, 50)
        y_kw = np.clip(0.61 / (x_kw - 0.47) + 1.19, -2, 2)
        fig.add_trace(go.Scatter(
            x=x_kw, y=y_kw, mode='lines',
            line=dict(color='yellow', dash='dot', width=1),
            showlegend=False
        ), row=1, col=1)

        fig.update_layout(
            height=900, width=1100,
            title_text="다중 위상공간 분석 (Multi-panel Phase Space Analysis)",
            template='plotly_dark', showlegend=False
        )

        # 축 설정
        fig.update_xaxes(title_text='log([NII]/Hα)', range=[-2, 1], row=1, col=1)
        fig.update_yaxes(title_text='log([OIII]/Hβ)', range=[-1.5, 1.5], row=1, col=1)
        fig.update_xaxes(title_text='log(M★/M☉)', range=[7, 13], row=1, col=2)
        fig.update_yaxes(title_text='log(SFR)', range=[-4, 3], row=1, col=2)
        fig.update_xaxes(title_text='log(M★/M☉)', range=[7, 13], row=2, col=1)
        fig.update_yaxes(title_text='12+log(O/H)', range=[7.5, 9.5], row=2, col=1)
        fig.update_xaxes(title_text='log(M★/M☉)', range=[7, 13], row=2, col=2)
        fig.update_yaxes(title_text='(u-r)', range=[0, 4], row=2, col=2)

        return fig

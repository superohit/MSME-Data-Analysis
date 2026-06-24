"""
dashboard.py
------------
Interactive Plotly Dash Dashboard for MSME Exporter Financing Analysis.
Run: python dashboard.py
Open: http://127.0.0.1:8050
"""

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from dash import Dash, dcc, html, Input, Output, dash_table
import warnings
warnings.filterwarnings('ignore')

# ── Load & Prep Data ──────────────────────────────────────────────────────────
df = pd.read_csv('data/msme_loan_disbursements.csv', parse_dates=['Disbursement_Date'])

FY_ORDER      = [f'FY{y}-{str(y+1)[-2:]}' for y in range(2015, 2024)]
RISK_COLORS   = {'Low': '#2e7d32', 'Medium': '#f57f17', 'High': '#c62828'}
SECTOR_LIST   = sorted(df['Sector'].unique())
STATE_LIST    = sorted(df['State'].unique())

# Pre-compute FY summary
fy_summary = df.groupby('Fiscal_Year').agg(
    Total_Disbursements = ('Loan_ID', 'count'),
    Total_Amount_Cr     = ('Loan_Amount_INR', lambda x: x.sum() / 1e7),
    Avg_Loan_Lakhs      = ('Loan_Amount_INR', lambda x: x.mean() / 1e5),
    NPA_Count           = ('NPA_History', lambda x: (x == 'Yes').sum()),
    IES_Claimed         = ('IES_Claimed',  lambda x: (x == 'Yes').sum()),
    IES_Eligible        = ('IES_Eligible', lambda x: (x == 'Yes').sum()),
).reindex(FY_ORDER).reset_index()
fy_summary['IES_Claim_Rate'] = (fy_summary['IES_Claimed'] / fy_summary['IES_Eligible'] * 100).round(1)
fy_summary['NPA_Rate']       = (fy_summary['NPA_Count'] / fy_summary['Total_Disbursements'] * 100).round(1)
fy_summary['YoY_Growth']     = fy_summary['Total_Amount_Cr'].pct_change() * 100

# ── App Layout ────────────────────────────────────────────────────────────────
app = Dash(__name__, title="MSME Trade Finance Dashboard")

CARD_STYLE = {
    'backgroundColor': '#ffffff',
    'borderRadius': '8px',
    'padding': '20px',
    'boxShadow': '0 2px 8px rgba(0,0,0,0.08)',
    'marginBottom': '20px'
}

KPI_STYLE = {
    **CARD_STYLE,
    'textAlign': 'center',
    'padding': '18px 10px'
}

def kpi_card(title, value, subtitle='', color='#1565c0'):
    return html.Div([
        html.P(title, style={'fontSize': '12px', 'color': '#666', 'margin': '0 0 4px 0',
                             'textTransform': 'uppercase', 'letterSpacing': '0.5px'}),
        html.H3(value, style={'fontSize': '26px', 'fontWeight': '700', 'color': color,
                              'margin': '0 0 4px 0'}),
        html.P(subtitle, style={'fontSize': '11px', 'color': '#888', 'margin': 0}),
    ], style=KPI_STYLE)

app.layout = html.Div(style={'backgroundColor': '#f0f4f8', 'fontFamily': 'Segoe UI, Arial, sans-serif',
                              'minHeight': '100vh'}, children=[

    # ── Header ──
    html.Div(style={'backgroundColor': '#0d3b6e', 'padding': '16px 32px',
                    'marginBottom': '24px'}, children=[
        html.H2('📊 MSME Exporter Financing & Loan Disbursement Analysis',
                style={'color': 'white', 'margin': 0, 'fontSize': '22px'}),
        html.P('Trade Finance Dashboard | Export Promotion Mission (EPM) | DGFT',
               style={'color': '#90caf9', 'margin': '4px 0 0 0', 'fontSize': '13px'})
    ]),

    html.Div(style={'padding': '0 28px'}, children=[

        # ── KPI Row ──
        html.Div(style={'display': 'grid', 'gridTemplateColumns': 'repeat(5, 1fr)',
                        'gap': '16px', 'marginBottom': '8px'}, children=[
            kpi_card('Total Loans',        f'{len(df):,}',        'FY2015-16 to FY2023-24'),
            kpi_card('Portfolio Size',     f'₹{df["Loan_Amount_INR"].sum()/1e9:.1f}B',
                                           'Total Disbursed', '#1565c0'),
            kpi_card('Avg Loan Size',      f'₹{df["Loan_Amount_INR"].mean()/1e5:.1f}L',
                                           'Per MSME Exporter', '#00695c'),
            kpi_card('High-Risk Loans',    f'{(df["Risk_Tier"]=="High").mean()*100:.1f}%',
                                           'Flagged for Review', '#c62828'),
            kpi_card('IES Claim Rate',
                     f'{(df["IES_Claimed"]=="Yes").sum()/(df["IES_Eligible"]=="Yes").sum()*100:.1f}%',
                     'Among Eligible Loans', '#6a1b9a'),
        ]),

        # ── Filters ──
        html.Div(style={**CARD_STYLE, 'padding': '16px 20px'}, children=[
            html.P('Filters', style={'fontWeight': '600', 'marginBottom': '12px',
                                     'color': '#333', 'fontSize': '13px'}),
            html.Div(style={'display': 'grid', 'gridTemplateColumns': 'repeat(4, 1fr)', 'gap': '16px'},
                     children=[
                html.Div([
                    html.Label('Fiscal Year', style={'fontSize': '12px', 'color': '#555'}),
                    dcc.Dropdown(
                        id='filter-fy',
                        options=[{'label': 'All Years', 'value': 'ALL'}] +
                                [{'label': fy, 'value': fy} for fy in FY_ORDER],
                        value='ALL', clearable=False,
                        style={'fontSize': '13px'}
                    )
                ]),
                html.Div([
                    html.Label('Sector', style={'fontSize': '12px', 'color': '#555'}),
                    dcc.Dropdown(
                        id='filter-sector',
                        options=[{'label': 'All Sectors', 'value': 'ALL'}] +
                                [{'label': s, 'value': s} for s in SECTOR_LIST],
                        value='ALL', clearable=False,
                        style={'fontSize': '13px'}
                    )
                ]),
                html.Div([
                    html.Label('Risk Tier', style={'fontSize': '12px', 'color': '#555'}),
                    dcc.Dropdown(
                        id='filter-risk',
                        options=[{'label': 'All Tiers', 'value': 'ALL'},
                                 {'label': 'Low',    'value': 'Low'},
                                 {'label': 'Medium', 'value': 'Medium'},
                                 {'label': 'High',   'value': 'High'}],
                        value='ALL', clearable=False,
                        style={'fontSize': '13px'}
                    )
                ]),
                html.Div([
                    html.Label('Enterprise Size', style={'fontSize': '12px', 'color': '#555'}),
                    dcc.Dropdown(
                        id='filter-size',
                        options=[{'label': 'All Sizes', 'value': 'ALL'},
                                 {'label': 'Micro',  'value': 'Micro'},
                                 {'label': 'Small',  'value': 'Small'},
                                 {'label': 'Medium', 'value': 'Medium'}],
                        value='ALL', clearable=False,
                        style={'fontSize': '13px'}
                    )
                ]),
            ])
        ]),

        # ── Trend Charts ──
        html.Div(children=[
            html.Div(style=CARD_STYLE, children=[dcc.Graph(id='trend-chart', style={'height': '320px'})]),
            html.Div(style=CARD_STYLE, children=[dcc.Graph(id='yoy-chart',   style={'height': '320px'})]),
        ], style={'display': 'grid', 'gridTemplateColumns': '2fr 1fr', 'gap': '16px'}),

        # ── Risk & IES Charts ──
        html.Div(children=[
            html.Div(style=CARD_STYLE, children=[dcc.Graph(id='risk-pie',    style={'height': '300px'})]),
            html.Div(style=CARD_STYLE, children=[dcc.Graph(id='sector-risk', style={'height': '300px'})]),
            html.Div(style=CARD_STYLE, children=[dcc.Graph(id='ies-chart',   style={'height': '300px'})]),
        ], style={'display': 'grid', 'gridTemplateColumns': '1fr 1fr 1fr', 'gap': '16px'}),

        # ── State & Destination ──
        html.Div(children=[
            html.Div(style=CARD_STYLE, children=[dcc.Graph(id='state-chart', style={'height': '380px'})]),
            html.Div(style=CARD_STYLE, children=[dcc.Graph(id='dest-chart',  style={'height': '380px'})]),
        ], style={'display': 'grid', 'gridTemplateColumns': '1fr 1fr', 'gap': '16px'}),

        # ── Data Table ──
        html.Div(style=CARD_STYLE, children=[
            html.H6('📋 Flagged High-Risk Loans (Sample)',
                    style={'fontWeight': '600', 'marginBottom': '12px', 'color': '#333'}),
            html.Div(id='risk-table')
        ]),

        # Footer
        html.P('Data: Synthetic dataset inspired by RBI DBIE, DGFT Export Statistics & SIDBI MSME Pulse | '
               'Built for DGFT Export Promotion Mission — Trade Finance Analysis',
               style={'textAlign': 'center', 'color': '#aaa', 'fontSize': '11px',
                      'marginTop': '8px', 'paddingBottom': '20px'}),
    ])
])


# ── Callbacks ─────────────────────────────────────────────────────────────────

def apply_filters(fy, sector, risk, size):
    filtered = df.copy()
    if fy     != 'ALL': filtered = filtered[filtered['Fiscal_Year']    == fy]
    if sector != 'ALL': filtered = filtered[filtered['Sector']         == sector]
    if risk   != 'ALL': filtered = filtered[filtered['Risk_Tier']      == risk]
    if size   != 'ALL': filtered = filtered[filtered['Enterprise_Size'] == size]
    return filtered


@app.callback(
    Output('trend-chart', 'figure'),
    Output('yoy-chart',   'figure'),
    Output('risk-pie',    'figure'),
    Output('sector-risk', 'figure'),
    Output('ies-chart',   'figure'),
    Output('state-chart', 'figure'),
    Output('dest-chart',  'figure'),
    Output('risk-table',  'children'),
    Input('filter-fy',     'value'),
    Input('filter-sector', 'value'),
    Input('filter-risk',   'value'),
    Input('filter-size',   'value'),
)
def update_all(fy, sector, risk, size):
    fd = apply_filters(fy, sector, risk, size)

    # 1. Trend chart
    agg = fd.groupby('Fiscal_Year').agg(
        Amount = ('Loan_Amount_INR', lambda x: x.sum() / 1e7),
        Count  = ('Loan_ID', 'count')
    ).reindex(FY_ORDER).reset_index()
    fig_trend = make_subplots(specs=[[{'secondary_y': True}]])
    fig_trend.add_trace(go.Bar(x=agg['Fiscal_Year'], y=agg['Amount'], name='Amount (₹ Cr)',
                               marker_color='#1565c0', opacity=0.8), secondary_y=False)
    fig_trend.add_trace(go.Scatter(x=agg['Fiscal_Year'], y=agg['Count'], name='No. of Loans',
                                   mode='lines+markers', line=dict(color='#ff6f00', width=2.5),
                                   marker=dict(size=6)), secondary_y=True)
    fig_trend.update_layout(title_text='Disbursement Trend by Fiscal Year', title_font_size=13,
                            legend=dict(orientation='h', y=-0.2), margin=dict(t=40, b=10, l=10, r=10),
                            plot_bgcolor='white', paper_bgcolor='white')
    fig_trend.update_yaxes(title_text='Amount (₹ Crore)', secondary_y=False)
    fig_trend.update_yaxes(title_text='No. of Loans', secondary_y=True)

    # 2. YoY growth
    agg2 = fd.groupby('Fiscal_Year')['Loan_Amount_INR'].sum().div(1e7).reindex(FY_ORDER)
    yoy  = agg2.pct_change() * 100
    fig_yoy = go.Figure(go.Bar(
        x=yoy.index, y=yoy.values,
        marker_color=['#c62828' if v < 0 else '#2e7d32' for v in yoy.fillna(0)],
        opacity=0.85
    ))
    fig_yoy.add_hline(y=0, line_dash='dash', line_color='black', line_width=1)
    fig_yoy.update_layout(title_text='YoY Growth (%)', title_font_size=13,
                          margin=dict(t=40, b=10, l=10, r=10),
                          plot_bgcolor='white', paper_bgcolor='white')

    # 3. Risk pie
    rc = fd['Risk_Tier'].value_counts()
    fig_risk = go.Figure(go.Pie(
        labels=rc.index, values=rc.values,
        marker_colors=[RISK_COLORS.get(t, '#999') for t in rc.index],
        hole=0.45, textinfo='label+percent'
    ))
    fig_risk.update_layout(title_text='Risk Tier Distribution', title_font_size=13,
                           showlegend=False, margin=dict(t=40, b=10, l=10, r=10))

    # 4. Sector risk score
    sr = fd.groupby('Sector')['Risk_Score'].mean().sort_values()
    fig_sr = go.Figure(go.Bar(
        x=sr.values, y=sr.index, orientation='h',
        marker_color=['#c62828' if v >= 40 else '#f57f17' if v >= 25 else '#2e7d32' for v in sr],
        opacity=0.85
    ))
    fig_sr.update_layout(title_text='Avg Risk Score by Sector', title_font_size=13,
                         margin=dict(t=40, b=10, l=10, r=80),
                         plot_bgcolor='white', paper_bgcolor='white')

    # 5. IES claim rate by state tier
    ies_fd = fd[fd['IES_Eligible'] == 'Yes']
    ies_state = ies_fd.groupby('State').apply(
        lambda x: (x['IES_Claimed'] == 'Yes').mean() * 100
    ).sort_values()
    tiers = fd.groupby('State')['State_Tier'].first()
    fig_ies = go.Figure(go.Bar(
        x=ies_state.values, y=ies_state.index, orientation='h',
        marker_color=[{1:'#1565c0',2:'#2e7d32',3:'#c62828'}.get(tiers.get(s,2),'#999')
                      for s in ies_state.index],
        opacity=0.85
    ))
    fig_ies.add_vline(x=75, line_dash='dash', line_color='black', line_width=1)
    fig_ies.update_layout(title_text='IES Claim Rate by State (%)', title_font_size=13,
                          margin=dict(t=40, b=10, l=10, r=10),
                          plot_bgcolor='white', paper_bgcolor='white', height=300)

    # 6. State disbursement
    state_amt = fd.groupby('State')['Loan_Amount_INR'].sum().div(1e7).sort_values(ascending=True)
    fig_state = go.Figure(go.Bar(
        x=state_amt.values, y=state_amt.index, orientation='h',
        marker_color='#1565c0', opacity=0.8
    ))
    fig_state.update_layout(title_text='Total Disbursement by State (₹ Crore)', title_font_size=13,
                            margin=dict(t=40, b=10, l=10, r=10),
                            plot_bgcolor='white', paper_bgcolor='white')

    # 7. Destination risk
    dest_amt = fd.groupby(['Destination_Country','Destination_Risk'])['Loan_Amount_INR'].sum().div(1e7)
    dest_df  = dest_amt.reset_index().sort_values('Loan_Amount_INR', ascending=False)
    fig_dest = go.Figure(go.Bar(
        x=dest_df['Destination_Country'],
        y=dest_df['Loan_Amount_INR'],
        marker_color=[RISK_COLORS.get(r, '#999') for r in dest_df['Destination_Risk']],
        opacity=0.85,
        text=dest_df['Destination_Risk'],
        textposition='outside'
    ))
    fig_dest.update_layout(title_text='Exposure by Destination Country (Coloured by Risk)',
                           title_font_size=13,
                           margin=dict(t=40, b=60, l=10, r=10),
                           plot_bgcolor='white', paper_bgcolor='white',
                           xaxis_tickangle=-40)

    # 8. High-risk table
    high_risk = fd[fd['Risk_Tier'] == 'High'][[
        'Loan_ID', 'Fiscal_Year', 'State', 'Sector', 'Enterprise_Size',
        'Loan_Amount_INR', 'Risk_Score', 'NPA_History',
        'Destination_Country', 'Destination_Risk', 'IES_Eligible', 'IES_Claimed'
    ]].head(15).copy()
    high_risk['Loan_Amount_INR'] = high_risk['Loan_Amount_INR'].apply(lambda x: f'₹{x/1e5:.1f}L')

    table = dash_table.DataTable(
        data=high_risk.rename(columns={'Loan_Amount_INR': 'Loan Amt'}).to_dict('records'),
        columns=[{'name': c, 'id': c} for c in high_risk.rename(
            columns={'Loan_Amount_INR': 'Loan Amt'}).columns],
        style_table={'overflowX': 'auto'},
        style_header={'backgroundColor': '#0d3b6e', 'color': 'white',
                      'fontWeight': '600', 'fontSize': '12px'},
        style_cell={'fontSize': '12px', 'padding': '8px 12px',
                    'textAlign': 'left', 'border': '1px solid #eee'},
        style_data_conditional=[
            {'if': {'filter_query': '{NPA_History} = "Yes"'},
             'backgroundColor': '#fff3e0', 'color': '#e65100'},
            {'if': {'filter_query': '{Destination_Risk} = "High"'},
             'backgroundColor': '#fce4ec', 'color': '#880e4f'},
        ],
        page_size=10
    )

    return fig_trend, fig_yoy, fig_risk, fig_sr, fig_ies, fig_state, fig_dest, table


if __name__ == '__main__':
    print('🚀 Starting MSME Trade Finance Dashboard...')
    print('   Open browser at: http://127.0.0.1:8050')
    app.run(debug=True, port=8050)

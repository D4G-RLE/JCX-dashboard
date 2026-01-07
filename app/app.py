import dash
from dash import dcc, html, Input, Output, State, callback_context
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

# Données des projets
from app.data_loader import load_projects_data
# Charger les vraies données (pour github changer en real=False)
projects_data = load_projects_data(real=True)

CO2_GAS = 0.18316

CO2_ELEC_BE = {
    2024: 0.104820908, 2025: 0.10623495, 2026: 0.107648992, 2027: 0.109063034,
    2028: 0.110477076, 2029: 0.111891118, 2030: 0.11330516, 2031: 0.112363514,
    2032: 0.111421868, 2033: 0.110480221, 2034: 0.109538575, 2035: 0.108596928,
    2036: 0.10677822, 2037: 0.104959512, 2038: 0.103140804, 2039: 0.101322096,
    2040: 0.099503388, 2041: 0.099135306, 2042: 0.098767224, 2043: 0.098399142,
    2044: 0.09803106, 2045: 0.097662978, 2046: 0.097148195, 2047: 0.096633411,
    2048: 0.096118628, 2049: 0.095603845, 2050: 0.095089061
}

PARIS_TARGET = {
    2024: 34.39737161, 2025: 31.47916175, 2026: 28.46332818, 2027: 25.70657477,
    2028: 23.09118141, 2029: 20.61644164, 2030: 18.19982845, 2031: 16.15410307,
    2032: 14.1493106, 2033: 12.26297963, 2034: 10.49043135, 2035: 8.832651339,
    2036: 7.264334733, 2037: 5.812548239, 2038: 4.573668339, 2039: 3.578097418,
    2040: 2.777574811, 2041: 2.334398458, 2042: 1.999520601, 2043: 1.7050406,
    2044: 1.448436241, 2045: 1.207772654, 2046: 1.034903163, 2047: 0.868545078,
    2048: 0.721077114, 2049: 0.585189692, 2050: 0.455132508
}

def calculate_consumption(project, year, ref_level, timeline):
    data = projects_data[project]
    gas, elec = data['gasInit'], data['elecInit']
    
    project_actions = [a for a in timeline if a['project'] == project and a['year'] <= year]
    max_ref = max([a['ref'] for a in project_actions], default=0)
    effective_ref = min(ref_level, max_ref)
    
    if effective_ref >= 1:
        elec *= (1 - data['redElecRef1'])
        gas *= (1 - data['redGasRef1'])
    if effective_ref >= 2:
        elec *= (1 - data['redElecRef2'])
        gas *= (1 - data['redGasRef2'])
    if effective_ref >= 3:
        elec *= (1 - data['redElecRef3'])
        gas *= (1 - data['redGasRef3'])
    
    return gas, elec

def calculate_co2(project, year, ref_level, timeline):
    gas, elec = calculate_consumption(project, year, ref_level, timeline)
    co2_factor = CO2_ELEC_BE.get(year, CO2_ELEC_BE[2050])
    co2 = (gas * CO2_GAS + elec * co2_factor) / projects_data[project]['surface']
    return co2

# Initialisation de l'application Dash
app = dash.Dash(__name__)

app.layout = html.Div([
    # Header
    html.H1("Projet de Rénovation Énergétique JCX", 
            style={
                'textAlign': 'center', 
                'color': '#1f2937', 
                'marginBottom': '40px',
                'fontSize': '36px',
                'fontWeight': 'bold'
            }),
    
    # Section graphique avec checkboxes
    html.Div([
        html.H2("Évolution CO2e/m² et CAPEX annuel", 
                style={
                    'fontSize': '24px', 
                    'fontWeight': '600', 
                    'marginBottom': '20px',
                    'color': '#374151'
                }),
        
        # Checkboxes pour les projets
        html.Div([
            dcc.Checklist(
                id='project-visibility',
                options=[{'label': f'  {p}', 'value': p} for p in projects_data.keys()],
                value=list(projects_data.keys()),
                inline=True,
                style={'fontSize': '15px', 'color': '#4b5563'}
            ),
        ], style={'marginBottom': '20px'}),
        
        # Graphique
        dcc.Graph(id='main-graph', style={'height': '600px'}),
        
    ], style={
        'backgroundColor': 'white', 
        'padding': '30px', 
        'borderRadius': '12px', 
        'marginBottom': '30px',
        'boxShadow': '0 1px 3px rgba(0,0,0,0.1)'
    }),
    
    # Stats boxes (côte à côte avec flex)
    html.Div([
        # CO2 économisé
        html.Div([
            html.H3("CO2 ÉCONOMISÉ (2024-2050)", 
                    style={
                        'fontSize': '14px', 
                        'marginBottom': '12px',
                        'fontWeight': '600',
                        'letterSpacing': '0.5px',
                        'opacity': '0.95'
                    }),
            html.H2(id='co2-saved', 
                    style={
                        'fontSize': '56px', 
                        'fontWeight': 'bold', 
                        'marginBottom': '8px',
                        'lineHeight': '1'
                    }),
            html.P("tonnes CO2e", 
                   style={
                       'fontSize': '20px', 
                       'marginBottom': '20px',
                       'fontWeight': '500'
                   }),
            html.Hr(style={
                'borderColor': 'rgba(255,255,255,0.3)',
                'margin': '20px 0'
            }),
            html.Div(id='co2-equivalents', 
                     style={
                         'fontSize': '14px',
                         'lineHeight': '1.8'
                     })
        ], style={
            'flex': '1',
            'backgroundColor': '#10b981',
            'color': 'white', 
            'padding': '35px', 
            'borderRadius': '12px',
            'boxShadow': '0 4px 6px rgba(0,0,0,0.1)'
        }),
        
        # Investissement total
        html.Div([
            html.H3("INVESTISSEMENT TOTAL", 
                    style={
                        'fontSize': '14px', 
                        'marginBottom': '12px',
                        'fontWeight': '600',
                        'letterSpacing': '0.5px',
                        'opacity': '0.95'
                    }),
            html.H2(id='investment-total', 
                    style={
                        'fontSize': '56px', 
                        'fontWeight': 'bold', 
                        'marginBottom': '8px',
                        'lineHeight': '1'
                    }),
            html.P(id='investment-detail', 
                   style={
                       'fontSize': '20px',
                       'fontWeight': '500'
                   })
        ], style={
            'flex': '1',
            'backgroundColor': '#3b82f6',
            'color': 'white', 
            'padding': '35px', 
            'borderRadius': '12px',
            'boxShadow': '0 4px 6px rgba(0,0,0,0.1)'
        }),
        
    ], style={
        'display': 'flex',
        'gap': '25px',
        'marginBottom': '30px'
    }),
    
    # Section planification des mesures
    html.Div([
        html.H2("Planifier une mesure", 
                style={
                    'fontSize': '24px', 
                    'fontWeight': '600', 
                    'marginBottom': '25px',
                    'color': '#374151'
                }),
        
        # Contrôles pour ajouter une mesure
        html.Div([
            html.Div([
                html.Label("Année d'exécution:", 
                          style={
                              'fontWeight': '600', 
                              'marginBottom': '8px',
                              'display': 'block',
                              'color': '#374151'
                          }),
                dcc.Input(
                    id='year-input', 
                    type='number', 
                    value=2025, 
                    min=2025, 
                    max=2050,
                    style={
                        'width': '100%', 
                        'padding': '10px', 
                        'fontSize': '16px',
                        'border': '2px solid #e5e7eb',
                        'borderRadius': '8px'
                    }
                ),
            ], style={'flex': '1'}),
            
            html.Div([
                html.Label("Projet:", 
                          style={
                              'fontWeight': '600', 
                              'marginBottom': '8px',
                              'display': 'block',
                              'color': '#374151'
                          }),
                dcc.Dropdown(
                    id='project-dropdown',
                    options=[{'label': p, 'value': p} for p in projects_data.keys()],
                    value=list(projects_data.keys())[0],
                    style={'fontSize': '16px'}
                ),
            ], style={'flex': '1'}),
            
            html.Div([
                html.Label("Mesure:", 
                          style={
                              'fontWeight': '600', 
                              'marginBottom': '8px',
                              'display': 'block',
                              'color': '#374151'
                          }),
                dcc.Dropdown(
                    id='measure-dropdown',
                    options=[
                        {'label': 'Groupe de mesures 1 : Quick wins', 'value': 1},
                        {'label': 'Groupe de mesures 2 : Isolation', 'value': 2},
                        {'label': 'Groupe de mesures 3 : Ventilation + PAC', 'value': 3}
                    ],
                    value=1,
                    style={'fontSize': '16px'}
                ),
            ], style={'flex': '1'}),
        ], style={
            'display': 'flex',
            'gap': '20px',
            'marginBottom': '25px'
        }),
        
        # Boutons
        html.Div([
            html.Button('Ajouter la mesure', 
                       id='add-button', 
                       n_clicks=0,
                       style={
                           'backgroundColor': '#3b82f6', 
                           'color': 'white', 
                           'padding': '12px 24px',
                           'fontSize': '16px', 
                           'border': 'none', 
                           'borderRadius': '8px', 
                           'cursor': 'pointer',
                           'fontWeight': '600',
                           'marginRight': '12px',
                           'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'
                       }),
            html.Button('Réinitialiser', 
                       id='reset-button', 
                       n_clicks=0,
                       style={
                           'backgroundColor': '#ef4444', 
                           'color': 'white', 
                           'padding': '12px 24px',
                           'fontSize': '16px', 
                           'border': 'none', 
                           'borderRadius': '8px', 
                           'cursor': 'pointer',
                           'fontWeight': '600',
                           'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'
                       }),
        ]),
        
    ], style={
        'backgroundColor': 'white', 
        'padding': '30px', 
        'borderRadius': '12px', 
        'marginBottom': '30px',
        'boxShadow': '0 1px 3px rgba(0,0,0,0.1)'
    }),
    
    # Planning des mesures
    html.Div([
        html.H2("Planning des mesures", 
                style={
                    'fontSize': '24px', 
                    'fontWeight': '600', 
                    'marginBottom': '20px',
                    'color': '#374151'
                }),
        html.Div(id='timeline-display')
    ], style={
        'backgroundColor': 'white', 
        'padding': '30px', 
        'borderRadius': '12px',
        'boxShadow': '0 1px 3px rgba(0,0,0,0.1)'
    }),
    
    # Store pour le timeline
    dcc.Store(id='timeline-store', data=[]),
    dcc.Store(id='alert-trigger', data=0)
    
], style={
    'maxWidth': '1400px', 
    'margin': '0 auto', 
    'padding': '40px 20px', 
    'backgroundColor': '#f3f4f6',
    'minHeight': '100vh'
})

@app.callback(
    [Output('timeline-store', 'data'),
     Output('alert-trigger', 'data')],
    [Input('add-button', 'n_clicks'),
     Input('reset-button', 'n_clicks')],
    [State('year-input', 'value'),
     State('project-dropdown', 'value'),
     State('measure-dropdown', 'value'),
     State('timeline-store', 'data'),
     State('alert-trigger', 'data')]
)
def update_timeline(add_clicks, reset_clicks, year, project, measure, timeline, alert_trigger):
    ctx = callback_context
    if not ctx.triggered:
        return timeline, alert_trigger
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if button_id == 'reset-button':
        return [], alert_trigger
    
    if button_id == 'add-button' and add_clicks > 0:
        project_actions = [a for a in timeline if a['project'] == project]
        max_ref_done = max([a['ref'] for a in project_actions], default=0)
        
        if measure > max_ref_done + 1:
            return timeline, alert_trigger + 1
        
        if any(a['ref'] == measure for a in project_actions):
            return timeline, alert_trigger + 1
        
        timeline.append({'project': project, 'ref': measure, 'year': year})
    
    return timeline, alert_trigger

@app.callback(
    [Output('main-graph', 'figure'),
     Output('co2-saved', 'children'),
     Output('co2-equivalents', 'children'),
     Output('investment-total', 'children'),
     Output('investment-detail', 'children'),
     Output('timeline-display', 'children')],
    [Input('timeline-store', 'data'),
     Input('project-visibility', 'value')]
)
def update_graph(timeline, visible_projects):
    years = list(range(2024, 2051))
    
    # Calculer les données
    data = {year: {} for year in years}
    for year in years:
        project_states = {p: 0 for p in projects_data.keys()}
        for action in timeline:
            if action['year'] <= year:
                project_states[action['project']] = max(project_states[action['project']], action['ref'])
        
        total_co2 = 0
        total_surface = 0
        for project in projects_data.keys():
            co2 = calculate_co2(project, year, project_states[project], timeline)
            data[year][project] = co2
            total_co2 += co2 * projects_data[project]['surface']
            total_surface += projects_data[project]['surface']
        
        data[year]['Moyenne'] = total_co2 / total_surface
        data[year]['Paris'] = PARIS_TARGET.get(year, None)
        
        year_actions = [a for a in timeline if a['year'] == year]
        data[year]['CAPEX'] = sum(projects_data[a['project']][f"costRef{a['ref']}"] for a in year_actions)
    
    # Créer le graphique
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Barres CAPEX
    fig.add_trace(
        go.Bar(x=years, y=[data[y]['CAPEX'] for y in years], name='CAPEX annuel (€)',
               marker_color='rgba(239, 68, 68, 0.6)', yaxis='y2'),
        secondary_y=True
    )
    
    # Ligne moyenne
    fig.add_trace(
        go.Scatter(x=years, y=[data[y]['Moyenne'] for y in years], name='Moyenne CO2',
                   line=dict(color='black', width=3), mode='lines'),
        secondary_y=False
    )
    
    # Ligne objectif Paris
    fig.add_trace(
        go.Scatter(x=years, y=[data[y]['Paris'] for y in years], name='Objectif Paris 1.5°C',
                   line=dict(color='red', width=2, dash='dash'), mode='lines'),
        secondary_y=False
    )
    
    # Lignes des projets
    colors = ['#8884d8', '#82ca9d', '#ffc658', '#ff8042', '#a4de6c']
    for i, project in enumerate(projects_data.keys()):
        if project in visible_projects:
            fig.add_trace(
                go.Scatter(x=years, y=[data[y][project] for y in years], name=project,
                           line=dict(color=colors[i], width=2), mode='lines'),
                secondary_y=False
            )
    
    fig.update_xaxes(title_text="Année", title_font=dict(size=14))
    fig.update_yaxes(title_text="kg CO2e/m²", secondary_y=False, title_font=dict(size=14))
    fig.update_yaxes(title_text="CAPEX (€)", secondary_y=True, title_font=dict(size=14))
    fig.update_layout(
        height=600, 
        hovermode='x unified', 
        template='plotly_white',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    # Calculs stats
    total_investment = sum(projects_data[a['project']][f"costRef{a['ref']}"] for a in timeline)
    initial_co2 = data[2024]['Moyenne']
    final_co2 = data[2050]['Moyenne']
    total_surface = sum(p['surface'] for p in projects_data.values())
    co2_saved = (initial_co2 - final_co2) * total_surface * 26 / 1000
    
    # Format investissement
    if total_investment >= 1000000:
        inv_display = f"{total_investment/1000000:.1f}M"
    else:
        inv_display = f"{total_investment/1000:.0f}k"
    
    inv_detail = f"€ ({total_investment:,.0f} €)".replace(',', ' ')
    
    # Équivalents CO2
    equivalents = html.Div([
        html.Div(f"📱 {int(co2_saved * 1000 / 200):,} ordinateurs portables".replace(',', ' '), 
                 style={'marginBottom': '8px'}),
        html.Div(f"✈️ {int(co2_saved * 1000 / 1100):,} vols Paris-NYC (AR)".replace(',', ' '), 
                 style={'marginBottom': '8px'}),
        html.Div(f"👤 {int(co2_saved * 1000 / 13400):,} Belges pendant 1 an".replace(',', ' '))
    ])
    
    # Timeline display
    sorted_timeline = sorted(timeline, key=lambda x: x['year'])
    ref_names = {1: 'Quick wins', 2: 'Isolation', 3: 'Ventilation + PAC'}
    timeline_items = []
    for item in sorted_timeline:
        cost = projects_data[item['project']][f"costRef{item['ref']}"]
        timeline_items.append(
            html.Div([
                html.Span(f"{item['year']}", 
                         style={
                             'fontWeight': 'bold', 
                             'color': '#3b82f6', 
                             'marginRight': '20px',
                             'fontSize': '16px',
                             'minWidth': '60px',
                             'display': 'inline-block'
                         }),
                html.Span(f"{item['project']} - {ref_names[item['ref']]}", 
                         style={
                             'marginRight': '20px',
                             'flex': '1',
                             'color': '#374151'
                         }),
                html.Span(f"{cost:,.0f} €".replace(',', ' '), 
                         style={
                             'color': '#10b981', 
                             'fontWeight': 'bold',
                             'fontSize': '16px'
                         })
            ], style={
                'padding': '15px 20px', 
                'backgroundColor': '#f9fafb', 
                'marginBottom': '10px',
                'borderRadius': '8px', 
                'border': '1px solid #e5e7eb',
                'display': 'flex',
                'alignItems': 'center',
                'transition': 'all 0.2s'
            })
        )
    
    timeline_display = timeline_items if timeline_items else html.P(
        "Aucune mesure planifiée", 
        style={
            'fontStyle': 'italic', 
            'color': '#9ca3af',
            'textAlign': 'center',
            'padding': '20px'
        }
    )
    
    return fig, f"{co2_saved:.1f}", equivalents, inv_display, inv_detail, timeline_display

if __name__ == '__main__':
    app.run(debug=True, port=8050)
import pandas as pd
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output, callback
import dash

# Load data once (looks for files next to this script or in common places)
import pathlib
SCRIPT_DIR = pathlib.Path(__file__).parent.resolve()

def find_file(name):
    candidates = [
        SCRIPT_DIR / name,
        SCRIPT_DIR / "data" / name,
    ]
    for p in candidates:
        if p.exists():
            return p
    raise FileNotFoundError(f"Could not find {name}. Place it next to this script.")

print("Loading GC data...")
gc_path = find_file("gc_data.csv")
print(f"  Using GC file: {gc_path}")
gc = pd.read_csv(gc_path, parse_dates=['Date'])
gc = gc.dropna(subset=['Date', 'Compound'])
gc = gc[gc['Compound'].isin(['111-TCA', 'PCE', 'TCE'])].copy()
gc['DateOnly'] = gc['Date'].dt.normalize()
gc['Exceeded'] = gc['Exceeded?'] == 'Yes'

# Full-resolution data (every sample)
locations = sorted(gc['Location Details'].unique())
compounds = ['TCE', 'PCE', '111-TCA']

weather_path = find_file("beverly_weather.csv")
print(f"  Using weather file: {weather_path}")
weather = pd.read_csv(weather_path, parse_dates=['time'])
weather = weather.set_index('time').sort_index()
weather_options = [
    {'label': 'Avg Temperature (°C)', 'value': 'tavg'},
    {'label': 'Min Temperature (°C)', 'value': 'tmin'},
    {'label': 'Max Temperature (°C)', 'value': 'tmax'},
    {'label': 'Precipitation (mm)', 'value': 'prcp'},
    {'label': 'Wind Speed (km/h)', 'value': 'wspd'},
    {'label': 'Wind Direction (°)', 'value': 'wdir'},
    {'label': 'Pressure (hPa)', 'value': 'pres'},
]

app = Dash(__name__)
app.title = "Varian GC Data & Weather Conditions"

# Custom CSS to make rangeslider handles more obvious (red arrows-style)
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            /* Make rangeslider handles bigger and red */
            .rangeslider-handle {
                fill: #e74c3c !important;
                stroke: #c0392b !important;
                stroke-width: 2px !important;
            }
            .rangeslider-mask-min, .rangeslider-mask-max {
                fill: rgba(231, 76, 60, 0.15) !important;
            }
            .rangeslider-slidebox {
                fill: rgba(231, 76, 60, 0.08) !important;
            }
            /* Larger hit area */
            .rangeslider-handle:hover {
                fill: #c0392b !important;
                cursor: ew-resize;
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

app.layout = html.Div([
    html.H2("Varian GC Data & Weather Conditions",
            style={'textAlign': 'center', 'marginBottom': '5px'}),
    html.P("Select one or more locations (checkboxes). Shows every sample (not daily max). Compound and weather update independently. Red X = Action Level Exceedance.",
           style={'textAlign': 'center', 'color': '#555', 'marginTop': '0'}),
    html.P("◄ Drag the red handles on the bottom timeline to zoom ◄",
           style={'textAlign': 'center', 'color': '#e74c3c', 'fontWeight': 'bold', 'margin': '4px 0 10px 0', 'fontSize': '14px'}),

    html.Div([
        html.Div([
            html.Label("Locations (multi-select)", style={'fontWeight': 'bold'}),
            dcc.Checklist(
                id='location-checklist',
                options=[{'label': loc, 'value': loc} for loc in locations],
                value=[locations[0]],  # default first location
                inline=False,
                style={'maxHeight': '220px', 'overflowY': 'auto', 'border': '1px solid #ddd',
                       'padding': '8px', 'borderRadius': '4px', 'background': '#fafafa'}
            ),
        ], style={'width': '28%', 'display': 'inline-block', 'verticalAlign': 'top', 'padding': '10px'}),

        html.Div([
            html.Label("Compound", style={'fontWeight': 'bold'}),
            dcc.Dropdown(
                id='compound-dropdown',
                options=[{'label': c, 'value': c} for c in compounds],
                value='TCE',
                clearable=False,
                style={'marginTop': '5px'}
            ),
            html.Br(),
            html.Label("Weather Metric", style={'fontWeight': 'bold'}),
            dcc.Dropdown(
                id='weather-dropdown',
                options=weather_options,
                value='tavg',
                clearable=False,
                style={'marginTop': '5px'}
            ),
        ], style={'width': '28%', 'display': 'inline-block', 'verticalAlign': 'top', 'padding': '10px'}),

        html.Div([
            html.Label("Quick Tips", style={'fontWeight': 'bold'}),
            html.Ul([
                html.Li("Check/uncheck locations to overlay multiple sites."),
                html.Li("Compound and weather change independently."),
                html.Li("Drag the red handles on the bottom timeline to zoom."),
                html.Li("Red X markers = action level exceedances (also on rangeslider)."),
            ], style={'fontSize': '13px', 'color': '#444'})
        ], style={'width': '38%', 'display': 'inline-block', 'verticalAlign': 'top', 'padding': '10px'}),
    ], style={'background': '#f8f9fa', 'borderRadius': '8px', 'margin': '10px 20px'}),

    dcc.Graph(id='timeline-graph', style={'height': '720px'})
], style={'fontFamily': 'Arial, sans-serif', 'margin': '0 auto', 'maxWidth': '1400px'})


@callback(
    Output('timeline-graph', 'figure'),
    Input('location-checklist', 'value'),
    Input('compound-dropdown', 'value'),
    Input('weather-dropdown', 'value')
)
def update_figure(selected_locations, selected_compound, weather_col):
    if not selected_locations:
        selected_locations = [locations[0]]

    fig = go.Figure()

    # GC traces for selected locations + compound (every sample)
    for loc in selected_locations:
        mask = (gc['Location Details'] == loc) & (gc['Compound'] == selected_compound)
        d = gc[mask].sort_values('Date')
        if len(d) == 0:
            continue

        fig.add_trace(go.Scatter(
            x=d['Date'],
            y=d['Final Concentration (ug/m3)'],
            mode='lines+markers',
            name=f'{loc} - {selected_compound}',
            line=dict(width=1.2),
            marker=dict(size=3),
            hovertemplate='%{x|%Y-%m-%d %H:%M}<br>%{y:.2f} µg/m³<extra>' + loc + '</extra>'
        ))

        # Exceedances
        exceed = d[d['Exceeded']]
        if len(exceed) > 0:
            fig.add_trace(go.Scatter(
                x=exceed['Date'],
                y=exceed['Final Concentration (ug/m3)'],
                mode='markers',
                name=f'Exceedance ({loc})',
                marker=dict(size=10, color='red', symbol='x', line=dict(width=1.5, color='darkred')),
                hovertemplate='EXCEEDED<br>%{x|%Y-%m-%d %H:%M}<br>%{y:.2f} µg/m³<extra>' + loc + '</extra>',
                showlegend=True
            ))

    # Weather on secondary axis
    if weather_col in weather.columns:
        y = weather[weather_col].ffill()
        weather_label = next((o['label'] for o in weather_options if o['value'] == weather_col), weather_col)
        fig.add_trace(go.Scatter(
            x=weather.index,
            y=y,
            mode='lines',
            name=weather_label,
            line=dict(width=1.4, dash='dot', color='orange'),
            opacity=0.75,
            yaxis='y2',
            hovertemplate='%{x|%Y-%m-%d}<br>' + weather_label + ': %{y:.1f}<extra></extra>'
        ))

    fig.update_layout(
        title=f'{selected_compound} across {len(selected_locations)} location(s) + Beverly Weather',
        height=700,
        hovermode='x unified',
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        template='plotly_white',
        margin=dict(t=60, b=40),
        yaxis=dict(title='Concentration (µg/m³)'),
        yaxis2=dict(title='Weather', overlaying='y', side='right', showgrid=False),
        xaxis=dict(
            title='Date',
            type='date',
            rangeslider=dict(visible=True, thickness=0.12, bgcolor='#fff5f5'),
            rangeselector=dict(buttons=[
                dict(count=7, label='1w', step='day', stepmode='backward'),
                dict(count=1, label='1m', step='month', stepmode='backward'),
                dict(count=3, label='3m', step='month', stepmode='backward'),
                dict(step='all', label='All')
            ])
        )
    )
    return fig


if __name__ == '__main__':
    print("Starting GC Timeline app...")
    print("Open http://127.0.0.1:8050 in your browser")
    app.run(debug=False, host='0.0.0.0', port=8050)

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output, callback

data = {
    'Year': [1930, 1934, 1938, 1950, 1954, 1958, 1962, 1966, 1970, 1974, 1978, 1982, 
             1986, 1990, 1994, 1998, 2002, 2006, 2010, 2014, 2018, 2022],
    'Host': ['Uruguay', 'Italy', 'France', 'Brazil', 'Switzerland', 'Sweden', 'Chile', 
             'England', 'Mexico', 'Germany', 'Argentina', 'Spain', 'Mexico', 'Italy', 
             'United States', 'France', 'South Korea/Japan', 'Germany', 'South Africa', 
             'Brazil', 'Russia', 'Qatar'],
    'Winner': ['Uruguay', 'Italy', 'Italy', 'Uruguay', 'Germany', 'Brazil', 'Brazil', 
               'England', 'Brazil', 'Germany', 'Argentina', 'Italy', 'Argentina', 
               'Germany', 'Brazil', 'France', 'Brazil', 'Italy', 'Spain', 'Germany', 
               'France', 'Argentina'],
    'Runner_Up': ['Argentina', 'Czechoslovakia', 'Hungary', 'Brazil', 'Hungary', 'Sweden', 
                  'Czechoslovakia', 'Germany', 'Italy', 'Netherlands', 'Netherlands', 
                  'Germany', 'Germany', 'Argentina', 'Italy', 'Brazil', 'Germany', 
                  'France', 'Netherlands', 'Argentina', 'Croatia', 'France']
}

# Create DataFrame
df = pd.DataFrame(data)
#print(df['Year'])

winners_count = df['Winner'].value_counts().reset_index()
winners_count.columns = ['Country', 'Wins']

#print(winners_count)

runnerup_count = df['Runner_Up'].value_counts().reset_index()
runnerup_count.columns = ['Country', 'Runner_Ups']

# Create a merged dataframe with both winning and runner-up info
country_stats = pd.merge(winners_count, runnerup_count, on='Country', how='outer').fillna(0)
country_stats['Total_Finals'] = country_stats['Wins'] + country_stats['Runner_Ups']
#print(country_stats)


country_codes = {
    'Uruguay': 'URY', 'Italy': 'ITA', 'Germany': 'DEU', 'Brazil': 'BRA',
    'England': 'GBR', 'Argentina': 'ARG', 'France': 'FRA', 'Spain': 'ESP',
    'Czechoslovakia': 'CZE', 'Hungary': 'HUN', 'Sweden': 'SWE', 
    'Netherlands': 'NLD', 'Croatia': 'HRV'
}

# Add ISO codes to datasets
country_stats['ISO'] = country_stats['Country'].map(country_codes)
df['Winner_ISO'] = df['Winner'].map(country_codes)
df['Runner_Up_ISO'] = df['Runner_Up'].map(country_codes)

#print(df)


app = Dash(__name__)
server = app.server  # Required for deployment

# App layout
app.layout = html.Div([
    html.H1("FIFA World Cup Winners Dashboard", style={"textAlign": "center", "marginTop": "20px", "marginBottom": "20px"}),
    
    dcc.Tabs([
        # Tab 1: World Cup Winners Map
        dcc.Tab(label="World Cup Winners", children=[
            html.Div([
                html.H3("Countries by World Cup Wins", style={"textAlign": "center", "marginTop": "15px"}),
                dcc.Graph(id="winners-map"),
                
                # Country selection and details section
                html.Div([
                    html.Div([
                        html.H4("Select a Country to View Details :", style={"marginTop": "15px"}),
                        dcc.Dropdown(
                            id="country-dropdown",
                            options=[{"label": country, "value": country} for country in sorted(country_stats['Country'].unique())],
                            value=None,
                            placeholder="Select a country..."
                        ),
                        html.H6("*all other countries not listed have zero (0) World Cup Final appearances and wins")
                    ], style={"width": "100%", "marginBottom": "20px"}),
                    
                    # Country details cards
                    html.Div(id="country-details", style={"textAlign": "center", "marginTop": "15px"}),
                    
                    # Tournament history for selected country
                    html.Div(id="country-tournaments", style={"marginTop": "20px"})
                ], style={"width": "80%", "margin": "0 auto", "padding": "20px"})
            ])
        ]),
        
        # Tab 2: World Cup by Year
        dcc.Tab(label="World Cup by Year", children=[
            html.Div([
                html.H3("World Cup Results by Year", style={"textAlign": "center", "marginTop": "15px"}),
                dcc.Dropdown(
                    id="year-dropdown",
                    options=[{"label": year, "value": year} for year in sorted(df['Year'].unique())],
                    value=2022,
                    style={"width": "50%", "margin": "0 auto"}
                ),
                html.Div(id="year-details", style={"textAlign": "center", "marginTop": "15px"}),
                dcc.Graph(id="year-map")
            ])
        ])
    ], style={"width": "90%", "margin": "0 auto"})
], style={"width": "100%", "maxWidth": "1200px", "margin": "0 auto"})

# Callback for the winners map
@app.callback(
    Output("winners-map", "figure"),
    Input("country-dropdown", "value")
)
def update_winners_map(selected_country):
    # Create a choropleth map of all World Cup winners
    fig = px.choropleth(
        country_stats,
        locations="ISO",
        color="Wins",
        hover_name="Country",
        color_continuous_scale=px.colors.sequential.Blues,
        range_color=[0, country_stats['Wins'].max()],
        title="Number of FIFA World Cup Victories by Country"
    )
    
    # Highlight selected country if any
    if selected_country:
        selected_iso = country_codes.get(selected_country)
        if selected_iso:
            fig.add_scattergeo(
                locations=[selected_iso],
                locationmode="ISO-3",
                text=[selected_country],
                mode="markers",
                marker=dict(size=15, color="red", line=dict(width=2, color="black")),
                name=selected_country
            )
    
    fig.update_layout(
        geo=dict(
            showframe=False,
            showcoastlines=True,
            projection_type='natural earth'
        ),
        height=600,
        margin=dict(l=0, r=0, t=30, b=0)
    )
    
    return fig

# Callback for country details
@app.callback(
    [Output("country-details", "children"),
     Output("country-tournaments", "children")],
    Input("country-dropdown", "value")
)
def update_country_details(selected_country):
    if not selected_country:
        return "Select a country to see World Cup details", None
    
    country_data = country_stats[country_stats['Country'] == selected_country].iloc[0]
    wins = int(country_data['Wins'])
    runner_ups = int(country_data['Runner_Ups'])
    
    # Get years when the country won
    winning_years = df[df['Winner'] == selected_country]['Year'].tolist()
    runner_up_years = df[df['Runner_Up'] == selected_country]['Year'].tolist()
    
    # Create the stats cards
    stats_cards = html.Div([
        html.H4(f"{selected_country} World Cup History", style={"marginBottom": "20px"}),
        
        # Stats cards in a row
        html.Div([
            # Wins Card
            html.Div([
                html.H1(f"{wins}", style={"fontSize": "48px", "color": "#FFD700", "marginBottom": "10px"}),
                html.H5("World Cup Wins", style={"color": "#555"})
            ], style={"backgroundColor": "#f8f9fa", "padding": "20px", "borderRadius": "10px", "textAlign": "center", "width": "30%", "display": "inline-block", "margin": "0 1.5%"}),
            
            # Runner-up Card
            html.Div([
                html.H1(f"{runner_ups}", style={"fontSize": "48px", "color": "#C0C0C0", "marginBottom": "10px"}),
                html.H5("Runner-up Finishes", style={"color": "#555"})
            ], style={"backgroundColor": "#f8f9fa", "padding": "20px", "borderRadius": "10px", "textAlign": "center", "width": "30%", "display": "inline-block", "margin": "0 1.5%"}),
            
            # Total Finals Card
            html.Div([
                html.H1(f"{wins + runner_ups}", style={"fontSize": "48px", "color": "#0275d8", "marginBottom": "10px"}),
                html.H5("Total Finals", style={"color": "#555"})
            ], style={"backgroundColor": "#f8f9fa", "padding": "20px", "borderRadius": "10px", "textAlign": "center", "width": "30%", "display": "inline-block", "margin": "0 1.5%"})
        ], style={"display": "flex", "justifyContent": "space-between", "marginBottom": "20px"})
    ])
    
    # Create detailed tournament history
    tournament_details = None
    if winning_years or runner_up_years:
        # Combine and sort all years the country participated in finals
        all_years = sorted(list(set(winning_years + runner_up_years)))
        
        # Create a table of all tournament appearances
        rows = []
        for year in all_years:
            result = "Winner" if year in winning_years else "Runner-up"
            opponent = ""
            if year in winning_years:
                match_data = df[df['Year'] == year].iloc[0]
                opponent = match_data['Runner_Up']
            else:
                match_data = df[df['Year'] == year].iloc[0]
                opponent = match_data['Winner']
            
            host = df[df['Year'] == year].iloc[0]['Host']
            
            rows.append(html.Tr([
                html.Td(year, style={"padding": "8px", "borderBottom": "1px solid #ddd"}),
                html.Td(host, style={"padding": "8px", "borderBottom": "1px solid #ddd"}),
                html.Td(result, style={"padding": "8px", "borderBottom": "1px solid #ddd", 
                                      "color": "#FFD700" if result.startswith("Winner") else "#C0C0C0",
                                      "fontWeight": "bold"}),
                html.Td(f"vs {opponent}", style={"padding": "8px", "borderBottom": "1px solid #ddd"})
            ]))
        
        tournament_details = html.Div([
            html.H4(f"{selected_country}'s World Cup Final Appearances", 
                   style={"marginTop": "30px", "marginBottom": "15px"}),
            html.Table(
                # Header row
                [html.Thead(html.Tr([
                    html.Th("Year", style={"textAlign": "left", "padding": "8px", "borderBottom": "2px solid #ddd"}),
                    html.Th("Host", style={"textAlign": "left", "padding": "8px", "borderBottom": "2px solid #ddd"}),
                    html.Th("Result", style={"textAlign": "left", "padding": "8px", "borderBottom": "2px solid #ddd"}),
                    html.Th("Opponent", style={"textAlign": "left", "padding": "8px", "borderBottom": "2px solid #ddd"})
                ]))] +
                # Data rows
                [html.Tbody(rows)],
                style={"width": "100%", "borderCollapse": "collapse"}
            )
        ])
    
    return stats_cards, tournament_details

# Callback for year details
@app.callback(
    Output("year-details", "children"),
    Input("year-dropdown", "value")
)
def update_year_details(selected_year):
    if not selected_year:
        return "Select a year to see World Cup details"
    
    year_data = df[df['Year'] == selected_year].iloc[0]
    winner = year_data['Winner']
    runner_up = year_data['Runner_Up']
    host = year_data['Host']
    
    return [
        html.H4(f"{selected_year} FIFA World Cup"),
        html.P(f"Host: {host}"),
        html.P([
            html.Span("Winner: "),
            html.Span(winner, style={"color": "gold", "font-weight": "bold"})
        ]),
        html.P([
            html.Span("Runner-up: "),
            html.Span(runner_up, style={"color": "silver", "font-weight": "bold"})
        ])
    ]

# Callback for year map
@app.callback(
    Output("year-map", "figure"),
    Input("year-dropdown", "value")
)
def update_year_map(selected_year):
    if not selected_year:
        return {}
    
    year_data = df[df['Year'] == selected_year].iloc[0]
    winner = year_data['Winner']
    runner_up = year_data['Runner_Up']
    winner_iso = year_data['Winner_ISO']
    runner_up_iso = year_data['Runner_Up_ISO']
    
    # Create a simple dataset for the choropleth
    map_data = pd.DataFrame({
        'Country': [winner, runner_up],
        'ISO': [winner_iso, runner_up_iso],
        'Result': ['Winner', 'Runner-up'],
        'Value': [2, 1]  # Winner = 2, Runner-up = 1 for color coding
    })
    
    fig = px.choropleth(
        map_data,
        locations="ISO",
        color="Value",
        hover_name="Country",
        color_continuous_scale=[[0, "white"], [0.5, "silver"], [1, "gold"]],
        range_color=[0, 2],
        title=f"{selected_year} FIFA World Cup Results"
    )

    fig.update_geos(
        showcountries=True,
        countrycolor="Black",
        countrywidth=0.5 
    )
    
    
    fig.update_layout(
        coloraxis_showscale=False,
        geo=dict(
            showframe=False,
            showcoastlines=True,
            projection_type='natural earth'
        ),
        height=600,
        margin=dict(l=0, r=0, t=30, b=0)
    )
    
    # Add annotations for winner and runner-up
    fig.add_scattergeo(
        locations=[winner_iso],
        locationmode="ISO-3",
        text=[f"{winner} (Winner)"],
        mode="markers+text",
        marker=dict(size=15, color="gold", line=dict(width=2, color="black")),
        textposition="top center",
        name="Winner"
    )
    
    fig.add_scattergeo(
        locations=[runner_up_iso],
        locationmode="ISO-3",
        text=[f"{runner_up} (Runner-up)"],
        mode="markers+text",
        marker=dict(size=15, color="silver", line=dict(width=2, color="black")),
        textposition="bottom center",
        name="Runner-up"
    )
    
    return fig


if __name__ == '__main__':
    app.run(debug=True, port=8059)
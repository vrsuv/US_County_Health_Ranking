# import packages
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from dash import Dash, html, dash_table, dcc
from dash.dependencies import Input, Output

# ------------------------------- DATA PROCESSING -------------------------------
# Load dataset
df_rates = pd.read_csv('./malaria_deaths.csv')
df_ages = pd.read_csv('./malaria_deaths_age.csv')
df_inc = pd.read_csv('./malaria_inc.csv')

# Initialise the app
app = Dash(__name__)

# Function to perform Exploratory Data Analysis (EDA)
def perform_Eda(df_rates):
    years = sorted(df_rates['Year'].unique()) # Define years array
    countries = sorted(df_rates['Entity'].unique()) # Define countries array
    rates = df_rates['Deaths - Malaria - Sex: Both - Age: Age-standardized (Rate) (per 100,000 people)'] # Define rates array

    # To get the mean value of rates.
    avg_rate = rates.mean()

    # Function to get country and year of the highest malaria death rate.
    def get_max_info(df_rates):
        max_rate_record = df_rates.loc[df_rates['Deaths - Malaria - Sex: Both - Age: Age-standardized (Rate) (per 100,000 people)'].idxmax()]
        return max_rate_record['Deaths - Malaria - Sex: Both - Age: Age-standardized (Rate) (per 100,000 people)'], \
               max_rate_record['Entity'], max_rate_record['Year']

    max_rate, max_ctry, max_rate_year = get_max_info(df_rates)

    # Define a dictionary to store summary of information from EDA process
    eda_summary = {
        'years': years,
        'countries': countries,
        'max_rate': max_rate,
        'max_ctry': max_ctry,
        'max_rate_year': max_rate_year,
        'avg_rate': round(avg_rate, 2)
    }
    return eda_summary

# Get EDA summary
eda_summary = perform_Eda(df_rates)

# lists to split dataset to countries and regions
countries_list = df_rates[df_rates['Code'].notna()]
regions_list = df_rates[df_rates['Code'].isna()]

# ------------------------------- Visualisation 1 -------------------------------
# Vis 1: Create a heatmap for a default year to represent malaria_deaths dataset
def create_Heatmap(year):
    # Filter data for the selected year
    filtered_data = df_rates[df_rates['Year'] == year]
    countries = filtered_data['Entity']
    rates = filtered_data['Deaths - Malaria - Sex: Both - Age: Age-standardized (Rate) (per 100,000 people)']

    # Plotly Choropleth map
    fig = go.Figure(go.Choropleth(
        locations=countries,
        locationmode='country names',
        z=rates,
        text=countries,
        colorscale='Sunset',
        colorbar_title='Rate',
    ))
    # Define the layout for the heatmap
    fig.update_layout(
        title=f'Heatmap of Rates for Year {year}',
        geo=dict(showcoastlines=True, coastlinecolor="rgb(255, 255, 255)", projection={'type': 'natural earth'}),
        margin=dict(l=0, r=0, t=0, b=0)
    )
    return fig

# ------------------------------- Visualisation 2 -------------------------------
# Vis 2: Create line graph for malaria_deaths_age.csv dataset
def create_Linegraph():
    # Initialise empty dictionary to store yearly average deaths with age-group
    yearly_rates = {}

    # Get list of age groups
    age_groups = df_ages['age_group'].unique()

    # Get data by age_group and year
    for age_group in age_groups:
        age_data = df_ages[df_ages['age_group'] == age_group]
        age_data_grouped = age_data.groupby('year')['deaths'].mean().reset_index() # Find the mean

        # Store the mean values of deaths for each year
        for _, row in age_data_grouped.iterrows():
            year = row['year']
            avg_deaths = row['deaths']
            if year not in yearly_rates:
                yearly_rates[year] = {'age_groups': {}}  # Initialise for new years
            # Update the age_groups with respective average deaths
            yearly_rates[year]['age_groups'][age_group] = avg_deaths

    fig = go.Figure()

    # Loop over the age groups to create a line for each one
    for age_group in yearly_rates[next(iter(yearly_rates))]['age_groups']:
        # Extract the data for this age group across all years
        x_values = list(yearly_rates.keys())
        y_values = [yearly_rates[year]['age_groups'].get(age_group, 0) for year in x_values]
        
        # Add the line trace for the current age group
        fig.add_trace(go.Scatter(
            x=x_values,
            y=y_values,
            mode='lines+markers',
            name=age_group
        ))

    # Define the layout for the line graph
    fig.update_layout(
        title='Malaria Deaths by Age Group Over Time',
        xaxis_title='Year',
        yaxis_title='Total Deaths',
        showlegend=True
    )

    return fig

# ------------------------------- Visualisation 3 -------------------------------
# Vis 3: Bar chart to represent malaria_inc.csv dataset
# Function to get top 10 countries with highest incidence rates in the first year
def get_top10_ctries(df_inc):
    # Filter dataset to records containing the first year
    firstyr_data = df_inc[df_inc['Year'] == 2000]
    
    # Sort by incidence values to get top 10
    top10_ctries = firstyr_data.nlargest(10, 'Incidence of malaria (per 1,000 population at risk) (per 1,000 population at risk)')['Entity'].tolist()
    
    return top10_ctries

# Function to create bar charts
def create_Barchart(df_inc, top10_ctries):
    # Get the distinct years
    years = sorted(df_inc['Year'].unique())
    bar_charts = [] # Array to store a bar chart

    xaxis_range = [0, 800]

    for year in years:
        # Filter data for the current year and the top 10 countries
        year_data = df_inc[(df_inc['Year'] == year) & (df_inc['Entity'].isin(top10_ctries))]
        
        # Create a bar chart for each year
        bar_chart = go.Figure(go.Bar(
            x=year_data['Incidence of malaria (per 1,000 population at risk) (per 1,000 population at risk)'],
            y=year_data['Entity'],
            orientation='h',
            text=year_data['Incidence of malaria (per 1,000 population at risk) (per 1,000 population at risk)'],
        ))
        
        # Define the layout for a bar chart
        bar_chart.update_layout(
            title=f"Top 10 Malaria Death Rates in {year}",
            xaxis_title="Malaria Death Rate (per 100,000 people)",
            yaxis_title="Country",
            showlegend=False,
            xaxis=dict(range=xaxis_range)
        )
        
        bar_charts.append(bar_chart)

    return bar_charts


top10_ctries = get_top10_ctries(df_inc) # Get the top 10 countries for the first year
bar_charts = create_Barchart(df_inc, top10_ctries) # Create a bar chart

# ------------------------------- HTML Layout -------------------------------
app.layout = html.Div([
    html.Div(
        children='Malaria deaths', 
        style={'text-align': 'center', 
               'padding': '10px',
               'font-size': '30px',
               'font-family': 'Arial, sans-serif',
    }),
    # EDA summary section
    html.Div([
        html.H3("Exploratory Data Analysis (EDA) Summary"),
        html.P(f"Average Malaria Death Rate (per 100,000 people): {eda_summary['avg_rate']}"),
        html.P([
            "The year with the highest malaria death rate: ", html.U(str(eda_summary['max_rate_year'])), " at ", 
            html.U(eda_summary['max_ctry']), " with a rate of ", 
            html.U(str(eda_summary['max_rate'])), "."
        ])
    ], style={'padding': '20px', 
              'font-size': '20px', 
              'font-family': 'Arial, sans-serif',
              'border-radius': '5px',
    }),

    # Visualisation 1: Heatmap section with years slider
    html.H3("Visualisation 1: Heatmap - Malaria Death Rate per 100,000 People Globally",
            style={'textAlign': 'center'}),
    html.Div([
        html.Div([
            html.Label('Select Year:'),
            # Slider for year selection
            dcc.Slider(
                id='year-slider',
                min=min(eda_summary['years']),
                max=max(eda_summary['years']),
                step=1,
                value=2016,
                marks={year: str(year) for year in range(1990, 2016)},
                vertical = True,
                tooltip={
                    "style": {"fontSize": "15px"},
                },
            ),
        ], style={'margin-left': '25%', 'margin-top': '-1%', 'padding': '20px'}),
        html.Div([
            dcc.Graph(id='heatmap',
                    figure=create_Heatmap(2016),
                    style={'height': '400px', 'width': '100%'})
        ]),
    ], style={
        'display': 'flex',
        'border': '1px solid #ddd',
        'border-radius': '5px'
    }),

    # Visualisation 2: Line Graph Section
    html.Div(id="line-graph-section", children=[
        html.H3("Visualisation 2: Line Graph - Average Malaria Deaths by Age Group Globally", style={'textAlign': 'center'}),
        html.Div([
            dcc.Graph(id='line-graph', 
                      figure=create_Linegraph(), 
                      style={'height': '700px', 'width': '100%'})
        ]),
    ]),
    
    # Visualisation 3: Bar chart Section
    html.H3("Visualisation 3: Bar chart - Top 10 Counties' Incidence of Malaria over years", style={'textAlign': 'center'}),
    html.Div([
        dcc.Graph(figure=bar_chart) for bar_chart in bar_charts
    ], style={'display': 'flex', 'flex-wrap': 'wrap', 'justify-content': 'center'}),
])

# Callback to update heatmap based on selected year from the slider
@app.callback(
    Output('heatmap', 'figure'),
    [Input('year-slider', 'value')],
)
def update_heatmap(year):
    return create_Heatmap(year)

# Run the app
if __name__ == '__main__':
    app.run(debug=True)

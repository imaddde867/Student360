import os
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import plotly.express as px
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score
import dash
from dash import dcc, html
from dash.dependencies import Input, Output

# Initialize Dash app
app = dash.Dash(__name__)

# Load and clean the data
def load_and_merge_data(data_dir='data'):
    # Correct the file paths to point to the 'data' folder directly
    math_file = os.path.join(data_dir, 'student-mat.csv')
    port_file = os.path.join(data_dir, 'student-por.csv')

    try:
        math_df = pd.read_csv(math_file, sep=';')
        port_df = pd.read_csv(port_file, sep=';')
    except FileNotFoundError as e:
        raise FileNotFoundError(f"Error loading files: {e}")
    except pd.errors.ParserError as e:
        raise ValueError(f"Error parsing files: {e}")

    # Add subject identifier
    math_df['subject'] = 'math'
    port_df['subject'] = 'portuguese'

    # Merge datasets
    all_data = pd.concat([math_df, port_df], ignore_index=True)

    return all_data


def preprocess_data(df):
    df_clean = df.copy()

    # Convert binary columns
    binary_mapping = {'yes': 1, 'no': 0, 'U': 1, 'R': 0, 'LE3': 0, 'GT3': 1,
                      'T': 1, 'A': 0, 'F': 0, 'M': 1}
    binary_columns = ['schoolsup', 'famsup', 'paid', 'activities', 'nursery',
                      'higher', 'internet', 'romantic', 'address', 'famsize', 'Pstatus', 'sex']

    for col in binary_columns:
        df_clean[col] = df_clean[col].map(binary_mapping)

    # Create grade metrics
    df_clean['average_grade'] = (df_clean['G1'] + df_clean['G2'] + df_clean['G3']) / 3
    df_clean['grade_improvement'] = df_clean['G3'] - df_clean['G1']
    df_clean['grade_volatility'] = df_clean[['G1', 'G2', 'G3']].std(axis=1)

    # Create composite features
    df_clean['study_efficiency'] = df_clean['average_grade'] / df_clean['studytime']
    df_clean['alcohol_consumption'] = (df_clean['Dalc'] + df_clean['Walc']) / 2
    df_clean['parent_education'] = (df_clean['Medu'] + df_clean['Fedu']) / 2

    # Normalize numeric columns
    numeric_cols = ['age', 'absences', 'G1', 'G2', 'G3', 'average_grade',
                    'grade_improvement', 'grade_volatility', 'study_efficiency']
    scaler = StandardScaler()
    df_clean[numeric_cols] = scaler.fit_transform(df_clean[numeric_cols])

    return df_clean

# Calculate performance metrics
def calculate_performance_metrics(df):
    return {
        'average_grade': df['G3'].mean(),
        'pass_rate': (df['G3'] >= 10).mean() * 100,
        'improvement_rate': (df['grade_improvement'] > 0).mean() * 100
    }

# Create grade distribution visualization
def create_grade_distribution(df):
    fig = px.histogram(df, x='G3',
                       color='subject',
                       nbins=20,
                       title='Grade Distribution by Subject')
    return fig

# Analyze the impact factors
def analyze_impact_factors(df):
    factors = ['studytime', 'absences', 'failures', 'schoolsup', 'famsup',
               'paid', 'activities', 'internet']
    correlations = df[factors + ['G3']].corr()['G3'].sort_values()

    fig = px.bar(
        x=correlations.values,
        y=correlations.index,
        orientation='h',
        title='Impact Factors on Final Grade'
    )
    return fig

# Define the layout
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),  # This is important for URL handling
    html.H1('Student360 Analytics Dashboard'),

    dcc.Tabs([
        dcc.Tab(label='Overview', children=[
            html.Div([
                html.H3('Performance Metrics'),
                html.Div(id='performance-metrics'),
                dcc.Graph(id='grade-distribution')
            ])
        ]),

        dcc.Tab(label='Impact Analysis', children=[
            html.Div([
                html.H3('Factor Impact Analysis'),
                dcc.Graph(id='impact-factors')
            ])
        ]),

        dcc.Tab(label='Detailed Analysis', children=[
            html.Div([
                html.H3('Subject Performance Comparison'),
                dcc.Graph(id='subject-comparison')
            ])
        ])
    ])
])

# Create callbacks
@app.callback(
    Output('performance-metrics', 'children'),
    Output('grade-distribution', 'figure'),
    Output('impact-factors', 'figure'),
    Input('url', 'pathname')  # This will now work with the dcc.Location component
)
def update_dashboard(_):
    df = preprocess_data(load_and_merge_data())  # Corrected to use preprocess_data

    metrics = calculate_performance_metrics(df)
    grade_dist = create_grade_distribution(df)
    impact = analyze_impact_factors(df)

    metrics_div = html.Div([
        html.P(f"Average Grade: {metrics['average_grade']:.2f}"),
        html.P(f"Pass Rate: {metrics['pass_rate']:.1f}%"),
        html.P(f"Improvement Rate: {metrics['improvement_rate']:.1f}%")
    ])

    return metrics_div, grade_dist, impact


if __name__ == '__main__':
    app.run_server(debug=True)

#Dash-dependencies
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

#helper-functions
import chart_helper

#Cassandra-related
from cloud import session
from queries_dict import admin_queries

#other Python libs
from pandas import DataFrame
import json
import datetime

#helper functions
month_dict = {
  'January': 1,
 'February': 2,
  'March': 3,
  'April': 4,
  'May': 5,
  'June': 6,
  'July': 7,
  'August': 8,
  'September': 9,
  'October': 10,
  'November': 11,
  'December': 12
}


#external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
#external_stylesheets=external_stylesheets
app = dash.Dash(__name__, suppress_callback_exceptions=True)
server = app.server

app.layout = html.Div([
  #NOTE: header div
  html.Div([
    #NOTE: company logo
    html.Div([
      html.Img(src='assets/paper.png', className='logo')
    ],
    className='logo-container'
    ),
    #NOTE: title
    html.Div([
      html.H1('OB3 Admin Dashboard')
    ],
    className='title-container'
    ),
    #NOTE: external link
    html.Div([
      html.A('Learn More', href='https://www.ob3.io/', target='_blank')
    ],
    className='link-container'
    )
  ],
  className='header-container'
  ),

  #NOTE: general filter container
  html.Div([ 
    html.Div([
      dcc.Dropdown(
        id='association-filter',
        options=[{'label': i, 'value': i} for i in ['uniA', 'uniB', 'uniC']],
        placeholder='Select Association'
      )    
    ]
    ),

    html.Div([
      dcc.Dropdown(
        id='month-filter',
        options=[{'label': key, 'value': month_dict[key]} for key in month_dict.keys()],
        clearable=False,
        value=1
      )
    ],
    ),
  ],
  className='general-filter-container'
  ),
  

  html.Div([
  
    html.Div(
        [html.H2(id="total-distinct-users"), html.H4("Distinct Users")],
        id="distinct-users",
        className="stat-container",
    ),
    
    html.Div(
        [html.H2(id="total-logins"), html.H4("Login Sessions")],
        id="logins",
        className="stat-container",
    ),

    html.Div(
        [html.H2(id="total-new-users-sessions"), html.H4("Sessions By New Users")],
        id="new-users",
        className="stat-container",
    ),

    html.Div(
        [html.H2(id="total-data-usage"), html.H4("MB Data Usage")],
        id="data",
        className="stat-container",
    ),

    html.Div(
        [html.H2(id="total-new-resources"), html.H4("New Resources")],
        id="resources",
        className="stat-container",
    )
  ],
  className="stat-box-container",
  ),
  
  #NOTE: login-chart-filter-container

  html.Div([
    #NOTE: status
    html.Div([
      dcc.Dropdown(
        id='login-chart-status-filter',
        options=[{'label': i, 'value': i} for i in ['student', 'teacher', 'alumnus']],
        placeholder='Select Status'
      )
    ]),

    html.Div([
      dcc.Dropdown(
        id='login-chart-frequency-filter',
        options=[{'label': i, 'value': i} for i in ['Daily', 'Weekly']],
        value='Daily',
        clearable=False,
      )
    ]),
    
    html.Div([
      dcc.Dropdown(
        id='login-chart-chart-type-filter',
        options=[{'label': i, 'value': i} for i in ['Bar Chart', 'Line Chart', 'Scatter Chart']],
        value='Bar Chart',
        clearable=False,
      )
    ])
  ],
  className='login-chart-filter-container'
  ),
  
  
  
  html.Div([
    dcc.Loading(children=html.Div(id='login-data-and-graph-container'))
  ],
  className='user-activity-graph-container'),
  
  html.Div([
    #NOTE: course filter
    html.Div(id='data-chart-course-filter-container', 
      children=[
        dcc.Dropdown(
          id='data-chart-course-filter',
          placeholder='Select A Course',
          disabled=True
        )
      ])   
  ],
  className='data-chart-filter-container'
  ),
  
  html.Div([
    dcc.Loading(children=html.Div(id='data-usage-data-and-graph-container'))
  ],
  className='data-usage-graph-container'),
  
],
className='main-container'
)

#NOTE: refetch login data when a new month is picked
@app.callback(
  Output('login-data-and-graph-container', 'children'),
  [Input('month-filter', 'value')])
def get_and_store_login_data(selected_month):
  rows = session.execute(admin_queries['logins_over_time'], [selected_month])
  df = DataFrame(rows)
  jsonified_data = df.to_json(date_format='iso')
  hidden_data_div = html.Div(id='jsonified-login-df', 
                             children=jsonified_data, 
                             style={'display': 'none'})
  graph=dcc.Graph(id='user_activity_graph')
  return [hidden_data_div, graph]

@app.callback(
  Output('data-usage-data-and-graph-container', 'children'),
  [Input('month-filter', 'value')])
def get_and_store_usage_data(selected_month):
  rows = session.execute(admin_queries['data_usage_by_month'], [selected_month])
  df = DataFrame(rows)
  jsonified_data = df.to_json(date_format='iso')
  hidden_data_div = html.Div(id='jsonified-data-usage-df', 
                             children=jsonified_data, 
                             style={'display' : 'none'})
  graph=dcc.Graph(id='data_usage_graph')
  return [hidden_data_div, graph]


#NOTE: update login chart on new filter
@app.callback(
  Output('user_activity_graph', 'figure'),
  [Input('jsonified-login-df', 'children'),
   Input('association-filter', 'value'),
   Input('login-chart-status-filter', 'value'),
   Input('login-chart-chart-type-filter', 'value'),
   Input('login-chart-frequency-filter', 'value')],
  [State('month-filter', 'value')]
)
def update_login_chart_on_filter_change(jsonified_df, association, status, chart_type, frequency, month):
  if jsonified_df is None:
    print("Nothing to show for!")
    raise PreventUpdate
  else:
    df = chart_helper.decode_json_df(jsonified_df)
    #print(df.head())
    if (association == None):
      if (status == None):
        fig = chart_helper.make_login_chart(df, month, frequency=frequency[0], chart_type=chart_type)
        #print(fig.data)
        return fig
      else:
        fig = chart_helper.make_login_chart(df, month, status=status, frequency=frequency[0], chart_type=chart_type)
        #print(fig.data)
        return fig
    else:
      if (status == None):
        fig = chart_helper.make_login_chart(df, month, association=association, frequency=frequency[0], chart_type=chart_type)
        #print(fig.data)
        return fig
      else:
        fig = chart_helper.make_login_chart(df, month, association, status, frequency=frequency[0], chart_type=chart_type)
        #print(fig.data)
        return fig

#NOTE: return new options for each association
@app.callback(
  Output('data-chart-course-filter', 'options'),
  [Input('association-filter', 'value')],
  [State('jsonified-data-usage-df', 'children')]
)
def update_data_chart_course_filter(association, jsonified_df):
  if (jsonified_df is None):
    raise PreventUpdate
  else:
    df = chart_helper.decode_json_df(jsonified_df)
    options = chart_helper.get_course_filter_options(df, association)
    return options

#NOTE: enable/disable course filter
@app.callback(
  Output('data-chart-course-filter', 'disabled'),
  [Input('association-filter', 'value')],
  [State('jsonified-data-usage-df', 'children')]
)
def update_data_chart_course_filter(association, jsonified_df):
  if (jsonified_df is None) or (association == None):
    return True
  else:
    return False

#NOTE: give course filter None value when user selects a new association
@app.callback(
  Output('data-chart-course-filter', 'value'),
  [Input('association-filter', 'value')],
  [State('jsonified-data-usage-df', 'children')]
)
def update_data_chart_course_filter(association, jsonified_df):
  return None
  

#NOTE: update usage chart on new filter
@app.callback(
  Output('data_usage_graph', 'figure'),
  [Input('jsonified-data-usage-df', 'children'),
   Input('association-filter', 'value'),
   Input('data-chart-course-filter', 'value')],
  [State('month-filter', 'value')]
)
def update_file_usage_chart(jsonified_df, association=None, course_id=None, month=None):
	if jsonified_df is None:
		raise PreventUpdate
	else:
		df = chart_helper.decode_json_df(jsonified_df)
	
		if (course_id == None) and (association == None):
			fig = chart_helper.make_aggregate_data_usage_chart(df, association, course_id, month)
			return fig
		elif (association != None) and (course_id == None):
			filtered_df = df[df['association'] == association]
			fig = chart_helper.make_data_bar_chart_facetted_by(filtered_df, 'course_id', association, course_id, month)
			return fig
		elif (association == None and course_id != None):
			raise PreventUpdate
		else:
    #NOTE: need to use bitwise operator with pandas (can't use And or Or)
			filt = (df['association'] == association) & (df['course_id'] == course_id)
			filtered_df = df[filt]
			fig = chart_helper.make_data_bar_chart_facetted_by(filtered_df, 'paper_id', association, course_id, month)
			return fig


#ANCHOR: cbs for stat boxes: total-logins, total-distinct-users, total-data-usage
@app.callback(
  Output('total-logins', 'children'),
  [Input('jsonified-login-df', 'children'), 
   Input('association-filter', 'value')]
)
def display_total_logins_by_association(jsonified_df, association):
  if (jsonified_df is None):
      raise PreventUpdate
  else:
    return chart_helper.get_total_logins_by_association(jsonified_df, association)

@app.callback(
  Output('total-distinct-users', 'children'),
  [Input('jsonified-login-df', 'children'), 
   Input('association-filter', 'value')]
)
def display_total_distinct_users_by_association(jsonified_df, association):
  if (jsonified_df is None):
    raise PreventUpdate
  else:
    return chart_helper.get_total_distinct_users_by_association(jsonified_df, association)

@app.callback(
  Output('total-new-users-sessions', 'children'),
  [Input('jsonified-login-df', 'children'), 
   Input('association-filter', 'value')]
)
def display_total_new_users_sessions_by_association(jsonified_df, association):
  if (jsonified_df is None):
    raise PreventUpdate
  else:
    return chart_helper.get_total_new_users_sessions_by_association(jsonified_df, association)

@app.callback(
  Output('total-data-usage', 'children'),
  [Input('jsonified-data-usage-df', 'children'), 
   Input('association-filter', 'value')]
)
def display_total_distinct_users_by_association(jsonified_df, association):
  if (jsonified_df is None):
    raise PreventUpdate
  else:
    return chart_helper.get_total_data_usage_by_association(jsonified_df, association)

@app.callback(
  Output('total-new-resources', 'children'),
  [Input('jsonified-data-usage-df', 'children'), 
   Input('association-filter', 'value')]
)
def display_total_new_resources_by_association(jsonified_df, association):
  if (jsonified_df is None):
    raise PreventUpdate	
  else:
    return chart_helper.get_total_resources_by_association(jsonified_df, association)



#NOTE: run app in debug mode
if __name__ == '__main__':
  app.run_server(debug=True)
  
  '''app.run_server(debug=False,
                 dev_tools_ui=False,
                 dev_tools_props_check=False)'''


#TODO: https://dash.plotly.com/deployment try to deploy / polish display


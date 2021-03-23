import pandas as pd
import matplotlib.pyplot as plt
from fpdf import FPDF
import argparse
import plotly.express as px
import plotly.graph_objects as go

# import datetime as dt
def divide_day(df, label):
	print (pd.to_datetime(df['T']))

	df=df.assign(session=pd.cut(pd.to_datetime(df['T']).dt.hour,
                            [0,6,12,18,23],
                            labels=['Night','Morning','Afternoon','Evening'],
                            include_lowest=True))
	session_mean = df.groupby(['session']).mean()
	print(session_mean['HR'].values)
	fig = px.line(session_mean, width=1000, height=600, text=session_mean['HR'].values.astype(int), title="Heartbeat Daily Statistics")
	fig.update_xaxes(
		title = "Time",
        )
	fig.update_yaxes(
		title = "Beats Per Minute"
        )
	fig.update_traces(textposition='top center', marker_color='lightsalmon')
	filename = "divide_{}.png".format(label)
	fig.write_image(filename)
	# plt.figure(figsize=(20,10)) 
	# plt.title("Daily statistic for {}".format(label), size=25, y=1.02)
	# plt.plot(session_mean.index, session_mean[label])
	# plt.xticks(size = 20)
	# plt.yticks(size = 20)
	# for a,b in zip(session_mean.index,session_mean[label]):
	#     plt.text(a, b+0.1, '%.1f' % b, ha='center', va= 'bottom',fontsize=20)
	# filename = "divide_{}.png".format(label)
	# plt.savefig(filename)
	return [filename]

# stacked area chart for heartbeat
def draw_stacked_chart(df, filtered_df):
	hr_data = df["HR"]
	hr_quantile = hr_data.quantile([.33, .66, 1])
	low_data = filtered_df[filtered_df["HR"] < hr_quantile[0.33]]
	low_size = low_data.set_index(pd.DatetimeIndex(pd.to_datetime(low_data['T']))).groupby(pd.Grouper(freq='D')).count()['HR']
	medium_data = filtered_df[filtered_df["HR"] < hr_quantile[0.66]]
	medium_size = medium_data.set_index(pd.DatetimeIndex(pd.to_datetime(medium_data['T']))).groupby(pd.Grouper(freq='D')).count()['HR']
	high_data = filtered_df[filtered_df["HR"] < hr_quantile[1]]
	high_size = high_data.set_index(pd.DatetimeIndex(pd.to_datetime(high_data['T']))).groupby(pd.Grouper(freq='D')).count()['HR']
	dates = high_size.index
	plt.figure(figsize=(20,10)) 
	plt.title("Stacked Area Chart for HR", size=25, y=1.02)
	plt.stackplot(dates,low_size, medium_size, high_size, labels=['Low','Medium','High'])
	plt.xticks(dates, rotation=30, size = 20)
	plt.yticks(size = 20)
	plt.legend(loc='upper left', fontsize=25)
	filename = "stacked_HR.png"
	plt.savefig(filename)
	return [filename]


# filtering data according to deviceid, start date, and end date
def filtering_data(df, deviceid, start_date, end_date, operation):
	filtered_df = df.loc[df['DeviceId'] == deviceid]
	filtered_df = filtered_df[(filtered_df['T'] > start_date) & (filtered_df['T'] < end_date)]
	if operation == 'sum':
		day_df = filtered_df.set_index(pd.DatetimeIndex(pd.to_datetime(filtered_df['T']))).groupby(pd.Grouper(freq='D')).sum()
	elif operation == 'mean':
		day_df = filtered_df.set_index(pd.DatetimeIndex(pd.to_datetime(filtered_df['T']))).groupby(pd.Grouper(freq='D')).mean()
	elif operation == 'max-min':
		day_df = filtered_df.set_index(pd.DatetimeIndex(pd.to_datetime(filtered_df['T']))).groupby(pd.Grouper(freq='D'))['Count'].agg(['max','min'])
		day_df['Count'] = day_df['max']-day_df['min']
	elif operation == 'max':
		day_df = filtered_df.set_index(pd.DatetimeIndex(pd.to_datetime(filtered_df['T']))).groupby(pd.Grouper(freq='D')).max()
	elif operation == 'min':
		day_df = filtered_df.set_index(pd.DatetimeIndex(pd.to_datetime(filtered_df['T']))).groupby(pd.Grouper(freq='D')).min()
	return day_df, filtered_df

# save figures and return figure file names
def draw_figure(data_type, df, title, ylabel, n_bins, weekdays, mean_value, ytick, max_df = None, min_df = None, max_min = False):
	filename = "images_{}.png".format(data_type)
	filenames = []
	colors = []
	df = df.dropna()
	df[ylabel] = df[ylabel] - mean_value
	print(df[ylabel])
	fig = px.area(x=df.index.date, y = df[ylabel], width=1000, height=600, text=df[ylabel] + mean_value, title=title)
	if max_min:
		max_df = max_df.dropna()
		min_df = min_df.dropna()
		fig.add_trace(go.Scatter(
			x=df.index.date,
			y=max_df[ylabel] - mean_value,
			connectgaps=True, # override default to connect the gaps
			name = "max"
		))
		fig.add_trace(go.Scatter(
			x=df.index.date,
			y=min_df[ylabel] - mean_value,
			connectgaps=True, # override default to connect the gaps
			name = "min"
		))
	full_fig = fig.full_figure_for_development()
	space = (int(full_fig.layout.yaxis.range[1]) - int(full_fig.layout.yaxis.range[0]))//10
	fig.update_yaxes(tickmode = 'array',
		tickvals = list(range(int(full_fig.layout.yaxis.range[0]), int(full_fig.layout.yaxis.range[1]), space)),
		ticktext = list(range(int(full_fig.layout.yaxis.range[0] + mean_value), int(full_fig.layout.yaxis.range[1] + mean_value), space))
		)
	# fig.update_xaxes(
	# 	title = "Date",
	# 	type='category',
	# 	tickangle=45,
	# 	dtick="D1"
 #        )
	fig.update_xaxes(
		title = "Date",
		tickangle=45,
		dtick="D1"
        )
	fig.update_yaxes(
		title = ytick
        )
	fig.update_traces(texttemplate='%{text:.1s}', textposition='top center')
	for date in df.index.date:
		if str(date.weekday()) in weekdays:
			fig.add_vline(x=date, line_color="orange", line_width=1, line_dash="dash")
	fig.write_image(filename)
	filenames.append(filename)
	# plt.savefig(filename)
	return filenames

# generate pdf according to imagelist
def generate_pdf(deviceid, imagelist):
	pdf = FPDF()
	pdf.add_font('ArialUnicode',fname='arial-unicode-ms.ttf',uni=True)
	pdf.set_font('ArialUnicode')
	# imagelist is the list with all image filenames
	pdf.set_auto_page_break(0)
	for i in range(len(imagelist)):
		if i % 2 == 0:
			pdf.add_page()
			pdf.cell(w=100,txt = '{} Report'.format(deviceid))
		pdf.image(imagelist[i], w=190, x=10, y=130*(i%2) + 30)
	pdf.output("{}_report.pdf".format(deviceid), "F")

def draw_scale_data(df, ylabel1, ylabel2, start_date, end_date, weekdays):
	filenames = []
	df = df[df['Date'] > "2021-01-01"]
	mean_value1 = df[ylabel1].mean()
	df['Date'] =pd.to_datetime(df.Date)
	df = df.sort_values(by='Date')
	df[ylabel1] = df[ylabel1] - mean_value1
	fig = px.area(x=df['Date'].dt.date, y = df[ylabel1], width=1000, height=600, text=df[ylabel1] + mean_value1, title="Weight Changes")
	full_fig = fig.full_figure_for_development()
	space = (int(full_fig.layout.yaxis.range[1] + 10) - int(full_fig.layout.yaxis.range[0]))//10
	fig.update_yaxes(tickmode = 'array',
		tickvals = list(range(int(full_fig.layout.yaxis.range[0]), int(full_fig.layout.yaxis.range[1]), space)),
		ticktext = list(range(int(full_fig.layout.yaxis.range[0] + mean_value1), int(full_fig.layout.yaxis.range[1] + mean_value1), space))
		)
	fig.update_xaxes(
		title = "Date",
		dtick="D1",
		tickangle=45
        )
	fig.update_yaxes(
		title = ylabel1
        )
	for date in pd.date_range(start=full_fig.layout.xaxis.range[0],end=full_fig.layout.xaxis.range[1]):
		if str(date.weekday()) in weekdays:
			fig.add_vline(x=date, line_color="orange", line_width=1, line_dash="dash")
	fig.update_traces(textposition='top right')
	filename = ylabel1 + ".jpg"
	fig.write_image(filename)
	filenames.append(filename)


	mean_value2 = df[ylabel2].mean()
	df[ylabel2] = df[ylabel2] - mean_value2
	fig = px.area(x=df['Date'].dt.date, y = df[ylabel2], width=1000, height=600, text=df[ylabel2] + mean_value2, title="Hydration Changes")
	full_fig = fig.full_figure_for_development()
	print(full_fig.layout.yaxis.range)
	space = (int(full_fig.layout.yaxis.range[1] + 10) - int(full_fig.layout.yaxis.range[0]))//10
	fig.update_yaxes(tickmode = 'array',
		tickvals = list(range(int(full_fig.layout.yaxis.range[0]), int(full_fig.layout.yaxis.range[1]), space)),
		ticktext = list(range(int(full_fig.layout.yaxis.range[0] + mean_value2), int(full_fig.layout.yaxis.range[1] + mean_value2), space))
		)
	fig.update_traces(textposition='top center', connectgaps=True)
	fig.update_xaxes(
		title = "Date",
		dtick="D1",
		tickangle=45
        )
	fig.update_yaxes(
		title = ylabel2
        )
	for date in pd.date_range(start=full_fig.layout.xaxis.range[0],end=full_fig.layout.xaxis.range[1]):
		if str(date.weekday()) in weekdays:
			fig.add_vline(x=date, line_color="orange", line_width=1, line_dash="dash")
	filename = ylabel2 + ".jpg"
	fig.write_image(filename)
	filenames.append(filename)
	return filenames

def main(args):
	filenames = []
	heartrate_df = pd.read_csv('Smartwatch_HeartRateDatum.csv')
	filtered_heart_df, not_group_by_filtered_df = filtering_data(heartrate_df, args.deviceid, args.start_date, args.end_date, operation="mean")
	print (filtered_heart_df)
	filtered_heart_df_max, not_group_by_filtered_df_max = filtering_data(heartrate_df, args.deviceid, args.start_date, args.end_date, operation="max")
	print (filtered_heart_df_max)
	filtered_heart_df_min, not_group_by_filtered_df_min = filtering_data(heartrate_df, args.deviceid, args.start_date, args.end_date, operation="min")
	divide_hr_filenames = divide_day(not_group_by_filtered_df, "HR")
	hear_filenames = draw_figure('heart1', filtered_heart_df, "Daily Heart Rate Average (orange vertical line dialysis date)", "HR", 15, ytick = "HeartRate (Beats per minute)", weekdays = args.dialysis_session, mean_value = filtered_heart_df["HR"].mean(), max_df = filtered_heart_df_max, min_df=filtered_heart_df_min, max_min=True)
	filenames += hear_filenames
	fluid_df = pd.read_csv('Smartwatch_FluidDatum.csv')
	#divide_fluid_filenames = divide_day(fluid_df, "Volume")
	filtered_fluid_df, _ = filtering_data(fluid_df, args.deviceid, args.start_date, args.end_date, operation="sum")
	fluid_filenames = draw_figure('fluid', filtered_fluid_df, "Daily Fluid Intake Volume (orange vertical line dialysis date)", "Volume", 15, ytick = "Volume of fluid intake (oz)", weekdays = args.dialysis_session,  mean_value = filtered_fluid_df["Volume"].mean())
	step_df = pd.read_csv('Smartwatch_StepCountDatum.csv')
	# divide_step_filenames = divide_day(step_df, "Count")
	filtered_step_df, _ = filtering_data(step_df, args.deviceid, args.start_date, args.end_date, operation="max-min")
	step_filenames = draw_figure('step', filtered_step_df, "Daily Step Count (orange vertical line dialysis date)", "Count", 15, ytick = "Number of steps" , weekdays = args.dialysis_session,  mean_value = filtered_step_df['Count'].mean())
	filenames +=  divide_hr_filenames + fluid_filenames + step_filenames
	fluisense_email_df = pd.read_excel("Fluisense Emails.xlsx")
	columnNames = fluisense_email_df.iloc[0] 
	fluisense_email_df = fluisense_email_df[1:] 
	fluisense_email_df.columns = columnNames
	participant_df = fluisense_email_df[fluisense_email_df['Device ID'] == args.deviceid]
	baseline_weight = participant_df['Weight'].values[0]
	user = participant_df['Watch/Box#'].values[0]
	weight_df = pd.read_csv("Scale Data\Scale Data\data_{}_Scale\weight.csv".format(user))
	scale_filenames = draw_scale_data(weight_df, "Weight (lb)", "Hydration (lb)", args.start_date, args.end_date, args.dialysis_session)
	filenames += scale_filenames
	# pass image filenames as imagelist
	generate_pdf(args.deviceid, filenames)


if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument("--deviceid", help="deviceid", default="45eb179e1d93ae0d")
	parser.add_argument("--start_date", help="yyyy-mm-dd", default="2021-01-12")
	parser.add_argument("--end_date", help="yyyy-mm-dd", default="2021-02-29")
	parser.add_argument("--dialysis_session", type=list, help="yyyy-mm-dd", default="246")
	args = parser.parse_args()
	main(args)
import pandas as pd
import matplotlib.pyplot as plt
from fpdf import FPDF
import argparse

# filtering data according to deviceid, start date, and end date
def filtering_data(df, deviceid, start_date, end_date, operation):
	filtered_df = df.loc[df['DeviceId'] == deviceid]
	filtered_df = filtered_df[(filtered_df['T'] > start_date) & (filtered_df['T'] < end_date)]
	if operation == 'sum':
		day_df = filtered_df.set_index(pd.DatetimeIndex(pd.to_datetime(filtered_df['T']))).groupby(pd.Grouper(freq='D')).sum()
	elif operation == 'mean':
		day_df = filtered_df.set_index(pd.DatetimeIndex(pd.to_datetime(filtered_df['T']))).groupby(pd.Grouper(freq='D')).mean()
	elif operation == 'max':
		day_df = filtered_df.set_index(pd.DatetimeIndex(pd.to_datetime(filtered_df['T']))).groupby(pd.Grouper(freq='D')).max()
	return day_df

# save figures and return figure file names
def draw_figure(data_type, df, title, ylabel):
	# Line chart
	filenames = []
	plt.figure(figsize=(20,10)) 
	plt.title(title, size=25, y=1.02)
	plt.ylabel(ylabel)
	plt.plot(df.index, df[ylabel])
	for a,b in zip(df.index,df[ylabel]):
	    plt.text(a, b+0.1, '%.1f' % b, ha='center', va= 'bottom',fontsize=15)
	plt.xticks(df.index, rotation=30, size=15)
	plt.yticks(size=15)
	filename = "line_{}.png".format(data_type)
	filenames.append(filename)
	plt.savefig(filename)
	# Bar chart
	plt.figure(figsize=(20,10)) 
	plt.title(title, size=25, y=1.02)
	plt.ylabel(ylabel)
	plt.bar(df.index, df[ylabel])
	for a,b in zip(df.index,df[ylabel]):
	    plt.text(a, b+0.1, '%.1f' % b, ha='center', va= 'bottom',fontsize=15)
	plt.xticks(df.index, rotation=30, size=15)
	plt.yticks(size=15)
	filename = "bar_{}.png".format(data_type)
	filenames.append(filename)
	plt.savefig(filename)
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

def main(args):
	filenames = []
	heartrate_df = pd.read_csv('Smartwatch_HeartRateDatum.csv')
	filtered_heart_df = filtering_data(heartrate_df, args.deviceid, args.start_date, args.end_date, operation="mean")
	hear_filenames = draw_figure('heart', filtered_heart_df, "Daily Heart Rate Average", "HR")
	fluid_df = pd.read_csv('Smartwatch_FluidDatum.csv')
	filtered_fluid_df = filtering_data(fluid_df, args.deviceid, args.start_date, args.end_date, operation="sum")
	fluid_filenames = draw_figure('fluid', filtered_fluid_df, "Daily Fluid Intake Volume", "Volume")
	step_df = pd.read_csv('Smartwatch_StepCountDatum.csv')
	filtered_step_df = filtering_data(step_df, args.deviceid, args.start_date, args.end_date, operation="max")
	step_filenames = draw_figure('step', filtered_step_df, "Daily Step Count", "Count")
	filenames = hear_filenames + fluid_filenames + step_filenames
	print(filenames)
	# pass image filenames as imagelist
	generate_pdf(args.deviceid, filenames)


if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument("--deviceid", help="deviceid")
	parser.add_argument("--start_date", help="yyyy-mm-dd")
	parser.add_argument("--end_date", help="yyyy-mm-dd")
	args = parser.parse_args()
	main(args)
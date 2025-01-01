import matplotlib
matplotlib.use('Agg')  # Force Matplotlib to use a non-GUI backend

from django.shortcuts import render
from .forms import CSVUploadForm
import pandas as pd
import os
from django.conf import settings
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
import base64

def upload_csv(request):
    data = None
    stats = None
    histograms = []
    pie_charts = []
    boxplots = []
    correlation_heatmap = None
    pairplot_image = None
    missing_values = None

    if request.method == 'POST':
        form = CSVUploadForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = request.FILES['csv_file']
            file_path = os.path.join(settings.MEDIA_ROOT, csv_file.name)

            # Ensure the media directory exists
            os.makedirs(settings.MEDIA_ROOT, exist_ok=True)

            # Save the uploaded file
            with open(file_path, 'wb+') as f:
                for chunk in csv_file.chunks():
                    f.write(chunk)

            # Read and process CSV/Excel file using pandas
            try:
                if csv_file.name.endswith('.csv'):
                    df = pd.read_csv(file_path)
                elif csv_file.name.endswith(('.xls', '.xlsx')):
                    df = pd.read_excel(file_path, engine='openpyxl')
                else:
                    raise ValueError("Unsupported file format. Please upload a CSV or Excel file.")

                # Convert data to HTML tables
                data = df.head().to_html(classes='table table-striped')
                stats = df.describe().to_html(classes='table table-bordered')

                # Handle missing values
                missing_values = df.isnull().sum().to_dict()

                # Generate histograms for numerical columns
                for column in df.select_dtypes(include=['number']).columns:
                    plt.figure()
                    sns.histplot(df[column].dropna(), kde=True)
                    plt.title(f"Histogram of {column}")
                    buffer = BytesIO()
                    plt.savefig(buffer, format='png')
                    buffer.seek(0)
                    image_png = buffer.getvalue()
                    buffer.close()
                    base64_image = base64.b64encode(image_png).decode('utf-8')
                    histograms.append(base64_image)
                    plt.close()  # Close the figure to free memory

                # Generate pie chart for a categorical column (adjust as per your data)
                if 'Preferred Payment Method' in df.columns:
                    payment_method_counts = df['Preferred Payment Method'].value_counts()
                    plt.figure(figsize=(8, 8))
                    payment_method_counts.plot(kind='pie', autopct='%1.1f%%', startangle=90)
                    plt.title('Preferred Payment Method Distribution')
                    buffer = BytesIO()
                    plt.savefig(buffer, format='png')
                    buffer.seek(0)
                    image_png = buffer.getvalue()
                    buffer.close()
                    base64_image = base64.b64encode(image_png).decode('utf-8')
                    pie_charts.append(base64_image)
                    plt.close()  # Close the figure to free memory

                # Generate boxplots for numerical columns
                for column in df.select_dtypes(include=['number']).columns:
                    plt.figure(figsize=(8, 6))
                    sns.boxplot(x=df[column])
                    plt.title(f"Boxplot of {column}")
                    buffer = BytesIO()
                    plt.savefig(buffer, format='png')
                    buffer.seek(0)
                    image_png = buffer.getvalue()
                    buffer.close()
                    base64_image = base64.b64encode(image_png).decode('utf-8')
                    boxplots.append(base64_image)
                    plt.close()  # Close the figure to free memory

                # Generate a correlation heatmap (if possible)
                numerical_columns = df.select_dtypes(include=['number'])
                if numerical_columns.shape[1] > 1:  # Check if there are multiple numerical columns
                    corr_matrix = numerical_columns.corr()
                    plt.figure(figsize=(10, 8))
                    sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', fmt='.2f')
                    plt.title('Correlation Heatmap')
                    buffer = BytesIO()
                    plt.savefig(buffer, format='png')
                    buffer.seek(0)
                    image_png = buffer.getvalue()
                    buffer.close()
                    correlation_heatmap = base64.b64encode(image_png).decode('utf-8')
                    plt.close()  # Close the figure to free memory
                else:
                    correlation_heatmap = None  # No heatmap if there is less than 2 numerical columns

                # Generate pairplot (only for numerical columns)
                if numerical_columns.shape[1] > 1:  # Check if there are multiple numerical columns
                    sns.set(style='whitegrid')
                    pairplot = sns.pairplot(numerical_columns)
                    plt.title('Pairplot')
                    buffer = BytesIO()
                    pairplot.savefig(buffer, format='png')
                    buffer.seek(0)
                    image_png = buffer.getvalue()
                    buffer.close()
                    pairplot_image = base64.b64encode(image_png).decode('utf-8')
                    plt.close()  # Close the figure to free memory
                else:
                    pairplot_image = None  # No pairplot if there is less than 2 numerical columns

            except Exception as e:
                return render(request, 'analysis/upload_csv.html', {
                    'form': form,
                    'error': f"Error processing file: {e}"
                })

    else:
        form = CSVUploadForm()

    return render(request, 'analysis/upload_csv.html', {
        'form': form,
        'data': data,
        'stats': stats,
        'missing_values': missing_values,
        'histograms': histograms,
        'pie_charts': pie_charts,
        'boxplots': boxplots,
        'correlation_heatmap': correlation_heatmap,
        'pairplot_image': pairplot_image,
    })

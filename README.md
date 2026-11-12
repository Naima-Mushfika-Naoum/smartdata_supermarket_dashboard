# SmartData | Supermarket Sales Dashboard

SmartData is an interactive dashboard for exploring supermarket sales and reviewing historical next-day sales forecasts across three branches. The browser demo runs from the repository's `index.html`. The original Python dashboard is also included.

## Try the dashboard

Open `index.html` in your browser.

- **Sales Dashboard:** Filter by branch and date, compare five sales metrics with the preceding period, explore product categories and daily sales, and download the filtered receipts as a CSV.
- **Sales Forecasts:** Select a branch and compare actual sales with the Ridge regression forecast and the previous day's sales. The tab shows mean absolute error (MAE) and the number of forecasts within 20% of actual sales.

## Dataset

This project uses [Supermarket Sales Dataset](https://www.kaggle.com/datasets/faresashraf1001/supermarket-sales), published on Kaggle by **Fares Ashraf** (`faresashraf1001`). The source file is `data/kaggle_dataset/SuperMarket Analysis.csv`. It contains **1,000 receipts**, **17 columns**, and three branch labels (**Alex, Cairo, and Giza**) from **1 January to 30 March 2019**. The dashboard uses the recorded sales amounts, which include tax.

## Forecasting results

The forecasting task was to predict the next day's sales for each branch. Ridge regression used yesterday's sales, sales from the same weekday one week earlier, the branch, and the weekday. Models were developed on earlier dates, and the original Ridge model was evaluated on **10–30 March 2019**. All methods below were scored on the same **60 branch-days**.

| Method | MAE ↓ | Forecasts within 20% ↑ |
| --- | ---: | ---: |
| Yesterday's sales | 829.57 | 9 of 60 |
| Same weekday last week | 974.81 | 3 of 60 |
| Ridge regression | **606.55** | **18 of 60** |

Ridge reduced MAE by **26.9%** against the strongest simple baseline. Its forecasts were within 20% of actual sales on **30% of scored branch-days**, which shows the limits of the prototype for daily planning. The browser demo displays saved historical forecasts from `reports/final_test_predictions.csv`.

## Run the Python app locally

From the repository root:

```bash
python -m pip install -r requirements.txt
python src/app.py
```

## Repository files

| Path | Contents |
| --- | --- |
| `index.html` | Browser dashboard for GitHub Pages |
| `src/` | Python Gradio app, data loading, and charts |
| `data/` | Source transaction CSV |
| `reports/` | Saved March forecast results |
| `requirements.txt` | Python dependencies |

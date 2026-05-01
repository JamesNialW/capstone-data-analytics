# Feature‑Driven Sales Insights for Knit & Crochet Patterns: ML + Power BI

This capstone project analyzes sales performance of knit and crochet patterns using machine learning and Power BI. The project utilizes data from Ravelry, a popular online community for knitters and crocheters, to uncover insights and trends in pattern sales.

The goal is to understand what drives pattern sales and to identify key features that contribute to successful patterns. By applying machine learning techniques, we can predict sales performance based on various pattern attributes and customer preferences.

This project uses real-world data from Ravelry (via the public API) and applies a full analytics workflow:

- Data cleaning & feature engineering
- Exploratory data analysis
- Model training & hyperparameter tuning
- Feature importance analysis
- Power BI storytelling & visual analytics


## Technologies Used:

- Python
	- pandas
	- seaborn
	- matplotlib
	- numpy
	- statsmodels
	- scikit-learn
	- matplotlib
- Power BI


## How to Reproduce:
PLEASE NOTE: The category columns (`supercategory`, `category`, `subcategory`, and `babycategory`) have known data quality issues which I believe originate in the API collection phase (`rav.py` file). Therefore, they are of limited useability in their current state and are extremely unreliable. If they are important for you use case, you will need to troubleshoot the data quality issues.

Additionally, most of these scripts take several hours to run, and the API collection scripts specifically can take up to 3 days to run. Some of the models are hardcoded with n_jobs = 1, so if you have access to a more powerful machine, make sure to change that.

1. Get access to Ravelry's API by creating a key: https://www.ravelry.com/pro/developer
2. Run the scripts in `/scripts/collection` to collect the pattern and yarn datasets. Expect this to take several days.
3. Run the other scripts in `/scripts` in order from 1-7. Expect each script to take several hours to run, especially the modeling scripts. Scripts 1, 2, and 7 are necessary to generate the final dataset used in Power BI, while the others are for EDA and modeling and can optionally be skipped.
4. Open the PBIX file in `/visualization` and make sure it is connected to the final dataset (`capstone_ravelry.csv`) generated in step 3 (by the file `7_preprocessing_powerbi`).


## Project structure:

* `/documentation`: Project report
* `/scripts`: Python scripts for data collection, processing, EDA, and modeling
* `/visualization`: PBIX file

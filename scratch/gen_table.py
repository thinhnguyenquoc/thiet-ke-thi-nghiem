import pandas as pd
df = pd.read_csv('/Users/nguyenquocthinh/Documents/thiet-ke-thi-nghiem/FINAL_ALL_CITIES_REPORT.csv')
pivot_df = df.pivot(index='City', columns='Model', values='CPC')
cols = ['Attraction-Weighted', 'Attraction-Uniform', 'Power-Pop', 'Power-POI', 'Exp-Pop', 'Exp-POI', 'Radiation-Pop', 'Radiation-POI']
pivot_df = pivot_df[cols]
header = '| City | Att-Weighted | Att-Uniform | Pow-Pop | Pow-POI | Exp-Pop | Exp-POI | Rad-Pop | Rad-POI |'
separator = '| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |'
print(header)
print(separator)
for city, row in pivot_df.iterrows():
    values = []
    for col in cols:
        val = row[col]
        if val == row.max():
            values.append(f'**{val:.4f}**')
        else:
            values.append(f'{val:.4f}')
    print(f'| {city} | ' + ' | '.join(values) + ' |')

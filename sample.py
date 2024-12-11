def main():
    import pandas as pd

    # Load raw data
    file_path = 'pu-data/trip_data_6.csv'
    data = pd.read_csv(file_path)

    # Add id column
    data['id'] = range(data.shape[0])

    # Sample data
    data = data.sample(n=40000)

    # Save as batches   
    batch_size = 2000
    for i in range(0, data.shape[0], batch_size):
        batch = data.iloc[i:i+batch_size]
        batch.to_csv(f'sample-data/trip_data_6_batch_{i+batch_size}.csv', index=False)

if __name__ == "__main__":
    main()


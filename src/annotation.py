import pandas as pd
# Load the cleaned dataset
df = pd.read_csv('CleanDataset.csv')
def annotate_rumor(is_rumor_value, string=True):
    """
    Annotates a rumor based on its 'is_rumor' value.
    - 1.0 (is a rumor) -> 'false'
    - 0.0 (is not a rumor) -> 'true'
    - Other -> 'unverified'
    """
    if is_rumor_value == 1.0:
        if string:
            label = "false"  # It's a rumor, so it's false information
        else:
            label = 0
    elif is_rumor_value == 0.0:
        if string:
            label = "true"  # It's not a rumor, so it's true information
        else:
            label = 1
    else:
        if string:
            label = "unverified" # For any other case
        else:
            label = 2
    return label

# Apply the function to create the new 'annotation' column
df['annotation'] = df['is_rumor'].apply(annotate_rumor)

# Save the annotated dataframe to a new CSV file
df.to_csv('AnnotatedDataset.csv', index=False)

# Display the first few rows of the annotated dataframe
print("Annotation complete. The first 5 rows of the annotated dataset are:")
print(df.head())

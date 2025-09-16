import os
import pandas as pd
# Load the cleaned dataset from datasets folder
DATASETS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'datasets')
INPUT_PATH = os.path.join(DATASETS_DIR, 'CleanDataset.csv')
OUTPUT_PATH = os.path.join(DATASETS_DIR, 'AnnotatedDataset.csv')
df = pd.read_csv(INPUT_PATH)
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

# Save the annotated dataframe to a new CSV file under datasets folder
df.to_csv(OUTPUT_PATH, index=False)

# Display the first few rows of the annotated dataframe
print("Annotation complete. The first 5 rows of the annotated dataset are:")
print(df.head())

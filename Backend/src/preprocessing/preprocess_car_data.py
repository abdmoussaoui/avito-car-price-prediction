import json
import joblib
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

def clean_kilometrage(km_range: str) -> float:
    """Clean kilometrage ranges and convert to numeric."""
    try:
        if "Plus de 500 000" in km_range:
            return 600000
        if "-" in km_range:
            km = [int(k.strip().replace(" ", "")) for k in km_range.split("-")]
            return np.mean(km)
        return int(km_range.strip().replace(" ", ""))
    except:
        return np.nan

# Load configuration from JSON file
def load_config(config_path: str = "config/config.json") -> Dict:
    """Load configuration from a JSON file."""
    try:
        with open(config_path, 'r', encoding='utf-8') as file:
            config = json.load(file)
        # Convert file paths to Path objects
        path_keys = ['data_path', 'output_path', 'mapping_path', 'scaler_path', 'log_path']
        for key in path_keys:
            if key in config:
                config[key] = Path(config[key])
        return config
    except FileNotFoundError:
        logger.error(f"Configuration file {config_path} not found.")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON from {config_path}: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Error loading configuration: {str(e)}")
        raise

CONFIG = load_config()

# Setup logging
logging.basicConfig(
    filename=CONFIG['log_path'],
    filemode='a',
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class DataPreprocessor:
    """Class to handle preprocessing of car dataset."""
    def __init__(self):
        self.scaler = StandardScaler()
        self.df = None

    def load_data(self) -> pd.DataFrame:
        """Load dataset with error handling."""
        try:
            self.df = pd.read_csv(CONFIG['data_path'])
            logger.info(f"Initial dataset shape: {self.df.shape}")
            return self.df
        except FileNotFoundError:
            logger.error(f"File {CONFIG['data_path']} not found.")
            raise
        except Exception as err:
            logger.error(f"Error loading data: {err}")
            raise

    def remove_duplicates(self) -> None:
        """Remove duplicate rows based on key columns."""
        self.df = self.df.drop_duplicates(
            subset=['Marque', 'Modèle', 'Année-Modèle', 'Kilométrage', 'Prix', 'Localisation']
        )
        logger.info(f"Shape after removing duplicates: {self.df.shape}")

    def handle_missing_brands_models(self) -> None:
        """Handle missing Marque and Modèle using title information."""
        brands = {
            brand: self.df[self.df["Marque"] == brand]["Modèle"].dropna().unique().tolist()
            for brand in self.df["Marque"].dropna().unique()
        }

        self.df["Titre"] = self.df["Titre"].str.lower()
        rows_to_delete = []

        for idx, row in self.df.iterrows():
            if pd.notnull(row["Marque"]) and pd.notnull(row["Modèle"]):
                continue
            title_lower = row["Titre"]
            brand_found = False
            for brand, models in brands.items():
                if brand.lower() in title_lower:
                    self.df.at[idx, "Marque"] = brand
                    brand_found = True
                    for model in models:
                        if isinstance(model, str) and model.lower() in title_lower:
                            self.df.at[idx, "Modèle"] = model
                            break
                    break
            if not brand_found:
                rows_to_delete.append(idx)
        if rows_to_delete:
            self.df = self.df.drop(index=rows_to_delete)
        logger.info(f"Shape after handling Marque and Modèle: {self.df.shape}")

    def handle_price(self) -> None:
        """Process price column (conversion and missing values only)."""
        self.df["Prix"] = self.df["Prix"].astype(str).str.replace("DH", "").str.replace(r"[\s\u202f]", "", regex=True)
        self.df["Prix"] = pd.to_numeric(self.df["Prix"], errors="coerce")
        self.df['Prix'] = self.df.groupby(['Marque', 'Modèle'])['Prix'].transform(
            lambda x: x.fillna(x.median()) if not x.isna().all() else np.nan
        )
        self.df = self.df.dropna(subset=["Prix"])
        logger.info(f"Shape after handling Prix: {self.df.shape}")

    def clip_and_transform_price(self) -> None:
        """Clip price outliers based on Marque_group and apply log transformation."""
        bounds_by_group = {}
        for group in self.df['Marque_group'].unique():
            group_data = self.df[self.df['Marque_group'] == group]['Prix']
            group_marque = self.df[self.df["Marque_group"] == group]["Group_marque"].iloc[0]
            lower_percentile = 0.10 if group_marque in ['Luxe', 'Premium'] else 0.05
            lower_bound = max(group_data.quantile(lower_percentile),
                              150000 if group_marque == 'Luxe' else
                              50000 if group_marque == 'Premium' else 20000)
            upper_bound = group_data.quantile(0.95)
            bounds_by_group[group] = {'Lower_Bound (DH)': lower_bound, 'Upper_Bound (DH)': upper_bound}
            self.df.loc[self.df['Marque_group'] == group, 'Prix'] = self.df.loc[
                self.df['Marque_group'] == group, 'Prix'].clip(lower=lower_bound, upper=upper_bound)
        self.df["Prix"] = self.df["Prix"].apply(lambda x: np.log(x + 1))
        logger.info("Price outliers clipped and log transformation applied")

    def handle_horsepower(self) -> None:
        """Process fiscal horsepower and clip outliers."""
        self.df["Puissance fiscale"] = self.df["Puissance fiscale"].astype(str).str.replace(
            "Plus de 41 CV", "41 CV").str.replace("CV", "").str.replace(r"\s+", "", regex=True)
        self.df["Puissance fiscale"] = pd.to_numeric(self.df["Puissance fiscale"], errors="coerce")
        self.df['Puissance fiscale'] = self.df.groupby(['Marque', 'Modèle'])['Puissance fiscale'].transform(
            lambda x: x.fillna(x.median()) if not x.isna().all() else np.nan
        )
        self.df = self.df.dropna(subset=["Puissance fiscale"])
        self.df["Puissance fiscale"] = self.df["Puissance fiscale"].astype(int)
        self.df['Puissance fiscale'] = self.df['Puissance fiscale'].clip(lower=1, upper=41)
        logger.info(f"Shape after handling Puissance fiscale: {self.df.shape}")

    def handle_condition(self) -> None:
        """Encode vehicle condition."""
        self.df['État'] = self.df['État'].replace('null', np.nan).map(CONFIG['status_mapping'])
        self.df['État'] = self.df.groupby(['Marque', 'Modèle'])['État'].transform(
            lambda x: x.fillna(x.mode().iloc[0] if not x.mode().empty else 4)
        )
        logger.info(f"Shape after handling État: {self.df.shape}")

    def handle_equipments(self) -> None:
        """Process equipment features and create scores."""
        self.df['Équipements'] = self.df['Équipements'].fillna('')
        all_equipments = set()
        for equip in self.df['Équipements']:
            if equip:
                for item in equip.split(','):
                    all_equipments.add(item.strip())

        for equip in all_equipments:
            self.df[f'Has_{equip.replace(" ", "_")}'] = self.df['Équipements'].apply(
                lambda x: 1 if equip in x else 0)

        self.df['Safety_Score'] = self.df[[
            f'Has_{feat.replace(" ", "_")}' for feat in CONFIG['safety_features']
            if f'Has_{feat.replace(" ", "_")}' in self.df.columns
        ]].sum(axis=1)

        self.df['Comfort_Score'] = self.df[[
            f'Has_{feat.replace(" ", "_")}' for feat in CONFIG['comfort_features']
            if f'Has_{feat.replace(" ", "_")}' in self.df.columns
        ]].sum(axis=1)

        self.df['Tech_Score'] = self.df[[
            f'Has_{feat.replace(" ", "_")}' for feat in CONFIG['tech_features']
            if f'Has_{feat.replace(" ", "_")}' in self.df.columns
        ]].sum(axis=1)

        equip_columns = [col for col in self.df.columns if col.startswith('Has_')]
        self.df = self.df.drop(columns=equip_columns)
        logger.info(f"Shape after handling Équipements: {self.df.shape}")

    def group_brands(self) -> None:
        """Group brands using K-means clustering based on features."""
        brand_features = self.df.groupby('Marque').agg({
            'Prix': 'mean',
            'Safety_Score': 'mean',
            'Comfort_Score': 'mean',
            'Tech_Score': 'mean',
            'Puissance fiscale': 'mean',
            'État': 'mean'
        }).reset_index()

        scaler = StandardScaler()
        brand_features_scaled = scaler.fit_transform(brand_features.drop(columns=['Marque']))

        kmeans = KMeans(n_clusters=3, random_state=42)
        brand_features['Cluster'] = kmeans.fit_predict(brand_features_scaled)

        cluster_prices = brand_features.groupby('Cluster')['Prix'].mean().sort_values()
        cluster_mapping = {
            cluster_prices.index[0]: 'Économique',
            cluster_prices.index[1]: 'Premium',
            cluster_prices.index[2]: 'Luxe'
        }
        brand_features['Group_marque'] = brand_features['Cluster'].map(cluster_mapping)

        for cluster in cluster_mapping:
            cluster_brands = brand_features[brand_features['Group_marque'] == cluster_mapping[cluster]]
            top_brands = cluster_brands.sort_values(by='Prix', ascending=False).head(5)
            logger.info(f"Top 5 brands in {cluster_mapping[cluster]} cluster by price:")
            for _, row in top_brands.iterrows():
                logger.info(f"  {row['Marque']}: {row['Prix']:.2f} DH")

        brand_to_group = dict(zip(brand_features['Marque'], brand_features['Group_marque']))
        self.df['Group_marque'] = self.df['Marque'].map(brand_to_group)

        brand_counts = self.df['Marque'].value_counts()
        self.df['Marque_group'] = self.df['Marque'].apply(
            lambda x: f"Autres marques {brand_to_group[x].lower()}" if brand_counts[x] < 10 else x
        )
        self.clip_and_transform_price()

        brand_classification = self.df.groupby('Marque')['Group_marque'].first()
        for brand, group in brand_classification.items():
            logger.info(f"Brand: {brand}, Classified as: {group}")

    def handle_location(self) -> None:
        """Standardize location names."""
        self.df['Localisation'] = self.df['Localisation'].apply(
            lambda city: city.split(',')[1].strip() if pd.notna(city) and ',' in city else city
        )
        self.df['Localisation'] = self.df['Localisation'].replace(CONFIG['cities_mapping'])

    def handle_categorical(self, columns: List[str]) -> None:
        """Handle missing values in categorical columns."""
        for col in columns:
            self.df[col] = self.df.groupby(['Marque', 'Modèle'])[col].transform(
                lambda x: x.fillna(x.mode().iloc[0] if not x.mode().empty else self.df[col].mode().iloc[0])
            )
        self.df = self.df.dropna(subset=columns)
        logger.info(f"Shape after handling {columns}: {self.df.shape}")

    def handle_kilometrage(self) -> None:
        """Process kilometrage ranges and clip outliers."""
        self.df["Kilométrage"] = self.df["Kilométrage"].astype(str).apply(clean_kilometrage)
        self.df['Kilométrage'] = self.df.groupby(['Marque', 'Modèle'])['Kilométrage'].transform(
            lambda x: x.fillna(x.median()) if not x.isna().all() else np.nan
        )
        self.df = self.df.dropna(subset=["Kilométrage"])
        self.df['Kilométrage'] = self.df['Kilométrage'].clip(lower=1000, upper=600000)
        logger.info(f"Shape after handling Kilométrage: {self.df.shape}")

    def handle_year(self) -> None:
        """Process model year and clip outliers."""
        self.df["Année-Modèle"] = self.df["Année-Modèle"].astype(str).str.replace("1980 ou plus ancien", "1980")
        self.df["Année-Modèle"] = pd.to_numeric(self.df["Année-Modèle"], errors="coerce")
        self.df['Année-Modèle'] = self.df.groupby(['Marque', 'Modèle'])['Année-Modèle'].transform(
            lambda x: x.fillna(x.median()) if not x.isna().all() else np.nan
        )
        self.df = self.df.dropna(subset=["Année-Modèle"])
        self.df["Année-Modèle"] = self.df["Année-Modèle"].astype(int)
        self.df['Année-Modèle'] = self.df['Année-Modèle'].clip(lower=1980, upper=2025)
        logger.info(f"Shape after handling Année-Modèle: {self.df.shape}")

    def handle_doors(self) -> None:
        """Process number of doors."""
        self.df["Nombre de portes"] = pd.to_numeric(self.df["Nombre de portes"], errors="coerce")
        self.df['Nombre de portes'] = self.df.groupby(['Marque', 'Modèle'])['Nombre de portes'].transform(
            lambda x: x.fillna(x.median()) if not x.isna().all() else np.nan
        )
        self.df = self.df.dropna(subset=["Nombre de portes"])
        self.df["Nombre de portes"] = self.df["Nombre de portes"].astype('Int64')
        logger.info(f"Shape after handling Nombre de portes: {self.df.shape}")

    def handle_first_owner(self) -> None:
        """Encode first owner status."""
        self.df['Première main'] = self.df['Première main'].map({'Oui': 1, 'Non': 0, 'null': np.nan})
        self.df['Première main'] = self.df.groupby(['Marque', 'Modèle'])['Première main'].transform(
            lambda x: x.fillna(x.mode().iloc[0] if not x.mode().empty else 1)
        )
        logger.info(f"Shape after handling Première main: {self.df.shape}")

    def target_encoding(self) -> None:
        """Perform smoothed target encoding for categorical variables."""
        group_means = self.df.groupby(['Localisation', 'Marque', 'Modèle'])['Prix'].agg(['mean', 'count']).reset_index()
        global_mean = self.df['Prix'].mean()
        smoothing_factor = 5
        group_means['mean'] = group_means.apply(
            lambda x: (x['count'] * x['mean'] + smoothing_factor * global_mean) / (x['count'] + smoothing_factor),
            axis=1
        )

        self.df = self.df.merge(group_means[['Localisation', 'Marque', 'Modèle', 'mean']],
                                on=['Localisation', 'Marque', 'Modèle'], how='left')
        self.df['Loc_Marque_Modèle_encoded'] = self.df['mean']
        self.df = self.df.drop(columns=['mean'])

        # Standardize numerical features
        numerical_cols = ['Kilométrage', 'Année-Modèle', 'Puissance fiscale', 'Nombre de portes',
                          'État', 'Première main', 'Safety_Score', 'Comfort_Score', 'Tech_Score',
                          'Loc_Marque_Modèle_encoded']
        self.df[numerical_cols] = self.scaler.fit_transform(self.df[numerical_cols])

        # Use a separate scaler for group_means['mean']
        encoding_scaler = StandardScaler()
        encoding_scaler.fit(self.df[['Loc_Marque_Modèle_encoded']])
        group_means['mean'] = encoding_scaler.transform(
            group_means[['mean']].rename(columns={'mean': 'Loc_Marque_Modèle_encoded'})
        )[:, 0]
        group_means.to_csv(CONFIG['mapping_path'], index=False)

        # Ensure the directory exists before saving the scaler
        Path(CONFIG['scaler_path']).parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.scaler, CONFIG['scaler_path'])
        logger.info("Scaler saved for prediction")
        logger.info("Completed smoothed and standardized target encoding")

    def one_hot_encoding(self) -> None:
        """Perform one-hot encoding for low-cardinality columns."""
        low_cardinality_cols = ["Boite de vitesses", "Type de carburant"]
        for column in low_cardinality_cols:
            encoded_cols = pd.get_dummies(self.df[column], prefix=column, dtype=int)
            self.df = pd.concat([self.df, encoded_cols], axis=1)

    def drop_columns(self) -> None:
        """Drop unnecessary columns."""
        columns_to_drop = ["Titre", "Date_publication", "Équipements", "Origine", "Marque",
                           "Modèle", "Localisation", "Marque_group", "Group_marque",
                           "Boite de vitesses", "Type de carburant"]
        self.df = self.df.drop(columns=columns_to_drop, errors='ignore')

    def final_check(self) -> None:
        """Final check for missing values."""
        self.df = self.df.dropna()
        logger.info(f"Shape after dropping any remaining NaN values: {self.df.shape}")

    def save_data(self) -> None:
        """Save the processed dataset."""
        logger.info(f"Writing {len(self.df)} rows and {len(self.df.columns)} columns to CSV...")
        Path(CONFIG['output_path']).parent.mkdir(parents=True, exist_ok=True)
        self.df.to_csv(CONFIG['output_path'], index=False, encoding="utf-8")
        logger.info(f"Final dataset shape: {self.df.shape}")

    def preprocess(self) -> pd.DataFrame:
        """Execute complete preprocessing pipeline."""
        self.load_data()
        self.remove_duplicates()
        self.handle_missing_brands_models()
        self.handle_price()
        self.handle_horsepower()
        self.handle_condition()
        self.handle_equipments()
        self.group_brands()
        self.handle_location()
        self.handle_categorical(["Boite de vitesses", "Type de carburant"])
        self.handle_kilometrage()
        self.handle_year()
        self.handle_doors()
        self.handle_first_owner()
        self.target_encoding()
        self.one_hot_encoding()
        self.drop_columns()
        self.final_check()
        self.save_data()
        return self.df

def main():
    """Main function to run preprocessing."""
    try:
        preprocessor = DataPreprocessor()
        processed_df = preprocessor.preprocess()
        logger.info("Preprocessing completed successfully")
        return processed_df
    except Exception as err:
        logger.error(f"Preprocessing failed: {str(err)}")
        raise

if __name__ == "__main__":
    main()
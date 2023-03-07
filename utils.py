#---------------------------------------------------------------------------------------------------#
# File name: utils.py                                                                               #
# Autor: Chrissi2802                                                                                #
# Created on: 13.01.2023                                                                            #
# Content: This file provides the datasets, prepares the data and                                   #
#          provides functions for machine learning tasks on the Hut-statistics dataset.             #
#---------------------------------------------------------------------------------------------------#


import pandas as pd
import numpy as np
import warnings
    
warnings.filterwarnings("ignore")


class Hut_Dataset:
    """This class provides the datasets and prepares the data of the Hut-statistics dataset.
    """

    def __init__(self, path, encoded = True):
        """This method initializes the class. 
           It loads the dataset and the indices and creates additional dataframes.
        
        Args:
            path (string): Path where the dataset and the indices are saved
            encoded (bool, optional): If the dataset is encoded or not. Defaults to True.
        """

        self.path = path
        self.path_indices = self.path + "Indizes.xlsx"

        # choose the right dataset
        if encoded == True:
            self.path_data = self.path + "BV_encoded.xlsx"
        else:
            self.path_data = self.path + "BV.xlsx"

        self.__load_dataset()
        self.__load_indices()
        self.__create_additional_dfs()

    def __load_dataset(self):
        """This mehtod loads the dataset und rounds the float values to 2 decimal digits.
        """

        # read excel file
        self.df_getränke = pd.read_excel(self.path_data, sheet_name = "Getränke")
        self.df_bier = pd.read_excel(self.path_data, sheet_name = "Top_Bier")
        self.df_schnaps = pd.read_excel(self.path_data, sheet_name = "Top_Schnaps")

        # round columns with float values to 2 decimal digits
        self.df_getränke = self.df_getränke.round(2)
        self.df_bier = self.df_bier.round(2)
        self.df_schnaps = self.df_schnaps.round(2)

    def __load_indices(self):
        """This method loads the indices.
        """

        # read excel file
        self.df_indices = pd.read_excel(self.path_indices)

    def __create_additional_dfs(self):
        """This method creates additional dataframes.
        """

        # Subdivide drinks
        # store df_drinks "Spezi, Fanta etc." (non-alcoholic) in own df
        self.df_getränke_alkrei = self.df_getränke[self.df_getränke["Biersorte"] == "Spezi, Fanta usw."]

        # Store only beer without non-alcoholic in own df
        self.df_getränke_ohne_alkfrei = self.df_getränke[self.df_getränke["Biersorte"] != "Spezi, Fanta usw."]

        # Summarize data in a data frame, data in liters
        self.df_kombiniert = pd.DataFrame({"Bier gesamt": self.df_getränke_ohne_alkfrei.groupby("Jahr").sum()["Kisten"].apply(lambda x: x * 20 * 0.5),
                            "Alkfrei gesamt": self.df_getränke_alkrei.groupby("Jahr").sum()["Kisten"].apply(lambda x: x * 20 * 0.5),
                            "Bier Top 10": self.df_bier.groupby("Jahr").sum()["Anzahl Bier"].apply(lambda x: x * 0.5),
                            "Alkfrei Top 10": self.df_bier.groupby("Jahr").sum()["Anzahl Alkfrei"].apply(lambda x: x * 0.5),
                            "Schnäpse Top 10": self.df_schnaps.groupby("Jahr").sum()["Schnäpse"].apply(lambda x: x * 0.2)})

        # Merge df_kombiniert with df_indices
        self.df_kombiniert_indizes = pd.merge(self.df_kombiniert, self.df_indices, on = "Jahr", how = "left")

        # Rename columns
        self.df_kombiniert_indizes.rename(columns = {"Bruttoinlandsprodukt (BIP) in Deutschland (in Milliarden Euro)": "BIP", 
                                                "Verbraucherpreisindex in Deutschland": "VPI"}, inplace = True)
        self.df_kombiniert_indizes.set_index("Jahr", inplace = True) # set index to year

    def get_dfs(self):
        """This method returns the dataframes.

        Returns:
            df_getränke (pandas DataFrame): Dataframe with all drinks
            df_bier (pandas DataFrame): Dataframe with the top 10 beer drinkers
            df_schnaps (pandas DataFrame): Dataframe with the top 10 schnaps drinkers
            df_getränke_alkrei (pandas DataFrame): Dataframe with all non-alcoholic drinks
            df_getränke_ohne_alkfrei (pandas DataFrame): Dataframe with all alcoholic drinks
            df_kombiniert (pandas DataFrame): Dataframe with summarized data
            df_kombiniert_indizes (pandas DataFrame): Dataframe with summarized data and indices
        """

        return self.df_getränke, self.df_bier, self.df_schnaps, self.df_getränke_alkrei, \
            self.df_getränke_ohne_alkfrei, self.df_kombiniert, self.df_kombiniert_indizes


def encode(path_dataset):
    """This function encodes the names in the dataset and saves the encoded names in a new excel file. 
       This way the names can be anonymized.

    Args:
        path_dataset (string): Path where the dataset is saved
    """
    
    CHut_Dataset = Hut_Dataset(path_dataset)

    # get dataframes
    df_getränke, df_bier, df_schnaps, _, _, _, _ = CHut_Dataset.get_dfs()

    # create a df with all unique names from df_bier and df_schnaps
    df_names = pd.DataFrame({"Name": df_bier["Name"].unique()})
    df_names = df_names.append(pd.DataFrame({"Name": df_schnaps["Name"].unique()}), ignore_index = True)
    df_names = df_names.drop_duplicates().reset_index(drop = True)

    # save df_names in excel file
    df_names.to_excel(path_dataset + "Names_encoding.xlsx", index = True)

    # df to dictionary for encoding
    dict_names = df_names["Name"].to_dict()
    dict_names_inv = {v: k for k, v in dict_names.items()}

    # use dictionary to decode the names
    df_bier["Name"] = df_bier["Name"].map(dict_names_inv)
    df_schnaps["Name"] = df_schnaps["Name"].map(dict_names_inv)

    # Save encoded data in excel in different spreadsheets
    with pd.ExcelWriter(path_dataset + "BV_encoded.xlsx") as writer:
        df_getränke.to_excel(writer, sheet_name = "Getränke", index = False)
        df_bier.to_excel(writer, sheet_name = "Top_Bier", index = False)
        df_schnaps.to_excel(writer, sheet_name = "Top_Schnaps", index = False)


def train_predict(model, df, column, next_year):
    """This function trains a model and predicts the next year.

    Args:
        model (sklearn model): Model to train
        df (pandas DataFrame): DataFrame with data and labels
        column (string): Column name of the data
        next_year (integer): Year to predict

    Returns:
        prediction (numpy array): Prediction of the next year
        line (numpy array): Linear line of the model
    """

    # 1D array to 2D array
    x = df.index.values.reshape(-1, 1)
    y = df[column].values.reshape(-1, 1)

    # Scale data
    #scaler = StandardScaler()
    #x = scaler.fit_transform(x)
    #y = scaler.transform(y)

    # Train model
    model.fit(x, y)

    # Predict
    prediction = model.predict([[next_year]])
    line = model.predict(np.append(x, [[next_year]]).reshape(-1, 1))

    return prediction, line


if __name__ == "__main__":
    
    path_dataset = "./Dataset/"
    CHut_Dataset = Hut_Dataset(path_dataset)

    # get dataframes
    df_getränke, df_bier, df_schnaps, df_getränke_alkrei, df_getränke_ohne_alkfrei, \
        df_kombiniert, df_kombiniert_indizes = CHut_Dataset.get_dfs()

    # print shape of all dataframes
    print(df_getränke.shape, df_bier.shape, df_schnaps.shape, df_getränke_alkrei.shape, 
          df_getränke_ohne_alkfrei.shape, df_kombiniert.shape, df_kombiniert_indizes.shape) 

    #encode(path_dataset)
    
# -*- coding: utf-8 -*-
import logging
from pathlib import Path
import argparse
import zipfile
import shutil
import pickle
import os
import pandas as pd
from multiprocessing import Pool


def set_directories(args):

    if args.proj_dir:
        proj_dir = Path(args.proj_dir)
    else:
        proj_dir = Path().cwd()

    if args.path_data_dir:
        path_data_dir = Path(args.path_data_dir)
    else:
        path_data_dir = proj_dir / "data"

    path_splits_dir = path_data_dir / "raw" / "cnc" / args.split_dir_name
    path_processed_raw_dir = path_data_dir / "raw" / "cnc" / args.save_dir_name
    path_processed_raw_dir.mkdir(parents=True, exist_ok=True)


    return proj_dir, path_data_dir, path_splits_dir, path_processed_raw_dir


def read_pickle(filename):
    'converts a filename to a pandas dataframe'

    col_selection = ["tool_no", "current_main", "current_sub"]

    df = pickle.load(open(filename, 'rb'))
    id = filename.stem
    df["id"] = id
    df['timestamp'] = id.split("_")[0]
    df['index_no'] = id.split("_")[-1]
    
    return df[["id", "timestamp", "index_no"] + col_selection]

def main(args):
    """Runs data processing scripts to turn raw data from (../raw) into
    cleaned data ready to be analyzed (saved in ../processed).
    """
    logger = logging.getLogger(__name__)
    logger.info("making final data set from raw data")

    proj_dir, path_data_dir, path_splits_dir, path_processed_raw_dir = set_directories(args)

    # get a list of file names
    files = os.listdir(path_splits_dir)
    file_list = [
        Path(path_splits_dir) / filename
        for filename in files
        if filename.endswith(".pickle")
    ]

    # set up your pool
    with Pool(processes=args.n_cores) as pool:  # or whatever your hardware can support

        # have your pool map the file names to dataframes
        df_list = pool.map(read_pickle, file_list)

        # reduce the list of dataframes to a single dataframe
        combined_df = pd.concat(df_list, ignore_index=True)

        return combined_df



if __name__ == "__main__":
    log_fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logging.basicConfig(level=logging.INFO, format=log_fmt)


    parser = argparse.ArgumentParser(description="Create dataframe from raw data")

    parser.add_argument(
        "-p",
        "--proj_dir",
        dest="proj_dir",
        type=str,
        help="Location of project folder",
    )

    parser.add_argument(
        "--path_data_dir",
        type=str,
        default="data/",
        help="Path to data folder that contains raw/interim/processed data folders",
    )

    parser.add_argument(
        "--save_dir_name",
        type=str,
        default="data_raw_processed",
        help="Name of the subfolder that will contain the final raw csv file",
    )

    parser.add_argument(
        "--split_dir_name",
        type=str,
        default="data_splits",
        help="Folder name containing all individual split pickle files.",
    )

    parser.add_argument(
        "--n_cores",
        type=int,
        default=2,
        help="Number of processes to use for multiprocessing",
    )


    args = parser.parse_args()

    proj_dir, path_data_dir, path_splits_dir, path_processed_raw_dir = set_directories(args)

    df = main(args)

    print("Shape of final df:", df.shape)

    # save the dataframe
    print("Saving dataframe...")
    df.to_csv(
        path_processed_raw_dir / "cnc_raw.csv.gz",
        compression="gzip",
        index=False,
    )

    shutil.copy(
        Path(proj_dir) / "src/dataprep/make_dataset_cnc.py",
        path_processed_raw_dir / "make_dataset_cnc.py",)

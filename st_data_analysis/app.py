import pandas as pd
import streamlit as st

from st_data_analysis.data_analysis import (
    compute_presence_in_text,
    document_explorer,
    draw_sidebar,
    plot_attribute_presence,
    plot_autoclass_influence,
    plot_doc_attr_counts,
    plot_input_channel_influence,
    plot_non_nan_ratio,
    plot_non_nan_ratio_by_doc_type,
)


@st.cache_data
def load_data(pickle_filename: str) -> pd.DataFrame:
    return pd.read_pickle(pickle_filename)


def run_dashboard():
    st.title("Document Analysis Dashboard")
    df = load_data("dummy_dataframe.pkl")
    numeric_cols = ["Number1", "Number2", "Number3"]

    # Sidebar filters
    filtered_df = draw_sidebar(df)

    # Compute presence columns
    filtered_df = compute_presence_in_text(filtered_df, numeric_cols)

    # Plots
    plot_doc_attr_counts(filtered_df, numeric_cols)
    plot_non_nan_ratio(filtered_df, numeric_cols)
    plot_non_nan_ratio_by_doc_type(filtered_df, numeric_cols)
    plot_input_channel_influence(filtered_df, numeric_cols)
    plot_attribute_presence(filtered_df, numeric_cols)
    plot_autoclass_influence(filtered_df, numeric_cols)

    # Document Explorer
    document_explorer(filtered_df, numeric_cols)


if __name__ == "__main__":
    run_dashboard()

import pandas as pd
import plotly.express as px
import streamlit as st


def draw_sidebar(df: pd.DataFrame):
    st.sidebar.title("Filters")
    doc_types = df["DocumentType"].unique()
    input_channels = df["InputChannel"].unique()
    autoclasses = df["Autoclass"].unique()

    selected_doc_types = st.sidebar.multiselect("Document Type", options=["All"] + list(doc_types), default=["All"])
    selected_input_channels = st.sidebar.multiselect(
        "Input Channel", options=["All"] + list(input_channels), default=["All"]
    )
    selected_autoclass = st.sidebar.multiselect("Autoclass", options=["All"] + list(autoclasses), default=["All"])

    filtered_df = df.copy()
    if "All" not in selected_doc_types:
        filtered_df = filtered_df.loc[filtered_df["DocumentType"].isin(selected_doc_types)]
    if "All" not in selected_input_channels:
        filtered_df = filtered_df.loc[filtered_df["InputChannel"].isin(selected_input_channels)]
    if "All" not in selected_autoclass:
        filtered_df = filtered_df.loc[filtered_df["Autoclass"].isin(selected_autoclass)]
    return filtered_df


def compute_presence_in_text(df: pd.DataFrame, numeric_cols):
    df = df.copy()
    for col in numeric_cols:
        presence_col = f"{col}_in_text"
        df.loc[:, presence_col] = df.apply(
            lambda row: str(row[col]) in str(row["clean_text"]) if row[col] else False, axis=1
        )
    return df


def plot_doc_attr_counts(df: pd.DataFrame, numeric_cols):
    doc_attr_counts = df.groupby("DocumentType")[numeric_cols].count().reset_index()
    fig = px.bar(
        doc_attr_counts.melt(id_vars="DocumentType", var_name="Attribute", value_name="Count"),
        x="DocumentType",
        y="Count",
        color="Attribute",
        barmode="group",
        title="Attribute Counts by DocumentType",
    )
    st.plotly_chart(fig)


def plot_non_nan_ratio(df: pd.DataFrame, numeric_cols):
    non_nan_ratio = df[numeric_cols].notna().mean().reset_index()
    non_nan_ratio.columns = ["Attribute", "Non-NaN Ratio"]
    fig = px.bar(non_nan_ratio, x="Attribute", y="Non-NaN Ratio", title="Overall Non-NaN Ratio per Attribute")
    st.plotly_chart(fig)


def plot_non_nan_ratio_by_doc_type(df: pd.DataFrame, numeric_cols):
    ratio_by_doc = df.groupby("DocumentType")[numeric_cols].apply(lambda x: x.notna().mean()).reset_index()
    ratio_melted = ratio_by_doc.melt(id_vars="DocumentType", var_name="Attribute", value_name="Ratio")
    fig = px.bar(
        ratio_melted,
        x="DocumentType",
        y="Ratio",
        color="Attribute",
        barmode="group",
        title="Non-NaN Ratio by DocumentType",
    )
    st.plotly_chart(fig)


def plot_input_channel_influence(df: pd.DataFrame, numeric_cols):
    input_attr_counts = df.groupby("InputChannel")[numeric_cols].count().reset_index()
    fig1 = px.bar(
        input_attr_counts.melt(id_vars="InputChannel", var_name="Attribute", value_name="Count"),
        x="InputChannel",
        y="Count",
        color="Attribute",
        barmode="group",
        title="Attribute Counts by InputChannel",
    )
    st.plotly_chart(fig1)

    doc_type_by_input = df.groupby(["InputChannel", "DocumentType"]).size().reset_index(name="Count")
    fig2 = px.bar(
        doc_type_by_input,
        x="InputChannel",
        y="Count",
        color="DocumentType",
        barmode="group",
        title="DocumentType Distribution by InputChannel",
    )
    st.plotly_chart(fig2)


def plot_attribute_presence(df: pd.DataFrame, numeric_cols):
    presence_cols = [f"{col}_in_text" for col in numeric_cols]
    presence_summary = df[[*numeric_cols, *presence_cols, "DocumentType", "InputChannel"]].melt(
        id_vars=["DocumentType", "InputChannel"], value_name="Value", var_name="Attribute_or_Presence"
    )
    presence_df = presence_summary[presence_summary["Attribute_or_Presence"].str.endswith("_in_text")].copy()
    presence_df["Attribute"] = presence_df["Attribute_or_Presence"].str.replace("_in_text", "")

    presence_rate = presence_df.groupby(["Attribute", "DocumentType", "InputChannel"])["Value"].mean().reset_index()
    fig = px.bar(
        presence_rate,
        x="Attribute",
        y="Value",
        color="DocumentType",
        facet_col="InputChannel",
        title="Attribute Presence in Clean Text by DocType and InputChannel",
    )
    st.plotly_chart(fig)


def plot_autoclass_influence(df: pd.DataFrame, numeric_cols):
    autoclass_df = df.groupby(["Autoclass", "DocumentType"])[numeric_cols].count().reset_index()
    fig = px.bar(
        autoclass_df.melt(id_vars=["Autoclass", "DocumentType"], var_name="Attribute", value_name="Count"),
        x="Autoclass",
        y="Count",
        color="DocumentType",
        barmode="group",
        facet_col="Attribute",
        title="Autoclass Influence on Attributes",
    )
    st.plotly_chart(fig)


def document_explorer(df: pd.DataFrame, numeric_cols):
    st.subheader("Document Explorer")
    doc_ids = df["Document_ID"].unique()
    selected_id = st.selectbox("Select a Document ID to inspect", options=doc_ids)

    if selected_id:
        row = df.loc[df["Document_ID"] == selected_id].iloc[0]

        # CHANGED: highlight any numeric attributes found in the text
        text = row["clean_text"]
        for col in numeric_cols:
            value = str(row[col]) if row[col] else None
            if value and value in text:
                text = text.replace(value, f"<span style='background-color: yellow;'>{value}</span>")

        # CHANGED: use markdown with unsafe_allow_html to render highlights
        st.markdown(f"**Document Text (ID {selected_id}):**", unsafe_allow_html=True)
        st.markdown(text, unsafe_allow_html=True)

        st.write("**Attribute Presence:**")
        for col in numeric_cols:
            value = row[col]
            if value is not None:
                found_in_text = row[f"{col}_in_text"]
                msg = f"{col} = {value} (Found in text: {found_in_text})"
                st.write(msg)

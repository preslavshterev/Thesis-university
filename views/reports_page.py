from datetime import date

import streamlit as st

from data_access import load_stores
from filters import describe_filters, get_filtered_sales
from reports import build_report_tables, sales_lines, to_csv_bytes, to_excel_bytes
from ui import card, page_header, stop_if_empty

EXCEL_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

page_header(
    "Reports",
    "Downloads follow the current sidebar filters. Customer personal data is not included.",
)

try:
    completed = get_filtered_sales()
    stores = load_stores()
except FileNotFoundError as error:
    st.error(
        f"A required data file is missing ({error}). "
        "Run etl_pipeline.py and export_tables.py first."
    )
    st.stop()

stop_if_empty(completed)

tables = build_report_tables(completed, stores, describe_filters())
today = date.today().isoformat()

with card("Excel report"):
    st.subheader("Excel report")
    st.write("One workbook with the summary, monthly revenue, categories, stores, top products and the filters used.")
    st.download_button(
        "Download Excel report",
        data=to_excel_bytes(tables),
        file_name=f"sales_report_{today}.xlsx",
        mime=EXCEL_MIME,
        type="primary",
    )

csv_exports = {
    "Sales lines": sales_lines(completed),
    "Monthly revenue": tables["Monthly revenue"],
    "Revenue by category": tables["By category"],
    "Revenue by store": tables["By store"],
}

with card("CSV exports"):
    st.subheader("CSV exports")
    columns = st.columns(len(csv_exports))
    for column, (name, table) in zip(columns, csv_exports.items()):
        column.download_button(
            f"{name} (CSV)",
            data=to_csv_bytes(table),
            file_name=f"{name.lower().replace(' ', '_')}_{today}.csv",
            mime="text/csv",
            key=f"csv_{name}",
        )

left, right = st.columns(2)
with left:
    with card("Report summary"):
        st.subheader("Report summary")
        st.dataframe(tables["Summary"], hide_index=True)
with right:
    with card("Filters used"):
        st.subheader("Filters used")
        st.dataframe(tables["Filters"], hide_index=True)
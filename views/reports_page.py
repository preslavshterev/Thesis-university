from datetime import date

import streamlit as st

from data_access import load_stores
from filters import describe_filters, get_filtered_sales
from reports import build_report_tables, sales_lines, to_csv_bytes, to_excel_bytes

EXCEL_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

st.title("Reports")
st.caption("Reports use the current sidebar filters. Customer personal data is not included.")

try:
    completed = get_filtered_sales()
    stores = load_stores()
except FileNotFoundError as error:
    st.error(
        f"A required data file is missing ({error}). "
        "Run etl_pipeline.py and export_tables.py first."
    )
    st.stop()

if completed.empty:
    st.warning("No sales match the selected filters.")
    st.stop()

tables = build_report_tables(completed, stores, describe_filters())
today = date.today().isoformat()

st.subheader("Excel report")
st.write("One workbook with the summary, monthly revenue, categories, stores, top products and the filters used.")
st.download_button(
    "Download Excel report",
    data=to_excel_bytes(tables),
    file_name=f"sales_report_{today}.xlsx",
    mime=EXCEL_MIME,
)

st.subheader("CSV exports")
csv_exports = {
    "Sales lines": sales_lines(completed),
    "Monthly revenue": tables["Monthly revenue"],
    "Revenue by category": tables["By category"],
    "Revenue by store": tables["By store"],
}
columns = st.columns(len(csv_exports))
for column, (name, table) in zip(columns, csv_exports.items()):
    column.download_button(
        f"{name} (CSV)",
        data=to_csv_bytes(table),
        file_name=f"{name.lower().replace(' ', '_')}_{today}.csv",
        mime="text/csv",
        key=f"csv_{name}",
    )

st.subheader("Report summary")
left, right = st.columns(2)
left.dataframe(tables["Summary"], hide_index=True)
right.dataframe(tables["Filters"], hide_index=True)
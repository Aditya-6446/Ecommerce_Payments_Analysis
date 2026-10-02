"""Interactive exploration of the project's documented payment-service listings."""

from html import escape
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from src.payments import ROOT, filter_listings, prepare_data, service_coverage

BLUE = "#315CDE"
INK = "#17233C"
MUTED = "#738098"


@st.cache_data
def load_data(source_modified: float):
    return prepare_data()


def style_chart(fig, height=390):
    fig.update_layout(
        height=height, margin=dict(l=0, r=18, t=12, b=0),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Arial", size=12, color=INK),
        hoverlabel=dict(bgcolor="white", font_color=INK),
        xaxis=dict(gridcolor="#E5E9F1", zeroline=False),
        yaxis=dict(gridcolor="#E5E9F1", zeroline=False),
    )
    return fig


def reset_filters():
    for key in ["countries", "services", "roles"]:
        st.session_state[key] = []
    st.session_state["search"] = ""


def overview(data, filtered):
    if filtered.empty:
        st.info("No listings match these filters. Clear a filter or reset the selection.")
        return
    coverage = service_coverage(filtered)
    left, right = st.columns([1.05, 1], gap="large")
    with left:
        st.subheader("Most-listed services")
        st.caption("Distinct markets where each service appears in the selected dataset records.")
        top = coverage.head(12).sort_values(["markets_listed", "service"], ascending=[True, False])
        fig = px.bar(top, x="markets_listed", y="service", orientation="h", text="markets_listed",
                     color_discrete_sequence=[BLUE], labels={"markets_listed": "Markets listed", "service": ""})
        fig.update_traces(textposition="outside", cliponaxis=False,
                          hovertemplate="%{y}<br>Markets listed: %{x}<extra></extra>")
        fig.update_xaxes(range=[0, max(top["markets_listed"]) * 1.16], dtick=10 if top["markets_listed"].max() > 20 else 1)
        st.plotly_chart(style_chart(fig), width="stretch", config={"displayModeBar": False})
    with right:
        st.subheader("Markets in this selection")
        st.caption("Geographic coverage of the dataset records selected in the sidebar.")
        mapped = filtered.groupby(["country", "iso3"], as_index=False).agg(listings=("listing_id", "size"))
        mapped["included"] = 1
        fig = px.choropleth(mapped, locations="iso3", color="included", hover_name="country",
                            custom_data=["listings"], color_continuous_scale=[BLUE, BLUE])
        fig.update_traces(hovertemplate="%{hovertext}<br>Selected listings: %{customdata[0]}<extra></extra>",
                          marker_line_color="#FFFFFF", marker_line_width=0.45)
        fig.update_geos(showframe=False, showcoastlines=False, showland=True, landcolor="#E7ECF5",
                        bgcolor="rgba(0,0,0,0)", projection_type="natural earth", fitbounds=False,
                        projection_scale=1.85)
        fig.update_layout(coloraxis_showscale=False)
        st.plotly_chart(style_chart(fig), width="stretch", config={"displayModeBar": False})
    best = coverage.iloc[0]
    st.markdown(
        f'<div class="finding"><span>FROM THIS SELECTION</span><strong>{escape(best["service"])} '
        f'appears in {int(best["markets_listed"])} of {filtered["market_id"].nunique()} selected markets.</strong>'
        '<p>This counts mentions in the original research table. It does not measure users or payment volume.</p></div>',
        unsafe_allow_html=True,
    )
    with st.container(border=True):
        st.subheader("Explore the listings")
        columns = ["country", "service", "role", "website", "review_url"]
        view = filtered[columns].rename(columns={"country": "Market", "service": "Payment service", "role": "Listed role",
                                                "website": "Website", "review_url": "Review reference"})
        st.dataframe(view, hide_index=True, width="stretch", height=340,
                     column_config={"Website": st.column_config.LinkColumn("Website"),
                                    "Review reference": st.column_config.LinkColumn("Review reference")})
        st.download_button("Download this selection", filtered.to_csv(index=False).encode("utf-8-sig"),
                           "payments-selection.csv", "text/csv", key="filtered_download")


def compare_markets(data):
    st.subheader("Compare markets")
    st.caption("Explore the main service and two alternatives recorded for each market in the source.")
    selected = st.multiselect("Choose up to three markets", sorted(data.markets["country"].tolist()),
                              default=["India", "United Kingdom", "United States"], max_selections=3, key="compare")
    if not selected:
        st.info("Choose a market to start the comparison.")
        return
    for col, country in zip(st.columns(len(selected), gap="medium"), selected):
        with col, st.container(border=True):
            st.markdown(f"### {country}")
            records = data.listings[data.listings["country"].eq(country)]
            for _, record in records.iterrows():
                st.caption(record["role"].upper())
                st.markdown(f"**{record['service']}**")
                st.link_button("Service website ↗", record["website"])
            st.caption("Service availability and linked websites need verification against primary sources.")
    records = data.listings[data.listings["country"].isin(selected)]
    shared = service_coverage(records)
    shared = shared[shared["markets_listed"].gt(1)]
    if len(selected) > 1:
        st.markdown("#### Shared service listings")
        if shared.empty:
            st.write("No service is listed in more than one of these selected markets.")
        else:
            st.dataframe(shared[["service", "markets_listed"]].rename(columns={"service": "Service", "markets_listed": "Selected markets"}),
                         hide_index=True, width="stretch")
    comparison = records.pivot(index="country", columns="role", values="service").reindex(columns=["Primary", "Alternative 1", "Alternative 2"])
    st.download_button("Download comparison", comparison.to_csv().encode("utf-8-sig"), "market-comparison.csv", "text/csv")


def methodology(data):
    st.subheader("Data and methodology")
    st.write("The original collaborative project collected one main payment service and two alternatives for 100 countries and territories. "
             "The explorer reshapes those records into market, service and listing tables.")
    st.markdown("#### What the counts mean")
    st.write("A listing is one service named in one source row and role. Service coverage counts distinct markets mentioning that service. "
             "These are dataset counts. They do not establish current availability, popularity or transaction volume.")
    st.markdown("#### Cleaning performed")
    cols = st.columns(3)
    cols[0].metric("Name corrections", data.summary["name_changes"])
    cols[1].metric("URL format changes", data.summary["url_changes"])
    cols[2].metric("Shares awaiting sources", data.summary["shares_needing_evidence"])
    st.dataframe(data.changes.rename(columns={"country": "Market", "field": "Field", "original": "Original", "cleaned": "Cleaned", "reason": "Reason"}).drop(columns="market_id"),
                 hide_index=True, width="stretch", height=280)
    with st.expander("Original market-share values and missing evidence"):
        st.write("The source includes percentages but does not document their measurement period, definition or original evidence. "
                 "They are preserved here for research and excluded from analytical rankings and aggregates.")
        share_view = data.markets[["country", "primary_service", "reported_share", "share_status"]].copy()
        share_view["reported_share"] = share_view["reported_share"] * 100
        st.dataframe(share_view, hide_index=True, width="stretch", height=300,
                     column_config={"country": "Market", "primary_service": "Listed main service",
                                    "reported_share": st.column_config.NumberColumn("Original share (unverified)", format="%.0f%%"),
                                    "share_status": "Source status"})
    st.markdown("#### Research still needed")
    st.write("Verify service identity and country availability, find primary sources for market-share figures, "
             "and record the observation date and measurement definition. Review and screenshot links are references supplied by the original dataset.")
    st.link_button("View the original dataset on GitHub ↗", data.summary["source"])
    workbook = ROOT / "outputs" / "payments-analysis" / "Digital-Payments-Analysis.xlsx"
    if workbook.exists():
        st.download_button("Download Excel analysis", workbook.read_bytes(), workbook.name,
                           "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    st.download_button("Download original CSV", (ROOT / "data/raw/payments.csv").read_bytes(), "original-payments.csv", "text/csv")


def main():
    st.set_page_config(page_title="Digital Payments Explorer · Aditya Sharma", page_icon="◈", layout="wide")
    st.markdown("""<style>
    .block-container { max-width: 1440px; padding-top: 3.5rem; padding-bottom: 3rem; }
    h1 { letter-spacing: -.045em; font-weight: 700 !important; line-height: 1.1 !important; }
    h3 { letter-spacing: -.025em; }
    .eyebrow { color:#738098; font-size:11px; font-weight:700; letter-spacing:.16em; margin-bottom:16px; }
    .intro { color:#738098; font-size:16px; max-width:680px; margin:14px 0 18px; line-height:1.6; }
    [data-testid="stMetric"] { background:white; border:1px solid #E4E8F0; border-radius:12px; padding:18px 22px; }
    [data-testid="stMetricValue"] { font-size:32px; font-weight:600; letter-spacing:-.04em; }
    [data-testid="stSidebar"] { border-right:1px solid #E4E8F0; }
    .finding { background:#E9EEFD; border:1px solid #D7E0FB; border-radius:12px; padding:22px 26px; margin:10px 0 26px; }
    .finding span { display:block; color:#315CDE; font-size:10px; font-weight:700; letter-spacing:.14em; margin-bottom:10px; }
    .finding strong { display:block; font-size:19px; letter-spacing:-.02em; }
    .finding p { color:#63708A; font-size:13px; margin:9px 0 0; }
    @media(max-width:640px) { .block-container { padding:3.4rem 1rem 1.3rem; } }
    </style>""", unsafe_allow_html=True)
    source = ROOT / "data/raw/payments.csv"
    try:
        data = load_data(source.stat().st_mtime)
    except (ValueError, LookupError, OSError) as error:
        st.error(f"The dataset could not be loaded: {error}")
        st.stop()
    with st.sidebar:
        st.markdown("### Payments explorer")
        st.caption("Explore a collaborative research dataset")
        st.divider()
        st.markdown("**Filter the overview**")
        countries = st.multiselect("Markets", sorted(data.markets["country"].tolist()), key="countries")
        service_names = dict(zip(data.services["service_id"], data.services["service"]))
        services = st.multiselect("Payment services", data.services["service_id"].tolist(),
                                  format_func=lambda key: service_names[key], key="services")
        roles = st.multiselect("Listed role", ["Primary", "Alternative 1", "Alternative 2"], key="roles")
        search = st.text_input("Search markets or services", placeholder="Try India or PayPal", key="search")
        st.button("Reset filters", on_click=reset_filters, width="stretch")
        st.divider()
        st.caption("Coverage refers to mentions in this dataset. Market-share figures and current availability need source verification.")
        st.link_button("Portfolio ↗", "https://aditya-6446.github.io/portfolio/")
    filtered = filter_listings(data.listings, countries, services, roles, search)
    st.markdown('<div class="eyebrow">ADITYA SHARMA / DATA ANALYSIS</div>', unsafe_allow_html=True)
    st.title("Digital payments, across markets.")
    st.markdown('<div class="intro">Explore payment-service listings, compare markets, and follow the data from its original source to the analysis.</div>', unsafe_allow_html=True)
    st.caption("ORIGINAL RESEARCH SNAPSHOT · 100 COUNTRIES AND TERRITORIES · SOURCE VERIFICATION IN PROGRESS")
    section = st.radio("Explore", ["Overview", "Compare markets", "Data & methodology"], horizontal=True, label_visibility="collapsed", key="section")
    st.divider()
    if section == "Overview":
        stats = st.columns(4, gap="medium")
        stats[0].metric("Markets selected", filtered["market_id"].nunique())
        stats[1].metric("Services listed", filtered["service_id"].nunique())
        stats[2].metric("Service listings", len(filtered))
        stats[3].metric("Primary listings", int(filtered["role"].eq("Primary").sum()))
        st.write("")
        overview(data, filtered)
    elif section == "Compare markets":
        compare_markets(data)
    else:
        methodology(data)
    st.caption("Digital Payments Explorer · Python, SQL, Excel and interactive visualization · Collaborative project")


if __name__ == "__main__":
    main()

"""Interactive exploration of the project's documented payment-service listings."""

from html import escape
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from src.payments import ROOT, filter_listings, prepare_data, service_coverage

ACCENT = "#79B7AE"
INK = "#202725"


@st.cache_data
def load_data(source_modified: float):
    return prepare_data()


def style_chart(fig, height=390):
    fig.update_layout(
        height=height, margin=dict(l=0, r=20, t=16, b=6),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Arial", size=12, color=INK),
        hoverlabel=dict(bgcolor=INK, font_color="#F8F6EF"),
        xaxis=dict(gridcolor="#EAE8E0", zeroline=False),
        yaxis=dict(gridcolor="#EAE8E0", zeroline=False),
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
    left, right = st.columns([1.05, 1], gap="medium")
    with left, st.container(border=True, key="chart_services"):
        st.markdown('<div class="panel-kicker">01 / SERVICE COVERAGE</div>', unsafe_allow_html=True)
        st.subheader("Most-listed services")
        st.caption("Distinct markets mentioning each service in the selected records.")
        top = coverage.head(12).sort_values(["markets_listed", "service"], ascending=[True, False])
        fig = px.bar(top, x="markets_listed", y="service", orientation="h", text="markets_listed",
                     color_discrete_sequence=["#4F8D83"], labels={"markets_listed": "Markets listed", "service": ""})
        fig.update_traces(textposition="outside", cliponaxis=False,
                          marker_cornerradius=5, hovertemplate="%{y}<br>Markets listed: %{x}<extra></extra>")
        fig.update_xaxes(range=[0, max(top["markets_listed"]) * 1.16], dtick=10 if top["markets_listed"].max() > 20 else 1)
        st.plotly_chart(style_chart(fig), width="stretch", config={"displayModeBar": False})
    with right, st.container(border=True, key="chart_markets"):
        st.markdown('<div class="panel-kicker">02 / GEOGRAPHIC VIEW</div>', unsafe_allow_html=True)
        st.subheader("Markets in this selection")
        st.caption("Geographic coverage of the dataset records selected in the sidebar.")
        mapped = filtered.groupby(["country", "iso3"], as_index=False).agg(listings=("listing_id", "size"))
        mapped["included"] = 1
        fig = px.choropleth(mapped, locations="iso3", color="included", hover_name="country",
                            custom_data=["listings"], color_continuous_scale=["#4F8D83", "#4F8D83"])
        fig.update_traces(hovertemplate="%{hovertext}<br>Selected listings: %{customdata[0]}<extra></extra>",
                          marker_line_color="#F8F6EF", marker_line_width=0.45)
        fig.update_geos(showframe=False, showcoastlines=False, showland=True, landcolor="#E9E6DD",
                        bgcolor="rgba(0,0,0,0)", projection_type="natural earth", fitbounds=False,
                        projection_scale=2.45)
        fig.update_layout(coloraxis_showscale=False)
        st.plotly_chart(style_chart(fig), width="stretch", config={"displayModeBar": False})
    best = coverage.iloc[0]
    st.markdown(
        '<div class="finding"><div class="finding-mark">↗</div><div><span>THE SIGNAL IN THIS SELECTION</span>'
        f'<strong>{escape(best["service"])} appears in <em>{int(best["markets_listed"])} of '
        f'{filtered["market_id"].nunique()}</em> selected markets.</strong>'
        '<p>This counts mentions in the original research table. It does not measure users or payment volume.</p></div></div>',
        unsafe_allow_html=True,
    )
    with st.container(border=True, key="listings_panel"):
        st.markdown('<div class="panel-kicker">03 / SOURCE RECORDS</div>', unsafe_allow_html=True)
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
    st.markdown('<div class="section-kicker">MARKET COMPARISON / 02</div>', unsafe_allow_html=True)
    st.subheader("Compare markets")
    st.caption("Explore the main service and two alternatives recorded for each market in the source.")
    selected = st.multiselect("Choose up to three markets", sorted(data.markets["country"].tolist()),
                              default=["India", "United Kingdom", "United States"], max_selections=3, key="compare")
    if not selected:
        st.info("Choose a market to start the comparison.")
        return
    for index, (col, country) in enumerate(zip(st.columns(len(selected), gap="medium"), selected), start=1):
        with col, st.container(border=True, key=f"market_card_{index}"):
            st.markdown(f'<div class="panel-kicker">MARKET PROFILE / {index:02d}</div>', unsafe_allow_html=True)
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
    st.markdown('<div class="section-kicker">BEHIND THE NUMBERS / 03</div>', unsafe_allow_html=True)
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
    st.markdown(f"<style>{(ROOT / 'dashboard.css').read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)
    source = ROOT / "data/raw/payments.csv"
    try:
        data = load_data(source.stat().st_mtime)
    except (ValueError, LookupError, OSError) as error:
        st.error(f"The dataset could not be loaded: {error}")
        st.stop()
    with st.sidebar:
        st.markdown('<div class="sidebar-brand"><div class="brand-symbol">◈</div><div><span>RESEARCH SERIES / 01</span><strong>Payments<br>Explorer</strong></div></div>', unsafe_allow_html=True)
        st.markdown('<div class="sidebar-lede">A closer look at how payment services are listed across markets.</div>', unsafe_allow_html=True)
        st.markdown('<div class="sidebar-section">REFINE THE VIEW <span>↘</span></div>', unsafe_allow_html=True)
        countries = st.multiselect("Markets", sorted(data.markets["country"].tolist()), key="countries")
        service_names = dict(zip(data.services["service_id"], data.services["service"]))
        services = st.multiselect("Payment services", data.services["service_id"].tolist(),
                                  format_func=lambda key: service_names[key], key="services")
        roles = st.multiselect("Listed role", ["Primary", "Alternative 1", "Alternative 2"], key="roles")
        search = st.text_input("Search markets or services", placeholder="Try India or PayPal", key="search")
        st.button("Reset filters", on_click=reset_filters, width="stretch")
        st.markdown('<div class="sidebar-note"><span>READING NOTE</span><p>Coverage means mentions in this dataset. Market-share figures and current availability still need source verification.</p></div>', unsafe_allow_html=True)
        st.link_button("Portfolio ↗", "https://aditya-6446.github.io/portfolio/")
    filtered = filter_listings(data.listings, countries, services, roles, search)
    st.markdown('''<div class="hero"><div class="hero-orbit orbit-one"></div><div class="hero-orbit orbit-two"></div>
        <div class="hero-top"><span><i></i> ADITYA SHARMA / DATA ANALYSIS</span><span>FIELD NOTES — 001</span></div>
        <div class="hero-content"><div class="hero-overline">THE DIGITAL PAYMENTS EXPLORER</div>
        <h1>Payments are global.<br><em>The story is local.</em></h1>
        <p>Explore payment-service listings, compare markets, and trace each insight back to its source.</p></div>
        <div class="hero-bottom"><span>100 COUNTRIES &amp; TERRITORIES</span><span>RESEARCH SNAPSHOT <b>·</b> SOURCE VERIFICATION IN PROGRESS</span></div></div>''', unsafe_allow_html=True)
    st.markdown('<div class="nav-kicker">EXPLORE THE RESEARCH <span>↓</span></div>', unsafe_allow_html=True)
    section = st.radio("Explore", ["Overview", "Compare markets", "Data & methodology"], horizontal=True, label_visibility="collapsed", key="section")
    if section == "Overview":
        st.markdown('<div class="section-heading"><div><span>AT A GLANCE / 01</span><h2>Explore the dataset</h2></div><p>Filter the records to see how the picture changes.</p></div>', unsafe_allow_html=True)
        stats = st.columns(4, gap="medium")
        stats[0].metric("Markets selected", filtered["market_id"].nunique())
        stats[1].metric("Services listed", filtered["service_id"].nunique())
        stats[2].metric("Service listings", len(filtered))
        stats[3].metric("Primary listings", int(filtered["role"].eq("Primary").sum()))
        overview(data, filtered)
    elif section == "Compare markets":
        compare_markets(data)
    else:
        methodology(data)
    st.markdown('<div class="dashboard-footer"><span>◈ &nbsp; DIGITAL PAYMENTS EXPLORER</span><span>ADITYA SHARMA &nbsp; / &nbsp; DATA ANALYSIS</span></div>', unsafe_allow_html=True)


if __name__ == "__main__":
    main()

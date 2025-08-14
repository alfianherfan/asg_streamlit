import streamlit as st 
import pandas as pd 
import numpy as np
import pickle
import plotly.express as px 
import plotly.graph_objects as go
from datetime import datetime, timedelta

# ---- set konfigurasi halaman ----
st.set_page_config(
    page_title='Dashboard Analisis Penjualan', ###GANTIIIIIIIII
    # page_icon='',
    layout='wide',
    initial_sidebar_state='expanded'
)

# -- fungsi untuk memuat data --
@st.cache_data
def load_data():
    return pd.read_csv("data/ecommerce_data.csv")

df = load_data()

# -- ganti pd date time --
df['InvoiceDate'] = pd.to_datetime(df['InvoiceDate'])

# judul dashboard 
st.title("Dashboard Penjualan Toko Jaya Abadi")
st.markdown("Dashboard berisi gambaran umum performa penjualan dan trend")

st.markdown("---") # garis pembatas 

# ----sidebar untuk filter ----
st.sidebar.header("**Filter**")

pilihan_halaman = st.sidebar.radio(
    "Halaman:",
    ("Overview Dashboard")
)

# Filter global (muncul untuk halaman overview dashboard)
if pilihan_halaman == "Overview Dashboard":
    st.sidebar.markdown("## Filter Dashboard")

    min_date = df['InvoiceDate'].min().date()
    max_date = df['InvoiceDate'].max().date()

    date_range = st.sidebar.date_input(
        "Pilih Rentang Tanggal",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )

    if len(date_range) == 2:
        start_date_filter = pd.to_datetime(date_range[0])
        end_date_filter = pd.to_datetime(date_range[1])

        filtered_df = df[
            (df['InvoiceDate'] >= start_date_filter) &
            (df['InvoiceDate'] <= end_date_filter)
        ]
    else:
        # kalau filter date-nya belum tuntas
        filtered_df = df


# hitung kolom Sales
df['Sales'] = df['Quantity'] * df['UnitPrice']

# Filter hanya tahun 2011
df_2011 = df[df['InvoiceDate'].dt.year == 2011]

# 1. top 5 produk penjualan tertinggi tahun 2011
top5_2011 = (
    df_2011.groupby('Description', as_index=False)['Sales']
           .sum()
           .sort_values('Sales', ascending=False)
           .head(5)
)

fig1 = px.bar(top5_2011, x='Description', y='Sales', template='seaborn')
fig1.update_traces(marker_color='#7A9E9F')
fig1.update_layout(title="Top 5 Produk Terlaris Tahun 2011", title_x=0)

# 2. total penjualan per bulan tahun 2011
df_2011['Month'] = df_2011['InvoiceDate'].dt.month
sales_per_month = (
    df_2011.groupby('Month', as_index=False)['Sales']
           .sum()
           .sort_values('Month')
)

fig2 = px.bar(sales_per_month, x='Month', y='Sales', template='seaborn')
fig2.update_traces(marker_color='#A3C4BC')
fig2.update_layout(title="Total Sales per Month (2011)", title_x=0)

# 3. produk terlaris setiap bulan di tahun 2011
# cari produk dengan sales tertinggi di tiap bulan
top_product_each_month = (
    df_2011.groupby(['Month', 'Description'], as_index=False)['Sales']
           .sum()
           .sort_values(['Month', 'Sales'], ascending=[True, False])
           .groupby('Month')
           .head(1)
)

fig3 = px.bar(top_product_each_month, x='Month', y='Sales', color='Description', template='seaborn')
fig3.update_layout(title="Produk Terlaris per Bulan (2011)", title_x=0)

# tampilkan sejajar
col1, col2, col3 = st.columns(3)
with col1:
    st.plotly_chart(fig1, use_container_width=True)
with col2:
    st.plotly_chart(fig2, use_container_width=True)
with col3:
    st.plotly_chart(fig3, use_container_width=True)

 # filter berdasarkan wilayah 
    selected_regions = st.sidebar.multiselect(
        "Pilih Wilayah:",
        options=df['Country'].unique().tolist(),
        default=df['Country'].unique().tolist()
    )

    filtered_df = filtered_df[filtered_df['Country'].isin(selected_regions)]

# filter kategori produk
selected_categories = st.sidebar.multiselect(
    "Pilih Kategori Produk:",
    options=df['Description'].unique().tolist(),
    default=df['Description'].unique().tolist()
)

# cek apakah user memilih kategori tertentu
if selected_categories:
    filtered_df = df[df['Description'].isin(selected_categories)]
else:  # kalau tidak ada filter kategori
    filtered_df = df.copy()

st.markdown("---")

# --- halaman utama overview dashboard -----------------
if pilihan_halaman == "Overview Dashboard":
#   metrik utama
    st.subheader("Ringkasan Performa Penjualan")

    col1, col2, col3, col4 = st.columns([3, 2, 3, 2])

    total_sales = filtered_df['Sales'].sum()
    total_orders = filtered_df['InvoiceNo'].nunique()
    avg_order_value = total_sales / total_orders if total_orders > 0 else 0 # handle kalau total order 0
    total_products_sold = filtered_df['Quantity'].sum()

    with col1:
      st.metric(label="Total Penjualan", value=f"$ {total_sales:,.2f}")
    with col2:
      st.metric(label="Jumlah Pesanan", value=f"{total_orders:,.2f}")
    with col3:
      st.metric(label="Rata-Rata Nilai Pesanan", value=f"$ {avg_order_value:,.2f}")
    with col4:
      st.metric(label="Jumlah Produk Terjual", value=f"{total_products_sold:,.2f}")


 # tren penjualan/line chart
    st.subheader("Tren Penjualan Bulanan")
    sales_by_month = df_2011.groupby('Month')['Sales'].sum()
    # sales_by_month['bulan'] = pd.to_datetime(sales_by_month['bulan']).dt.to_period('M')
    # sales_by_month = sales_by_month.value_counts(by='bulan')
    # sales_by_month['bulan'] = sales_by_month['bulan'].astype(str)

fig_monthly_sales = px.line(
      sales_by_month,
      x=sales_by_month.index,
      y='Sales',
      markers=True,
      hover_name=sales_by_month.index
    )
st.plotly_chart(fig_monthly_sales, use_container_width=True)

st.markdown("---")

col_vis1, col_vis2 = st.columns(2)

with col_vis1:
        st.write("### Top 10 Produk Terlaris")

        top_product_sold = filtered_df.groupby('Description')['Sales'].sum().nlargest(10).reset_index() # agregasi

        # bar chart
        fig_top_products = px.bar(
          top_product_sold,
          x='Sales',
          y='Description',
          orientation='h'
        )

        st.plotly_chart(fig_top_products, use_container_width=True)

with col_vis2:
    st.write("### Tren Penjualan Bulanan")

    # pastikan kolom tanggal sudah datetime
    filtered_df['InvoiceDate'] = pd.to_datetime(filtered_df['InvoiceDate'])

    # buat kolom bulan
    filtered_df['Month_Num'] = filtered_df['InvoiceDate'].dt.month
    filtered_df['Month'] = filtered_df['InvoiceDate'].dt.month_name()

    # grouping dan urutkan bulan
    sales_by_month = (
        filtered_df.groupby(['Month_Num', 'Month'])['Quantity']
        .sum()
        .reset_index()
        .sort_values('Month_Num')
    )

    fig_monthly_sales = px.line(
        sales_by_month,
        x='Month',
        y='Quantity',
        markers=True
    )

    st.plotly_chart(fig_monthly_sales, use_container_width=True)
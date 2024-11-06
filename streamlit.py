import streamlit as st
import pandas as pd
import time
from io import BytesIO

sudah_upload = st.file_uploader("Upload Sudah Upload.xlsx", type=["xlsx"])
forecast = st.file_uploader("Upload Forecast.xlsx", type=["xlsx"])
catalogue = st.file_uploader("Upload Catalogue Update.xlsx", type=["xlsx"])
purchase = st.file_uploader("Upload Item Purchases by Item Detail.xlsx", type=["xlsx"])

start = st.button("Start")

if start:
    if forecast is None or catalogue is None or purchase is None:
        st.warning("Upload all files.")
    else:
        progress_bar = st.progress(0, text="Reading Sudah Upload.xlsx")
        st.session_state.sudah_upload_toko = pd.read_excel(sudah_upload, sheet_name="Toko", dtype={'Item No.': str})
        st.session_state.sudah_upload_gudang = pd.read_excel(sudah_upload, sheet_name="Gudang", dtype={'Item No.': str})

        progress_bar.progress(33, text="Reading Forecast.xlsx")
        st.session_state.forecast_df = pd.read_excel(forecast, dtype={'ItemCode': str})

        progress_bar.progress(66, text="Reading Catalogue Update.xlsx")
        st.session_state.catalogue_df = pd.read_excel(catalogue, dtype={'Item No.': str})

        progress_bar.progress(100, text="Reading Item Purchases by Item Detail.xlsx")
        st.session_state.purchase_df = pd.read_excel(purchase, dtype={'Item No.': str})

        progress_bar.empty()
        st.write("Dataframe sudah dibaca.")

if "forecast_df" not in st.session_state:
    st.warning("Upload Forecast.xlsx")
else:
    forecast_df = st.session_state.forecast_df

if "catalogue_df" not in st.session_state:
    st.warning("Upload Catalogue Update.xlsx")
else:
    catalogue_df = st.session_state.catalogue_df

if "purchase_df" not in st.session_state:
    st.warning("Upload Item Purchases by Item Detail.xlsx")
else:
    purchase_df = st.session_state.purchase_df

if "sudah_upload_toko" not in st.session_state or "sudah_upload_gudang" not in st.session_state:
    st.warning("Upload Sudah Upload.xlsx")
else:
    sudah_upload_toko = st.session_state.sudah_upload_toko
    sudah_upload_gudang = st.session_state.sudah_upload_gudang

if all(key in st.session_state for key in ["forecast_df", "catalogue_df", "purchase_df", "sudah_upload_toko", "sudah_upload_gudang"]):
    list = forecast_df[forecast_df['ItemStatus'] == 'Active'].rename(columns={'ItemCode': 'Item No.'})
    list = pd.merge(list, catalogue_df[['Item No.', 'Gudang', 'Asemka', 'Tengsek']], on='Item No.', how='left')
    list = list[['Kategori', 'SubItemName', 'VendorName', 'Item No.', 'ItemName', 'Gudang', 'Asemka', 'Tengsek', 'OnOrder', 'IsiCtn', 'InventoryUoM', 'LastPurchasePrice', 'PriceFC', 'HargaJualLusin', 'HargaJualKoli', 'HargaJualSpecial', 'Tanggal Last SO', 'Tanggal Last GRPO', 'Tanggal Due Date GRPO', 'QtyLastGR']]

    listgudang = list[list['Gudang'] >= 20]
    listtoko = list[(list['Asemka'] + list['Tengsek']) >= 20]

    tanggal_loading = st.multiselect("Select Container No.", purchase_df['Tanggal Loading'].unique())
    if tanggal_loading:
        purchase_df = purchase_df[purchase_df['Tanggal Loading'].isin(tanggal_loading)]
        nocontainer = st.multiselect("Select Container No.", purchase_df['Container No.'].unique())
        purchase_df = purchase_df[purchase_df['Tanggal Loading'].isin(tanggal_loading)]
        purchase_df = purchase_df[purchase_df['Container No.'].isin(nocontainer)]
        purchase_df['Posting Date'] = pd.to_datetime(purchase_df['Posting Date'], format='%d.%m.%y')
        purchase_df = purchase_df.sort_values(by='Posting Date', ascending=False).groupby(['Item No.'])[['Tanggal Loading', 'Container No.']].first().reset_index()
        
        listgudang = pd.merge(listgudang, purchase_df[['Item No.', 'Tanggal Loading', 'Container No.']], on='Item No.', how='left')
        listtoko = pd.merge(listtoko, purchase_df[['Item No.', 'Tanggal Loading', 'Container No.']], on='Item No.', how='left')

        if st.button("Start Making"):
            with st.spinner("Making List Gudang..."):
                progress_bar = st.progress(0)
                total_steps = 5

                for step in range(total_steps):
                    if step == 0:
                        time.sleep(1)
                        st.write("Step 1: Mengumpulkan data gudang...")
                        listgudang = listgudang[listgudang['Gudang'] >= 20]
                        listtoko = listtoko[(listtoko['Asemka'] + listtoko['Tengsek']) >= 20]
                    elif step == 1:
                        time.sleep(1)
                        st.write("Step 2: Memproses data...")
                        listgudang = listgudang[~listgudang['Item No.'].isin(sudah_upload_gudang['Item No.'])]
                        listtoko = listtoko[~listtoko['Item No.'].isin(sudah_upload_toko['Item No.'])]
                    elif step == 2:
                        time.sleep(1)
                        st.write("Step 3: Membuat laporan...")
                        listgudang = listgudang[~listgudang['Kategori'].isin(['Marketplace', 'MARKETPLACE', 'DISKON 5%', 'SPECIAL ORDER', 'MIMORI', 'TEBUS MURAH'])]
                        listtoko = listtoko[~listtoko['Kategori'].isin(['Marketplace', 'MARKETPLACE', 'DISKON 5%', 'SPECIAL ORDER', 'MIMORI', 'TEBUS MURAH'])]
                        listgudang.loc[listgudang['Kategori'].isin(['AKSESORIS', 'AKSESORIS RAMBUT']), 'List Gudang'] = 'ACC'
                        listgudang.loc[listgudang['Kategori'].isin(['TAS & DOMPET', 'BARANG LOKAL']), 'List Gudang'] = 'TAS & DOMPET'
                        listgudang.loc[listgudang['Kategori'].isin(['STATIONARY']), 'List Gudang'] = 'STATIONARY'
                        listgudang.loc[listgudang['Kategori'].isin(['AKSESORIS RAMBUT KAMINO', 'LOLI & MOLI']), 'List Gudang'] = 'BRAND'
                        listgudang.loc[listgudang['Kategori'].isin(['ALAT MAKE UP']), 'List Gudang'] = 'AMU'
                        listgudang.loc[listgudang['Kategori'].isin(['ROCHE']), 'List Gudang'] = 'ROCHE'
                    elif step == 3:
                        time.sleep(1)
                        st.write("Step 4: Menyimpan laporan...")
                        listtoko.loc[listtoko['Kategori'].isin(['AKSESORIS', 'AKSESORIS RAMBUT']), 'List Toko'] = 'ACC'
                        listtoko.loc[listtoko['Kategori'].isin(['TAS & DOMPET', 'BARANG LOKAL']), 'List Toko'] = 'TAS & DOMPET'
                        listtoko.loc[listtoko['Kategori'].isin(['STATIONARY']), 'List Toko'] = 'STATIONARY'
                        listtoko.loc[listtoko['Kategori'].isin(['AKSESORIS RAMBUT KAMINO', 'LOLI & MOLI']), 'List Toko'] = 'BRAND'
                        listtoko.loc[listtoko['Kategori'].isin(['ALAT MAKE UP']), 'List Toko'] = 'AMU'
                        listtoko.loc[listtoko['Kategori'].isin(['ROCHE']), 'List Toko'] = 'ROCHE'
                    elif step == 4:
                        time.sleep(1)
                        st.write("Step 5: Selesai!")
                        
                        output = BytesIO()
                        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                            listgudang.to_excel(writer, index=False, sheet_name="List Gudang")
                            listtoko.to_excel(writer, index=False, sheet_name="List Toko")
                        st.download_button("Download List Gudang", data=output.getvalue(), file_name="List Upload.xlsx")
                    
                    progress_bar.progress((step + 1) / total_steps)
                    
            st.success("List Upload Made!")

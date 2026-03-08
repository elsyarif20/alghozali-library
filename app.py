import streamlit as st
import pandas as pd
from datetime import datetime
from supabase import create_client, Client

# ==========================================
# 1. KONFIGURASI HALAMAN & KONEKSI SUPABASE
# ==========================================
st.set_page_config(page_title="Al-Ghozali Library", page_icon="📚", layout="wide")

# Mengambil rahasia dari secrets.toml
URL = st.secrets["SUPABASE_URL"]
KEY = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(URL, KEY)

# ==========================================
# 2. FUNGSI DATABASE (CRUD KE SUPABASE)
# ==========================================
def fetch_books():
    response = supabase.table("books").select("*").execute()
    return pd.DataFrame(response.data)

def fetch_history():
    response = supabase.table("borrow_history").select("*").execute()
    return pd.DataFrame(response.data)

# Ambil data dari Supabase (Setiap halaman di-refresh, data terbaru akan ditarik)
df_books = fetch_books()

# ==========================================
# 3. NAVIGASI SIDEBAR
# ==========================================
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/2232/2232688.png", width=100)
st.sidebar.title("Al-Ghozali Library")
menu = st.sidebar.radio("Navigasi Menu", ["🏠 Beranda", "🔍 Katalog Buku", "🤝 Peminjaman", "⚙️ Kelola Buku (Admin)"])

# ==========================================
# 4. HALAMAN BERANDA
# ==========================================
if menu == "🏠 Beranda":
    st.title("Selamat Datang di Al-Ghozali Library 📚")
    st.markdown("Menebar ilmu dan hikmah melalui literasi Islami.")
    st.divider()
    
    col1, col2, col3 = st.columns(3)
    total_buku = len(df_books)
    buku_tersedia = len(df_books[df_books['status'] == 'Tersedia']) if total_buku > 0 else 0
    buku_dipinjam = total_buku - buku_tersedia
    
    col1.metric("Total Buku", total_buku)
    col2.metric("Buku Tersedia", buku_tersedia)
    col3.metric("Sedang Dipinjam", buku_dipinjam)

# ==========================================
# 5. HALAMAN KATALOG BUKU
# ==========================================
elif menu == "🔍 Katalog Buku":
    st.title("Katalog Buku Perpustakaan")
    
    col1, col2 = st.columns(2)
    search_query = col1.text_input("Cari Judul Buku:")
    
    kategori_list = ["Semua Kategori"]
    if not df_books.empty:
        kategori_list += list(df_books['kategori'].unique())
        
    filter_kategori = col2.selectbox("Filter Kategori:", kategori_list)
    
    df_tampil = df_books.copy()
    if not df_tampil.empty:
        if search_query:
            df_tampil = df_tampil[df_tampil['judul'].str.contains(search_query, case=False)]
        if filter_kategori != "Semua Kategori":
            df_tampil = df_tampil[df_tampil['kategori'] == filter_kategori]
            
    st.dataframe(df_tampil, use_container_width=True, hide_index=True)

# ==========================================
# 6. HALAMAN PEMINJAMAN BUKU
# ==========================================
elif menu == "🤝 Peminjaman":
    st.title("Sistem Peminjaman Buku")
    
    tab1, tab2 = st.tabs(["Pinjam Buku", "Kembalikan Buku"])
    
    with tab1:
        st.subheader("Formulir Peminjaman")
        buku_tersedia = df_books[df_books['status'] == 'Tersedia'] if not df_books.empty else pd.DataFrame()
        
        with st.form("form_pinjam"):
            nama_peminjam = st.text_input("Nama Lengkap Peminjam")
            pilihan_buku = st.selectbox("Pilih Buku", buku_tersedia['judul'].tolist() if not buku_tersedia.empty else ["Tidak ada buku tersedia"])
            submit_pinjam = st.form_submit_button("Pinjam Buku")
            
            if submit_pinjam:
                if nama_peminjam and pilihan_buku != "Tidak ada buku tersedia":
                    # Cari ID buku
                    id_buku = buku_tersedia.loc[buku_tersedia['judul'] == pilihan_buku, 'id_buku'].values[0]
                    
                    # 1. Update status di tabel books
                    supabase.table("books").update({"status": "Dipinjam"}).eq("id_buku", id_buku).execute()
                    
                    # 2. Catat di tabel borrow_history
                    supabase.table("borrow_history").insert({
                        "nama_peminjam": nama_peminjam,
                        "id_buku": id_buku,
                        "tanggal_pinjam": datetime.now().strftime("%Y-%m-%d"),
                        "status": "Dipinjam"
                    }).execute()
                    
                    st.success(f"Berhasil! Buku '{pilihan_buku}' dipinjam oleh {nama_peminjam}.")
                    st.rerun()
                else:
                    st.error("Mohon lengkapi formulir.")
                    
    with tab2:
        st.subheader("Pengembalian Buku")
        buku_dipinjam = df_books[df_books['status'] == 'Dipinjam'] if not df_books.empty else pd.DataFrame()
        
        with st.form("form_kembali"):
            pilihan_kembali = st.selectbox("Pilih Buku yang Dikembalikan", buku_dipinjam['judul'].tolist() if not buku_dipinjam.empty else ["Tidak ada buku dipinjam"])
            submit_kembali = st.form_submit_button("Kembalikan Buku")
            
            if submit_kembali:
                if pilihan_kembali != "Tidak ada buku dipinjam":
                    id_buku = buku_dipinjam.loc[buku_dipinjam['judul'] == pilihan_kembali, 'id_buku'].values[0]
                    
                    # Update status di tabel books menjadi Tersedia kembali
                    supabase.table("books").update({"status": "Tersedia"}).eq("id_buku", id_buku).execute()
                    
                    st.success(f"Buku '{pilihan_kembali}' berhasil dikembalikan. Terima kasih!")
                    st.rerun()

# ==========================================
# 7. HALAMAN KELOLA BUKU (ADMIN)
# ==========================================
elif menu == "⚙️ Kelola Buku (Admin)":
    st.title("Manajemen Koleksi Buku")
    
    with st.form("form_tambah_buku"):
        st.subheader("Tambah Buku Baru")
        col1, col2 = st.columns(2)
        
        new_id = col1.text_input("ID Buku (Contoh: B004)")
        new_judul = col2.text_input("Judul Buku")
        new_penulis = col1.text_input("Penulis")
        new_kategori = col2.text_input("Kategori")
        
        submit_tambah = st.form_submit_button("Simpan Buku")
        
        if submit_tambah:
            if new_id and new_judul and new_penulis and new_kategori:
                # Cek apakah ID sudah dipakai
                cek_id = supabase.table("books").select("id_buku").eq("id_buku", new_id).execute()
                
                if len(cek_id.data) > 0:
                    st.error("ID Buku sudah ada! Gunakan ID lain.")
                else:
                    supabase.table("books").insert({
                        "id_buku": new_id,
                        "judul": new_judul,
                        "penulis": new_penulis,
                        "kategori": new_kategori,
                        "status": "Tersedia"
                    }).execute()
                    st.success(f"Buku '{new_judul}' berhasil ditambahkan ke database!")
                    st.rerun()
            else:
                st.error("Mohon isi semua kolom data buku!")
                
    st.divider()
    st.subheader("Database Saat Ini")
    st.dataframe(df_books, use_container_width=True, hide_index=True)
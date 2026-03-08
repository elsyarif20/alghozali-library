import streamlit as st
import pandas as pd
import time
from datetime import datetime
from supabase import create_client, Client

# ==========================================
# 1. KONFIGURASI HALAMAN & KONEKSI SUPABASE
# ==========================================
st.set_page_config(page_title="Al-Ghozali Library App", page_icon="📚", layout="wide")

URL = st.secrets["SUPABASE_URL"]
KEY = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(URL, KEY)

# ==========================================
# 2. FUNGSI DATABASE (CRUD KE SUPABASE)
# ==========================================
def fetch_books():
    response = supabase.table("books").select("*").order("id_buku").execute()
    return pd.DataFrame(response.data)

def fetch_history():
    response = supabase.table("borrow_history").select("*").execute()
    return pd.DataFrame(response.data)

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
    st.markdown("Menebar ilmu dan hikmah melalui literasi Islami untuk para siswa dan santri.")
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
    st.title("Katalog Buku & E-Library")
    
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
            
    st.divider()
    
    if not df_tampil.empty:
        for index, row in df_tampil.iterrows():
            with st.container():
                col_info, col_baca = st.columns([3, 1])
                
                with col_info:
                    st.subheader(row['judul'])
                    st.write(f"✍️ Penulis: **{row['penulis']}** | 🏷️ Kategori: **{row['kategori']}**")
                    st.write(f"Status Fisik: **{row['status']}**")
                
                with col_baca:
                    punya_pdf = pd.notna(row.get('link_pdf')) and row.get('link_pdf') != "" and row.get('link_pdf') is not None
                    
                    if punya_pdf:
                        state_key = f"baca_{row['id_buku']}"
                        if state_key not in st.session_state:
                            st.session_state[state_key] = False
                            
                        if st.button("📖 Baca E-Book", key=f"btn_{row['id_buku']}"):
                            st.session_state[state_key] = not st.session_state[state_key]
                    else:
                        st.button("🚫 PDF Belum Ada", disabled=True, key=f"kosong_{row['id_buku']}")
                
                if punya_pdf and st.session_state.get(f"baca_{row['id_buku']}", False):
                    st.markdown(f"### Membaca: {row['judul']}")
                    st.markdown(f'''
                        <a href="{row["link_pdf"]}" target="_blank" style="text-decoration: none;">
                            <div style="background-color: #4CAF50; color: white; padding: 10px; border-radius: 5px; text-align: center; margin-bottom: 15px; font-weight: bold;">
                                ↗️ Klik di sini untuk Buka PDF Layar Penuh
                            </div>
                        </a>
                    ''', unsafe_allow_html=True)
                    
                    pdf_viewer = f'<iframe src="{row["link_pdf"]}" width="100%" height="800px" style="border: none;"></iframe>'
                    st.markdown(pdf_viewer, unsafe_allow_html=True)
                
                st.divider()
    else:
        st.warning("Buku tidak ditemukan di katalog.")

# ==========================================
# 6. HALAMAN PEMINJAMAN BUKU FISIK
# ==========================================
elif menu == "🤝 Peminjaman":
    st.title("Sistem Peminjaman Buku Fisik")
    
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
                    id_buku = buku_tersedia.loc[buku_tersedia['judul'] == pilihan_buku, 'id_buku'].values[0]
                    supabase.table("books").update({"status": "Dipinjam"}).eq("id_buku", id_buku).execute()
                    
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
                    supabase.table("books").update({"status": "Tersedia"}).eq("id_buku", id_buku).execute()
                    st.success(f"Buku '{pilihan_kembali}' berhasil dikembalikan. Terima kasih!")
                    st.rerun()

# ==========================================
# 7. HALAMAN KELOLA BUKU (ADMIN) - DENGAN FULL CRUD
# ==========================================
elif menu == "⚙️ Kelola Buku (Admin)":
    st.title("Manajemen Koleksi (CRUD)")
    
    # Membuat dua Tab: Satu untuk Tambah, Satu untuk Edit/Hapus
    tab_tambah, tab_edit = st.tabs(["➕ Tambah Buku Baru", "✏️ Edit / Hapus Buku"])
    
    # ---------------- TAB 1: TAMBAH BUKU ----------------
    with tab_tambah:
        with st.form("form_tambah_buku", clear_on_submit=True):
            st.subheader("Formulir Tambah Buku")
            col1, col2 = st.columns(2)
            
            new_id = col1.text_input("ID Buku (Contoh: B005)")
            new_judul = col2.text_input("Judul Buku")
            new_penulis = col1.text_input("Penulis")
            new_kategori = col2.text_input("Kategori")
            
            st.write("📁 **File E-Book (Opsional)**")
            file_pdf = st.file_uploader("Upload File PDF", type=['pdf'], key="upload_baru")
            
            submit_tambah = st.form_submit_button("Simpan Buku ke Database")
            
            if submit_tambah:
                if new_id and new_judul and new_penulis and new_kategori:
                    cek_id = supabase.table("books").select("id_buku").eq("id_buku", new_id).execute()
                    
                    if len(cek_id.data) > 0:
                        st.error("ID Buku sudah ada! Gunakan ID lain.")
                    else:
                        link_pdf_publik = ""
                        
                        if file_pdf is not None:
                            # Tambahkan timestamp agar nama file selalu unik
                            timestamp = int(time.time())
                            nama_file_unik = f"{new_id}_{timestamp}.pdf"
                            file_bytes = file_pdf.getvalue()
                            
                            try:
                                supabase.storage.from_("buku_pdf").upload(
                                    path=nama_file_unik,
                                    file=file_bytes,
                                    file_options={"content-type": "application/pdf"}
                                )
                                link_pdf_publik = supabase.storage.from_("buku_pdf").get_public_url(nama_file_unik)
                            except Exception as e:
                                st.warning(f"Gagal upload PDF: {e}")
                        
                        supabase.table("books").insert({
                            "id_buku": new_id, "judul": new_judul,
                            "penulis": new_penulis, "kategori": new_kategori,
                            "status": "Tersedia", "link_pdf": link_pdf_publik
                        }).execute()
                        
                        st.success(f"Buku '{new_judul}' berhasil ditambahkan!")
                        st.rerun()
                else:
                    st.error("Mohon isi ID, Judul, Penulis, dan Kategori!")
    
    # ---------------- TAB 2: EDIT / HAPUS BUKU ----------------
    with tab_edit:
        st.subheader("Edit atau Hapus Data Katalog")
        
        if not df_books.empty:
            # Dropdown untuk memilih buku yang mau diedit
            buku_pilihan = st.selectbox("Pilih Judul Buku:", df_books['judul'].tolist())
            
            # Ambil detail buku yang dipilih dari dataframe
            data_buku = df_books[df_books['judul'] == buku_pilihan].iloc[0]
            
            with st.form("form_edit_buku"):
                st.info(f"Mengedit ID Buku: **{data_buku['id_buku']}** (ID tidak bisa diubah)")
                
                col1, col2 = st.columns(2)
                edit_judul = col1.text_input("Judul Buku", value=data_buku['judul'])
                edit_penulis = col2.text_input("Penulis", value=data_buku['penulis'])
                edit_kategori = col1.text_input("Kategori", value=data_buku['kategori'])
                
                # Setting index dropdown status
                index_status = 0 if data_buku['status'] == "Tersedia" else 1
                edit_status = col2.selectbox("Status Ketersediaan", ["Tersedia", "Dipinjam"], index=index_status)
                
                st.markdown("---")
                st.write("📁 **Update E-Book / PDF**")
                st.write("*Biarkan kosong jika tidak ingin mengubah file PDF yang sudah ada.*")
                edit_pdf = st.file_uploader("Upload PDF Pengganti (Opsional)", type=['pdf'], key="upload_edit")
                
                st.markdown("---")
                # Tombol Aksi
                col_btn1, col_btn2 = st.columns(2)
                submit_update = col_btn1.form_submit_button("💾 Simpan Perubahan (Update)", type="primary")
                submit_delete = col_btn2.form_submit_button("🗑️ Hapus Buku Ini")
                
                if submit_update:
                    link_pdf_baru = data_buku['link_pdf'] # Default pakai link lama
                    
                    # Jika admin mengupload PDF baru untuk me-replace yang lama
                    if edit_pdf is not None:
                        timestamp = int(time.time())
                        nama_file_unik = f"{data_buku['id_buku']}_update_{timestamp}.pdf"
                        file_bytes = edit_pdf.getvalue()
                        
                        try:
                            supabase.storage.from_("buku_pdf").upload(
                                path=nama_file_unik, file=file_bytes,
                                file_options={"content-type": "application/pdf"}
                            )
                            link_pdf_baru = supabase.storage.from_("buku_pdf").get_public_url(nama_file_unik)
                        except Exception as e:
                            st.warning(f"Gagal update PDF: {e}")
                    
                    # Update database Supabase
                    supabase.table("books").update({
                        "judul": edit_judul,
                        "penulis": edit_penulis,
                        "kategori": edit_kategori,
                        "status": edit_status,
                        "link_pdf": link_pdf_baru
                    }).eq("id_buku", data_buku['id_buku']).execute()
                    
                    st.success(f"Buku '{edit_judul}' berhasil diperbarui!")
                    st.rerun()
                    
                if submit_delete:
                    # Menghapus dari Supabase
                    supabase.table("books").delete().eq("id_buku", data_buku['id_buku']).execute()
                    st.success(f"Buku '{buku_pilihan}' berhasil dihapus secara permanen!")
                    st.rerun()
        else:
            st.warning("Belum ada buku di database.")
            
    # Tampilkan database real-time di bagian bawah
    st.divider()
    st.subheader("Database Katalog Saat Ini")
    st.dataframe(df_books, use_container_width=True, hide_index=True)

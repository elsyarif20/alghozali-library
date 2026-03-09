import streamlit as st
import pandas as pd
import time
from datetime import datetime
from supabase import create_client, Client

# ==========================================
# 1. KONFIGURASI HALAMAN & TEMA MODERN
# ==========================================
st.set_page_config(page_title="Perpustakaan Al-Ghozali", page_icon="📚", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    div[data-testid="metric-container"] {
        background-color: #ffffff; border: 1px solid #e0e0e0;
        border-radius: 10px; padding: 20px; box-shadow: 2px 2px 10px rgba(0,0,0,0.05);
    }
    .stButton>button { border-radius: 8px; font-weight: bold; transition: 0.3s; }
    .stButton>button:hover { transform: scale(1.02); }
    </style>
""", unsafe_allow_html=True)

URL = st.secrets["SUPABASE_URL"]
KEY = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(URL, KEY)

# ==========================================
# 2. STATE MANAGEMENT (SISTEM LOGIN)
# ==========================================
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['role'] = None
    st.session_state['username'] = None
    st.session_state['nama'] = None

# ==========================================
# 3. FUNGSI DATABASE
# ==========================================
@st.cache_data(ttl=5)
def fetch_books():
    response = supabase.table("books").select("*").order("id_buku").execute()
    return pd.DataFrame(response.data)

def fetch_users():
    response = supabase.table("users").select("*").execute()
    return pd.DataFrame(response.data)

df_books = fetch_books()

# ==========================================
# 4. HALAMAN AUTENTIKASI (LOGIN & SIGN UP)
# ==========================================
if not st.session_state['logged_in']:
    col_kosong1, col_tengah, col_kosong2 = st.columns([1, 2, 1])
    
    with col_tengah:
        st.image("https://cdn-icons-png.flaticon.com/512/2232/2232688.png", width=100)
        st.title("Portal Perpustakaan")
        st.caption("Silakan masuk atau daftar untuk mengakses koleksi Al-Ghozali Library.")
        
        tab_login, tab_daftar = st.tabs(["🔑 Sign In", "📝 Sign Up (Siswa)"])
        
        # --- TAB LOGIN ---
        with tab_login:
            with st.form("form_login", border=True):
                login_user = st.text_input("Username")
                login_pass = st.text_input("Password", type="password")
                btn_login = st.form_submit_button("Masuk Aplikasi", type="primary", use_container_width=True)
                
                if btn_login:
                    if login_user and login_pass:
                        # Cek ke database Supabase
                        cek_user = supabase.table("users").select("*").eq("username", login_user).eq("password", login_pass).execute()
                        
                        if len(cek_user.data) > 0:
                            data_akun = cek_user.data[0]
                            st.session_state['logged_in'] = True
                            st.session_state['role'] = data_akun['role']
                            st.session_state['username'] = data_akun['username']
                            st.session_state['nama'] = data_akun['nama']
                            st.success(f"Berhasil masuk! Selamat datang, {data_akun['nama']}.")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("Username atau Password salah!")
                    else:
                        st.warning("Harap isi username dan password.")
                        
        # --- TAB SIGN UP ---
        with tab_daftar:
            with st.form("form_signup", border=True, clear_on_submit=True):
                st.info("Formulir pendaftaran khusus untuk Siswa/Santri.")
                reg_nama = st.text_input("Nama Lengkap")
                
                col_reg1, col_reg2 = st.columns(2)
                reg_jenjang = col_reg1.selectbox("Jenjang Pendidikan", ["SMP", "SMA"])
                reg_kelas = col_reg2.text_input("Kelas (Contoh: X IPA 1)")
                
                st.markdown("---")
                reg_user = st.text_input("Buat Username (Tanpa spasi)")
                reg_pass = st.text_input("Buat Password", type="password")
                
                btn_daftar = st.form_submit_button("Daftarkan Akun", type="primary", use_container_width=True)
                
                if btn_daftar:
                    if reg_nama and reg_jenjang and reg_kelas and reg_user and reg_pass:
                        # Cek apakah username sudah dipakai
                        cek_username = supabase.table("users").select("username").eq("username", reg_user).execute()
                        if len(cek_username.data) > 0:
                            st.error("Username sudah terdaftar! Silakan gunakan username lain.")
                        else:
                            # Simpan ke database
                            supabase.table("users").insert({
                                "username": reg_user.replace(" ", ""),
                                "password": reg_pass,
                                "role": "user",
                                "nama": reg_nama,
                                "jenjang": reg_jenjang,
                                "kelas": reg_kelas
                            }).execute()
                            st.success("Akun berhasil dibuat! Silakan masuk melalui tab 'Sign In'.")
                    else:
                        st.warning("Harap lengkapi seluruh formulir pendaftaran.")

# ==========================================
# 5. APLIKASI UTAMA (SETELAH LOGIN)
# ==========================================
else:
    # --- NAVIGASI SIDEBAR BERDASARKAN ROLE ---
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/2232/2232688.png", width=120)
        st.title("Al-Ghozali Digital Library")
        st.caption(f"Masuk sebagai: **{st.session_state['nama']}** ({st.session_state['role'].upper()})")
        st.divider()
        
        # Penyesuaian Menu
        if st.session_state['role'] == 'admin':
            menu_options = ["🏠 Dashboard Beranda", "🔍 E-Katalog & Baca", "🤝 Sirkulasi (Pinjam/Kembali)", "⚙️ Panel Admin"]
        else:
            # Menu khusus User (Siswa)
            menu_options = ["🏠 Dashboard Beranda", "🔍 E-Katalog & Baca"]
            
        menu = st.radio("📌 MENU UTAMA", menu_options)
        
        st.divider()
        # Tombol Logout
        if st.button("🚪 Keluar (Logout)", use_container_width=True):
            st.session_state['logged_in'] = False
            st.session_state['role'] = None
            st.session_state['username'] = None
            st.session_state['nama'] = None
            st.rerun()

    # --- KONTEN HALAMAN (Sama seperti sebelumnya) ---
    
    # 5.A. BERANDA
    if menu == "🏠 Dashboard Beranda":
        st.header(f"Ahlan wa Sahlan, {st.session_state['nama']}! 📚")
        st.markdown("Menebar ilmu dan hikmah melalui literasi Islami. Jelajahi ribuan koleksi buku fisik dan e-book kami.")
        st.write("")
        
        col1, col2, col3 = st.columns(3)
        total_buku = len(df_books)
        buku_tersedia = len(df_books[df_books['status'] == 'Tersedia']) if total_buku > 0 else 0
        buku_dipinjam = total_buku - buku_tersedia
        
        col1.metric("📚 Total Koleksi Buku", total_buku)
        col2.metric("✅ Tersedia di Rak", buku_tersedia)
        col3.metric("🤝 Sedang Dipinjam", buku_dipinjam)
        
        st.divider()
        st.subheader("🌟 Koleksi Terbaru")
        if not df_books.empty:
            highlight_books = df_books.tail(4)
            cols = st.columns(4)
            for i, (index, row) in enumerate(highlight_books.iterrows()):
                with cols[i % 4]:
                    with st.container(border=True):
                        cover = row.get('cover_url')
                        if pd.notna(cover) and cover != "":
                            st.image(cover, use_container_width=True)
                        else:
                            st.image("https://via.placeholder.com/150x200.png?text=No+Cover", use_container_width=True)
                        st.markdown(f"**{row['judul']}**")
                        st.caption(row['penulis'])
        else:
            st.info("Belum ada koleksi buku yang ditambahkan.")

    # 5.B. KATALOG & BACA
    elif menu == "🔍 E-Katalog & Baca":
        st.header("🔍 Eksplorasi Katalog Buku")
        
        with st.container(border=True):
            col_search, col_filter = st.columns([2, 1])
            search_query = col_search.text_input("Pencarian:", placeholder="Ketik judul buku...")
            
            kategori_list = ["Semua Kategori"]
            if not df_books.empty:
                kategori_list += list(df_books['kategori'].unique())
            filter_kategori = col_filter.selectbox("Filter Kategori:", kategori_list)
        
        df_tampil = df_books.copy()
        if not df_tampil.empty:
            if search_query:
                df_tampil = df_tampil[df_tampil['judul'].str.contains(search_query, case=False)]
            if filter_kategori != "Semua Kategori":
                df_tampil = df_tampil[df_tampil['kategori'] == filter_kategori]
                
        st.write("")
        
        if not df_tampil.empty:
            grid_cols = st.columns(3)
            for index, row in df_tampil.iterrows():
                col = grid_cols[index % 3] 
                
                with col:
                    with st.container(border=True):
                        cover = row.get('cover_url')
                        if pd.notna(cover) and cover != "":
                            st.image(cover, use_container_width=True)
                        else:
                            st.image("https://via.placeholder.com/300x400.png?text=No+Cover", use_container_width=True)
                        
                        st.subheader(row['judul'])
                        st.caption(f"✍️ {row['penulis']} | 🏷️ {row['kategori']}")
                        
                        if row['status'] == 'Tersedia':
                            st.success("Tersedia di Rak Fisik")
                        else:
                            st.error("Sedang Dipinjam")
                        
                        with st.expander("📖 Detail & Baca E-Book"):
                            st.write("**Sinopsis:**")
                            sinopsis = row.get('sinopsis')
                            if pd.notna(sinopsis) and sinopsis != "":
                                st.write(sinopsis)
                            else:
                                st.write("*Sinopsis belum tersedia.*")
                                
                            pdf_link = row.get('link_pdf')
                            if pd.notna(pdf_link) and pdf_link != "":
                                st.markdown(f'''
                                    <a href="{pdf_link}" target="_blank" style="text-decoration: none;">
                                        <div style="background-color: #008CBA; color: white; padding: 10px; border-radius: 5px; text-align: center; font-weight: bold; margin-top:10px;">
                                            ↗️ BUKA PDF E-BOOK
                                        </div>
                                    </a>
                                ''', unsafe_allow_html=True)
                            else:
                                st.warning("E-Book PDF tidak tersedia.")
        else:
            st.warning("Buku yang Anda cari tidak ditemukan.")

    # 5.C. SIRKULASI (KHUSUS ADMIN)
    elif menu == "🤝 Sirkulasi (Pinjam/Kembali)" and st.session_state['role'] == 'admin':
        st.header("Sistem Sirkulasi Perpustakaan")
        tab_pinjam, tab_kembali = st.tabs(["📤 Pinjam Buku Fisik", "📥 Pengembalian Buku"])
        
        with tab_pinjam:
            buku_tersedia = df_books[df_books['status'] == 'Tersedia'] if not df_books.empty else pd.DataFrame()
            with st.form("form_pinjam", border=True):
                nama_peminjam = st.text_input("👤 Nama Lengkap Siswa/Peminjam")
                pilihan_buku = st.selectbox("📚 Pilih Buku yang Tersedia", buku_tersedia['judul'].tolist() if not buku_tersedia.empty else ["Tidak ada buku tersedia"])
                submit_pinjam = st.form_submit_button("Catat Peminjaman", type="primary")
                
                if submit_pinjam:
                    if nama_peminjam and pilihan_buku != "Tidak ada buku tersedia":
                        id_buku = buku_tersedia.loc[buku_tersedia['judul'] == pilihan_buku, 'id_buku'].values[0]
                        supabase.table("books").update({"status": "Dipinjam"}).eq("id_buku", id_buku).execute()
                        supabase.table("borrow_history").insert({
                            "nama_peminjam": nama_peminjam, "id_buku": id_buku,
                            "tanggal_pinjam": datetime.now().strftime("%Y-%m-%d"), "status": "Dipinjam"
                        }).execute()
                        st.success(f"Berhasil! Buku dipinjam oleh {nama_peminjam}.")
                        time.sleep(1)
                        st.rerun()
                        
        with tab_kembali:
            buku_dipinjam = df_books[df_books['status'] == 'Dipinjam'] if not df_books.empty else pd.DataFrame()
            with st.form("form_kembali", border=True):
                pilihan_kembali = st.selectbox("📚 Pilih Buku yang Dikembalikan", buku_dipinjam['judul'].tolist() if not buku_dipinjam.empty else ["Tidak ada buku dipinjam"])
                submit_kembali = st.form_submit_button("Proses Pengembalian", type="primary")
                
                if submit_kembali:
                    if pilihan_kembali != "Tidak ada buku dipinjam":
                        id_buku = buku_dipinjam.loc[buku_dipinjam['judul'] == pilihan_kembali, 'id_buku'].values[0]
                        supabase.table("books").update({"status": "Tersedia"}).eq("id_buku", id_buku).execute()
                        st.success("Buku berhasil dikembalikan ke rak.")
                        time.sleep(1)
                        st.rerun()

    # 5.D. PANEL ADMIN (KHUSUS ADMIN)
    elif menu == "⚙️ Panel Admin" and st.session_state['role'] == 'admin':
        st.header("Panel Administrator")
        tab_tambah, tab_edit = st.tabs(["➕ Tambah Koleksi Baru", "✏️ Edit / Hapus Koleksi"])
        
        with tab_tambah:
            with st.form("form_tambah_buku", border=True, clear_on_submit=True):
                col1, col2 = st.columns(2)
                new_id = col1.text_input("🔑 ID Buku (Contoh: B001)")
                new_judul = col2.text_input("📖 Judul Buku")
                new_penulis = col1.text_input("✍️ Penulis")
                new_kategori = col2.text_input("🏷️ Kategori")
                new_sinopsis = st.text_area("📝 Sinopsis Singkat", height=100)
                
                col_file1, col_file2 = st.columns(2)
                file_cover = col_file1.file_uploader("🖼️ Upload Cover (JPG/PNG)", type=['jpg', 'jpeg', 'png'])
                file_pdf = col_file2.file_uploader("📁 Upload E-Book (PDF)", type=['pdf'])
                
                submit_tambah = st.form_submit_button("Simpan Data Buku", type="primary")
                
                if submit_tambah:
                    if new_id and new_judul and new_penulis and new_kategori:
                        cek_id = supabase.table("books").select("id_buku").eq("id_buku", new_id).execute()
                        if len(cek_id.data) > 0:
                            st.error("ID Buku sudah ada!")
                        else:
                            link_pdf_publik, link_cover_publik = "", ""
                            timestamp = int(time.time())
                            
                            if file_pdf is not None:
                                try:
                                    nama_pdf = f"{new_id}_{timestamp}.pdf"
                                    supabase.storage.from_("buku_pdf").upload(nama_pdf, file_pdf.getvalue(), file_options={"content-type": "application/pdf"})
                                    link_pdf_publik = supabase.storage.from_("buku_pdf").get_public_url(nama_pdf)
                                except Exception: pass
                                    
                            if file_cover is not None:
                                try:
                                    nama_cov = f"{new_id}_{timestamp}.png"
                                    supabase.storage.from_("buku_cover").upload(nama_cov, file_cover.getvalue(), file_options={"content-type": file_cover.type})
                                    link_cover_publik = supabase.storage.from_("buku_cover").get_public_url(nama_cov)
                                except Exception: pass
                            
                            supabase.table("books").insert({
                                "id_buku": new_id, "judul": new_judul, "penulis": new_penulis, 
                                "kategori": new_kategori, "status": "Tersedia", 
                                "link_pdf": link_pdf_publik, "sinopsis": new_sinopsis, "cover_url": link_cover_publik
                            }).execute()
                            st.success("Koleksi baru berhasil ditambahkan!")
                            time.sleep(1)
                            st.rerun()
                            
        with tab_edit:
            if not df_books.empty:
                buku_pilihan = st.selectbox("Pilih Buku yang akan diedit:", df_books['judul'].tolist())
                data_buku = df_books[df_books['judul'] == buku_pilihan].iloc[0]
                
                with st.form("form_edit_buku", border=True):
                    col1, col2 = st.columns(2)
                    edit_judul = col1.text_input("Judul Buku", value=data_buku['judul'])
                    edit_penulis = col2.text_input("Penulis", value=data_buku['penulis'])
                    edit_kategori = col1.text_input("Kategori", value=data_buku['kategori'])
                    
                    index_status = 0 if data_buku['status'] == "Tersedia" else 1
                    edit_status = col2.selectbox("Status Fisik", ["Tersedia", "Dipinjam"], index=index_status)
                    
                    isi_sinopsis = data_buku.get('sinopsis', '')
                    if pd.isna(isi_sinopsis): isi_sinopsis = ''
                    edit_sinopsis = st.text_area("Sinopsis Buku", value=isi_sinopsis, height=100)
                    
                    col_up1, col_up2 = st.columns(2)
                    edit_cover = col_up1.file_uploader("Timpa Cover Lama", type=['jpg', 'jpeg', 'png'])
                    edit_pdf = col_up2.file_uploader("Timpa PDF Lama", type=['pdf'])
                    
                    col_btn1, col_btn2 = st.columns(2)
                    submit_update = col_btn1.form_submit_button("💾 Simpan Perubahan", type="primary")
                    submit_delete = col_btn2.form_submit_button("🗑️ Hapus Buku Ini")
                    
                    if submit_update:
                        link_pdf_baru = data_buku.get('link_pdf', '')
                        link_cover_baru = data_buku.get('cover_url', '')
                        timestamp = int(time.time())
                        
                        if edit_pdf is not None:
                            try:
                                n_pdf = f"{data_buku['id_buku']}_up_{timestamp}.pdf"
                                supabase.storage.from_("buku_pdf").upload(n_pdf, edit_pdf.getvalue(), file_options={"content-type": "application/pdf"})
                                link_pdf_baru = supabase.storage.from_("buku_pdf").get_public_url(n_pdf)
                            except Exception: pass
                                
                        if edit_cover is not None:
                            try:
                                n_cov = f"{data_buku['id_buku']}_up_{timestamp}.png"
                                supabase.storage.from_("buku_cover").upload(n_cov, edit_cover.getvalue(), file_options={"content-type": edit_cover.type})
                                link_cover_baru = supabase.storage.from_("buku_cover").get_public_url(n_cov)
                            except Exception: pass
                        
                        supabase.table("books").update({
                            "judul": edit_judul, "penulis": edit_penulis, "kategori": edit_kategori, 
                            "status": edit_status, "sinopsis": edit_sinopsis,
                            "link_pdf": link_pdf_baru, "cover_url": link_cover_baru
                        }).eq("id_buku", data_buku['id_buku']).execute()
                        st.success("Perubahan berhasil disimpan!")
                        time.sleep(1)
                        st.rerun()
                        
                    if submit_delete:
                        supabase.table("books").delete().eq("id_buku", data_buku['id_buku']).execute()
                        st.success("Buku berhasil dihapus.")
                        time.sleep(1)
                        st.rerun()

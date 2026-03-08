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
# 2. FUNGSI DATABASE
# ==========================================
def fetch_books():
    response = supabase.table("books").select("*").order("id_buku").execute()
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
# 5. HALAMAN KATALOG BUKU (UI BARU DENGAN SINOPSIS & COVER)
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
                # Tampilan utama: Cover kecil di kiri, Info di kanan
                col_img, col_info = st.columns([1, 5])
                
                with col_img:
                    if pd.notna(row.get('cover_url')) and row.get('cover_url') != "":
                        st.image(row['cover_url'], use_container_width=True)
                    else:
                        st.image("https://via.placeholder.com/150x200.png?text=No+Cover", use_container_width=True)
                        
                with col_info:
                    st.subheader(row['judul'])
                    st.write(f"✍️ **Penulis:** {row['penulis']} | 🏷️ **Kategori:** {row['kategori']}")
                    st.write(f"Status Fisik: **{row['status']}**")
                    
                    # Dropdown Expander untuk melihat sinopsis dan baca buku
                    with st.expander("📖 Lihat Sinopsis & Baca Buku"):
                        st.write("**Sinopsis:**")
                        sinopsis_teks = row.get('sinopsis')
                        if pd.notna(sinopsis_teks) and sinopsis_teks != "":
                            st.write(sinopsis_teks)
                        else:
                            st.write("*Sinopsis belum tersedia untuk buku ini.*")
                        
                        st.markdown("---")
                        punya_pdf = pd.notna(row.get('link_pdf')) and row.get('link_pdf') != ""
                        
                        if punya_pdf:
                            st.success("Buku Digital (PDF) Tersedia!")
                            # Tombol utama untuk baca di tab baru (Solusi layar blank)
                            st.markdown(f'''
                                <a href="{row["link_pdf"]}" target="_blank" style="text-decoration: none;">
                                    <div style="background-color: #4CAF50; color: white; padding: 12px; border-radius: 8px; text-align: center; font-weight: bold; font-size: 16px;">
                                        ↗️ BACA BUKU (Buka PDF Layar Penuh)
                                    </div>
                                </a>
                            ''', unsafe_allow_html=True)
                            
                            st.caption("Jika bingkai di bawah ini putih/blank, gunakan tombol hijau di atas.")
                            # Alternatif embed menggunakan tag <embed> yang terkadang lebih stabil dari iframe
                            pdf_viewer = f'<embed src="{row["link_pdf"]}#toolbar=0" width="100%" height="600px" type="application/pdf">'
                            st.markdown(pdf_viewer, unsafe_allow_html=True)
                        else:
                            st.warning("🚫 File PDF E-Book belum tersedia untuk buku ini.")
                            
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
                    st.success(f"Buku '{pilihan_kembali}' berhasil dikembalikan.")
                    st.rerun()

# ==========================================
# 7. HALAMAN KELOLA BUKU (ADMIN)
# ==========================================
elif menu == "⚙️ Kelola Buku (Admin)":
    st.title("Manajemen Koleksi (CRUD)")
    
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
            
            new_sinopsis = st.text_area("Sinopsis Buku", height=100)
            
            st.markdown("---")
            col_file1, col_file2 = st.columns(2)
            file_cover = col_file1.file_uploader("🖼️ Upload Cover Buku (JPG/PNG)", type=['jpg', 'jpeg', 'png'])
            file_pdf = col_file2.file_uploader("📁 Upload File E-Book (PDF)", type=['pdf'])
            
            submit_tambah = st.form_submit_button("Simpan Buku ke Database")
            
            if submit_tambah:
                if new_id and new_judul and new_penulis and new_kategori:
                    cek_id = supabase.table("books").select("id_buku").eq("id_buku", new_id).execute()
                    
                    if len(cek_id.data) > 0:
                        st.error("ID Buku sudah ada! Gunakan ID lain.")
                    else:
                        link_pdf_publik = ""
                        link_cover_publik = ""
                        timestamp = int(time.time())
                        
                        # Upload PDF
                        if file_pdf is not None:
                            nama_file_pdf = f"{new_id}_{timestamp}.pdf"
                            try:
                                supabase.storage.from_("buku_pdf").upload(nama_file_pdf, file_pdf.getvalue(), file_options={"content-type": "application/pdf"})
                                link_pdf_publik = supabase.storage.from_("buku_pdf").get_public_url(nama_file_pdf)
                            except Exception as e:
                                st.warning(f"Gagal upload PDF: {e}")
                                
                        # Upload Cover
                        if file_cover is not None:
                            nama_file_cover = f"{new_id}_{timestamp}_{file_cover.name}".replace(" ", "_")
                            try:
                                supabase.storage.from_("buku_cover").upload(nama_file_cover, file_cover.getvalue(), file_options={"content-type": file_cover.type})
                                link_cover_publik = supabase.storage.from_("buku_cover").get_public_url(nama_file_cover)
                            except Exception as e:
                                st.warning(f"Gagal upload Cover: {e}")
                        
                        # Simpan ke Database
                        supabase.table("books").insert({
                            "id_buku": new_id, "judul": new_judul,
                            "penulis": new_penulis, "kategori": new_kategori,
                            "status": "Tersedia", "link_pdf": link_pdf_publik,
                            "sinopsis": new_sinopsis, "cover_url": link_cover_publik
                        }).execute()
                        
                        st.success(f"Buku '{new_judul}' berhasil ditambahkan!")
                        st.rerun()
                else:
                    st.error("Mohon isi ID, Judul, Penulis, dan Kategori!")
    
    # ---------------- TAB 2: EDIT / HAPUS BUKU ----------------
    with tab_edit:
        st.subheader("Edit atau Hapus Data Katalog")
        
        if not df_books.empty:
            buku_pilihan = st.selectbox("Pilih Judul Buku:", df_books['judul'].tolist())
            data_buku = df_books[df_books['judul'] == buku_pilihan].iloc[0]
            
            with st.form("form_edit_buku"):
                st.info(f"Mengedit ID Buku: **{data_buku['id_buku']}**")
                
                col1, col2 = st.columns(2)
                edit_judul = col1.text_input("Judul Buku", value=data_buku['judul'])
                edit_penulis = col2.text_input("Penulis", value=data_buku['penulis'])
                edit_kategori = col1.text_input("Kategori", value=data_buku['kategori'])
                
                index_status = 0 if data_buku['status'] == "Tersedia" else 1
                edit_status = col2.selectbox("Status Ketersediaan", ["Tersedia", "Dipinjam"], index=index_status)
                
                # Menggunakan fungsi get() dengan nilai default kosong jika kolom belum ada di baris tersebut
                isi_sinopsis = data_buku.get('sinopsis', '')
                if pd.isna(isi_sinopsis): isi_sinopsis = ''
                edit_sinopsis = st.text_area("Sinopsis Buku", value=isi_sinopsis, height=100)
                
                st.markdown("---")
                st.write("*Biarkan kosong jika tidak ingin mengubah Cover/PDF yang lama.*")
                col_up1, col_up2 = st.columns(2)
                edit_cover = col_up1.file_uploader("Ganti Cover (Opsional)", type=['jpg', 'jpeg', 'png'], key="edit_cover")
                edit_pdf = col_up2.file_uploader("Ganti PDF (Opsional)", type=['pdf'], key="edit_pdf")
                
                st.markdown("---")
                col_btn1, col_btn2 = st.columns(2)
                submit_update = col_btn1.form_submit_button("💾 Simpan Perubahan", type="primary")
                submit_delete = col_btn2.form_submit_button("🗑️ Hapus Buku Ini")
                
                if submit_update:
                    link_pdf_baru = data_buku.get('link_pdf', '')
                    link_cover_baru = data_buku.get('cover_url', '')
                    timestamp = int(time.time())
                    
                    if edit_pdf is not None:
                        nama_file_pdf = f"{data_buku['id_buku']}_update_{timestamp}.pdf"
                        try:
                            supabase.storage.from_("buku_pdf").upload(nama_file_pdf, edit_pdf.getvalue(), file_options={"content-type": "application/pdf"})
                            link_pdf_baru = supabase.storage.from_("buku_pdf").get_public_url(nama_file_pdf)
                        except Exception as e: pass
                            
                    if edit_cover is not None:
                        nama_file_cover = f"{data_buku['id_buku']}_update_{timestamp}_{edit_cover.name}".replace(" ", "_")
                        try:
                            supabase.storage.from_("buku_cover").upload(nama_file_cover, edit_cover.getvalue(), file_options={"content-type": edit_cover.type})
                            link_cover_baru = supabase.storage.from_("buku_cover").get_public_url(nama_file_cover)
                        except Exception as e: pass
                    
                    supabase.table("books").update({
                        "judul": edit_judul, "penulis": edit_penulis,
                        "kategori": edit_kategori, "status": edit_status,
                        "sinopsis": edit_sinopsis,
                        "link_pdf": link_pdf_baru, "cover_url": link_cover_baru
                    }).eq("id_buku", data_buku['id_buku']).execute()
                    
                    st.success(f"Buku '{edit_judul}' berhasil diperbarui!")
                    st.rerun()
                    
                if submit_delete:
                    supabase.table("books").delete().eq("id_buku", data_buku['id_buku']).execute()
                    st.success(f"Buku '{buku_pilihan}' berhasil dihapus secara permanen!")
                    st.rerun()
        else:
            st.warning("Belum ada buku di database.")

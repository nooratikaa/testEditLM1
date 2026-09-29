# Meja HR — Panduan pemasangan

Meja HR ialah web app. Ia dibuka dalam pelayar (Chrome atau Safari) di komputer atau telefon, dan boleh disimpan ke skrin utama telefon seperti app. Ia tidak perlu dipasang dari Play Store atau App Store.

| Peranan | Boleh lihat | Boleh buat |
|---|---|---|
| **Staf** | Data diri sendiri sahaja: baki cuti, permohonan cuti, kehadiran, target, amaran | Mohon cuti, ubah atau batal permohonan yang masih menunggu, tukar kata laluan |
| **Boss** | Semua pekerja | Lulus atau tolak cuti |
| **HR** | Semua pekerja | Semua perkara: pekerja, jawatan, kehadiran, target, amaran, tetapan |

Sekatan ini dikuatkuasakan oleh **pangkalan data** (Row Level Security dalam Supabase), bukan oleh paparan sahaja. Staf tidak boleh melihat data orang lain walaupun mereka cuba mengubah kod halaman.

Kos: **RM0** untuk syarikat bawah 20 orang (pelan percuma Supabase dan Netlify).

---

## Langkah 1: Cipta pangkalan data (Supabase), ~10 minit

1. Pergi ke **https://supabase.com**, tekan **Start your project** dan daftar (boleh guna akaun Google atau GitHub).
2. Tekan **New project**:
   - **Name**: `meja-hr`
   - **Database password**: pilih kata laluan yang kuat dan simpan (jarang diperlukan).
   - **Region**: **Southeast Asia (Singapore)**
   - Tekan **Create new project** dan tunggu ~2 minit.
3. Di menu kiri, buka **SQL Editor**, kemudian tekan **New query**.
4. Buka fail `supabase/schema.sql`, salin **semua** kandungannya, tampal ke dalam editor dan tekan **Run**.
5. Di bawah, keluar satu jadual kecil berisi **No. staf `HR001`** dan **Kod aktivasi** (6 aksara). **Salin kod ini.** Anda akan menggunakannya untuk log masuk kali pertama.
   > Terlupa kod? Jalankan query ini: `select staff_no, activation_code from employees where role = 'hr';`
6. Di menu kiri, buka **Authentication**, kemudian **Sign In / Providers**, kemudian **Email**:
   - Pastikan **Enable Email provider** dihidupkan.
   - **Matikan "Confirm email"** dan tekan **Save**.
   (Staf log masuk dengan no. staf, jadi tiada e-mel pengesahan dihantar.)
7. Di menu kiri, buka **Project Settings**, kemudian **API** (atau **Data API** / **API Keys**). Salin dua perkara:
   - **Project URL**, contohnya `https://abcdefgh.supabase.co`
   - Kunci **anon public**, iaitu teks panjang bermula dengan `eyJ...`

## Langkah 2: Isi `config.js`

Buka fail `config.js` dengan Notepad dan isi:

```js
window.MEJAHR_CONFIG = {
  url: 'https://abcdefgh.supabase.co',      // Project URL anda
  anonKey: 'eyJhbGciOi...',                  // kunci anon public anda
  emailDomain: 'staf.syarikatanda.com.my',  // domain syarikat anda (tiada e-mel dihantar)
  company: 'Syarikat Anda Sdn. Bhd.',       // nama di skrin log masuk
};
```

> Kunci **anon public** memang selamat untuk berada dalam halaman web. **Jangan sekali-kali** masukkan kunci **service_role** di sini.

## Langkah 3: Letak web app di internet (Netlify), ~3 minit

1. Pergi ke **https://app.netlify.com/drop** dan daftar akaun percuma.
2. **Seret keseluruhan folder `web`** (yang mengandungi `index.html`, `config.js`, `vendor/`, dan lain-lain) ke dalam kotak di halaman itu.
3. Netlify memberi pautan seperti `https://nama-rawak.netlify.app`. Anda boleh menukar nama di **Site configuration → Change site name**, contohnya `https://mejahr-syarikatanda.netlify.app`.
4. Setiap kali ada versi baharu `index.html` atau anda mengubah `config.js`, buka site itu di Netlify → **Deploys**, kemudian seret folder `web` sekali lagi.

## Langkah 4: Log masuk kali pertama sebagai HR

1. Buka pautan Netlify anda.
2. Tekan **Kali pertama? Aktifkan akaun**.
3. Isi no. staf `HR001`, kod aktivasi dari Langkah 1.5, dan kata laluan baharu (sekurang-kurangnya 8 aksara).
4. Buka **Akaun Saya** dan semak nama anda. Untuk menukar nama atau no. staf, buka **Pekerja**, kemudian rekod `HR001`, kemudian **Buka**.

## Langkah 5: Sediakan syarikat

1. **Tetapan**: nama syarikat, hari bekerja, cuti umum negeri anda dan had amaran.
2. **Jawatan**: contohnya *Eksekutif Jualan*, 14 hari cuti tahunan, target RM 30,000.
3. **Pekerja**, kemudian **Tambah pekerja**, untuk setiap staf:
   - Pilih **Peranan**: *Staf*, *Boss* atau *HR*.
   - Isi jenis gaji dan gaji pokok jika mahu anggaran gaji dalam Kehadiran.
   - Selepas disimpan, lajur **Log masuk** menunjukkan **kod aktivasi** untuk staf itu.
4. Beri setiap staf **pautan app + no. staf + kod aktivasi** mereka (contohnya melalui WhatsApp peribadi).

## Untuk staf

1. Buka pautan dan tekan **Kali pertama? Aktifkan akaun**.
2. Masukkan no. staf, kod aktivasi, dan pilih kata laluan sendiri.
3. Simpan ke skrin utama telefon:
   - **Android (Chrome)**: menu ⋮, kemudian **Add to Home screen** / **Install app**
   - **iPhone (Safari)**: butang Kongsi, kemudian **Add to Home Screen**
4. Selepas itu, log masuk dengan no. staf dan kata laluan sahaja.

## Staf lupa kata laluan

HR buka **Pekerja**, kemudian rekod staf, kemudian **Buka**, kemudian **Tetapkan semula (lupa kata laluan)**. Satu kod aktivasi baharu dijana. Staf aktifkan semula akaun dengan kod itu dan pilih kata laluan baharu.

## Perkara penting

- **Projek percuma Supabase akan "tidur" jika tiada sesiapa menggunakannya selama 7 hari.** Jika app tidak dapat dibuka selepas cuti panjang, log masuk ke supabase.com dan tekan **Restore project**. Penggunaan harian menghalang perkara ini berlaku.
- **Salinan data**: pelan percuma tidak menyimpan salinan automatik yang boleh dipulihkan. HR disyorkan **Eksport CSV** kehadiran setiap bulan. Untuk salinan penuh, naik taraf ke pelan Pro Supabase (USD 25 sebulan).
- **Anggaran gaji** dalam Kehadiran hanyalah panduan (gaji ÷ 26 × hari tak dibayar). Semak sebelum membuat bayaran.
- Pekerja yang berhenti: tukar **Status** kepada *Berhenti*. Jangan padam, supaya sejarah cuti dan amaran kekal.
- Jika log masuk menunjukkan ralat *"email invalid"*, tukar `emailDomain` dalam `config.js` kepada domain sebenar syarikat anda, kemudian muat naik semula.

## Fail dalam folder ini

| Fail | Kegunaan |
|---|---|
| `index.html` | Web app |
| `config.js` | Sambungan ke Supabase anda (**perlu diisi**) |
| `vendor/` | Pustaka Supabase (jangan ubah) |
| `supabase/schema.sql` | Jadual dan peraturan keselamatan (jalankan sekali) |
| `manifest.webmanifest`, `icon.*` | Ikon apabila disimpan ke skrin utama telefon |

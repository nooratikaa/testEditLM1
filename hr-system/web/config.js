// Tetapan sambungan Meja HR — isi selepas mencipta projek Supabase (lihat PANDUAN.md).
// Kunci "anon" ini memang direka untuk berada dalam pelayar; keselamatan data dijaga
// oleh peraturan dalam pangkalan data (schema.sql), bukan oleh kerahsiaan kunci ini.
window.MEJAHR_CONFIG = {
  url: 'https://xxxx.supabase.co',          // Project Settings → API → Project URL
  anonKey: 'TAMPAL_ANON_PUBLIC_KEY_DI_SINI', // Project Settings → API → anon public
  emailDomain: 'staf.syarikatanda.com.my',  // domain syarikat anda; tiada e-mel dihantar ke sini
  company: 'Syarikat Anda Sdn. Bhd.',       // dipaparkan di skrin log masuk
};

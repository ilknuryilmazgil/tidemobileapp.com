"""index.html (TR) dosyasından index-en.html (EN) üretir.

Her çeviri parçası birebir aranır; bulunamayan parça olursa betik durur.
Ayrıca iki sayfanın FAQPage yapısal verisini görünen SSS içeriğinden yeniden kurar.

Kullanım: python tools/build_home_en.py
"""
import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = "https://tidemobileapp.com"

IDS = [("hakkimizda", "about"), ("vizyon", "vision"), ("ekip", "team"), ("yol-haritasi", "roadmap"),
       ("uygulamalar", "apps"), ("iletisim", "contact"), ("sss", "faq"), ("basinda", "press")]

PAIRS = [
 # head
 ('<html lang="tr">', '<html lang="en">'),
 ("<title>Tide Mobile: Modi ve TerraVisa'nın Mobil Uygulama Stüdyosu</title>", "<title>Tide Mobile: The Mobile App Studio Behind Modi and TerraVisa</title>"),
 ('content="Tide Mobile (Tidemobile), Adana merkezli mobil uygulama stüdyosu. Ücretsiz ruh sağlığı uygulaması Modi\'yi ve vize planlama uygulaması TerraVisa\'yı geliştirir." />',
  'content="Tide Mobile (Tidemobile) is a mobile app studio based in Adana, Türkiye. We build Modi, a free mental health app, and TerraVisa, a visa and travel planning app." />'),
 ('<link rel="canonical" href="https://tidemobileapp.com/" />', '<link rel="canonical" href="https://tidemobileapp.com/index-en.html" />'),
 ('<meta property="og:locale" content="tr_TR" />\n  <meta property="og:locale:alternate" content="en_US" />', '<meta property="og:locale" content="en_US" />\n  <meta property="og:locale:alternate" content="tr_TR" />'),
 ('<meta property="og:url" content="https://tidemobileapp.com/" />', '<meta property="og:url" content="https://tidemobileapp.com/index-en.html" />'),
 ("Tide Mobile: İnsan odaklı mobil ürünler geliştiriyoruz", "Tide Mobile: We build human-centered mobile products"),
 ("Modi, TerraVisa, LunaPara ve Reframe'i geliştiren Adana merkezli mobil ürün stüdyosu. Psikoloji, veri ve tasarımın kesişiminde.",
  "The Adana-based mobile product studio behind Modi, TerraVisa, LunaPara and Reframe. Where psychology, data and design meet."),
 ("og-tidemobile.jpg", "og-tidemobile-en.jpg"),
 ("Modi ve TerraVisa'yı geliştiren mobil uygulama stüdyosu.", "The mobile app studio behind Modi and TerraVisa."),
 ('<meta name="theme-color"', '<meta name="theme-color"'),
 # menü
 (">İçeriğe geç<", ">Skip to content<"),
 ('aria-label="Tide Mobile ana sayfa"', 'aria-label="Tide Mobile home"'),
 ('href="/" class="wm"', 'href="index-en.html" class="wm"'),
 ('aria-label="Ana menü"', 'aria-label="Main menu"'),
 (">Hakkımızda</a>", ">About</a>"), (">Vizyon</a>", ">Vision</a>"), (">Ekip</a>", ">Team</a>"), (">Yol Haritası</a>", ">Roadmap</a>"),
 (">Uygulamalar</a>", ">Apps</a>"), ('href="teknik-ortaklik.html">Teknik Ortaklık</a>', 'href="teknik-ortaklik-en.html">Technical Partnership</a>'),
 ('href="blog.html">Blog</a>', 'href="blog-en.html">Blog</a>'), (">İletişim</a>", ">Contact</a>"),
 ('<a href="index-en.html" class="nav-lang" hreflang="en" lang="en" aria-label="English version">EN ', '<a href="index.html" class="nav-lang" hreflang="tr" lang="tr" aria-label="Türkçe sürüm">TR '),
 ('aria-label="Menüyü aç"', 'aria-label="Open menu"'),
 # hero
 ('İnsan odaklı mobil <span class="nowrap">ürünler <em>geliştiriyoruz.</em></span>', 'We build <span class="nowrap">human-centered</span> <em>mobile products.</em>'),
 ("Tide Mobile, sektör içgörülerini analiz ederek fırsatları belirleyen ve bunları finans, seyahat ve zihinsel iyi oluş alanlarında mobil ürünlere dönüştüren bağımsız bir ürün stüdyosudur.",
  "Tide Mobile is an independent product studio that studies industry insights, spots opportunities and turns them into mobile products for finance, travel and mental wellbeing."),
 (">Uygulamaları Keşfet <", ">Explore the Apps <"),
 (">Bize Ulaşın <", ">Get in Touch <"),
 ("<span>Adana'dan<br>Dünyaya.</span>", "<span>From Adana<br>to the world.</span>"),
 ('aria-label="Rakamlarla Tide Mobile ve çalışma biçimimiz"', 'aria-label="Tide Mobile in numbers and how we work"'),
 ('<span>Rakamlarla <span lang="en">Tide Mobile</span></span>', '<span>Tide Mobile in numbers</span>'),
 ("<dt>Uygulama</dt>", "<dt>Apps</dt>"), ("<dt>Kategori</dt>", "<dt>Categories</dt>"), ("<dt>Kuruluş Yılı</dt>", "<dt>Founded</dt>"),
 (">Nasıl çalışıyoruz?<", ">How we work<"),
 ("<h3>İçgörü</h3><p>Kullanıcı davranışlarını ve sektör dinamiklerini analiz ediyoruz.</p>", "<h3>Insight</h3><p>We analyze user behavior and industry dynamics.</p>"),
 ("<h3>Fırsat</h3><p>Gerçek ihtiyaçları belirliyor, çözümler geliştiriyoruz.</p>", "<h3>Opportunity</h3><p>We identify real needs and develop solutions.</p>"),
 ("<h3>Ürün</h3><p>İnsanlara değer katan mobil ürünlere dönüştürüyoruz.</p>", "<h3>Product</h3><p>We turn them into mobile products that add value to people's lives.</p>"),
 # hakkımızda
 ('<p class="label">Hakkımızda</p>', '<p class="label">About us</p>'),
 ("Psikoloji, veri ve tasarımın <em>kesişiminde.</em>", "Where psychology, data and design <em>meet.</em>"),
 ("Tide Mobile, insan davranışını anlamak, gerçek ihtiyaçları çözmek ve sürdürülebilir dijital deneyimler yaratmak için multidisipliner bir yaklaşımı benimser. Adana merkezli bağımsız bir stüdyoyuz; psikoloji tarafındaki içeriklerimiz uzman psikolog onayından geçer.",
  "Tide Mobile takes a multidisciplinary approach to understanding human behavior, solving real needs and building digital experiences that last. We are an independent studio based in Adana, and our psychology content is approved by a licensed psychologist."),
 (">Daha Fazla <", ">Learn More <"),
 ("<h3>Psikoloji Temelli Yaklaşım</h3><p>İnsan odaklı, empatik tasarım.</p>", "<h3>Psychology-Based Approach</h3><p>Human-centered, empathetic design.</p>"),
 ("<h3>Uzlaşmasız Tasarım Kalitesi</h3><p>Estetik ve işlevi bir arada sunar.</p>", "<h3>Uncompromising Design Quality</h3><p>Form and function, together.</p>"),
 ("<h3>Veri Odaklı Geliştirme</h3><p>Gerçek verilerle, doğru kararlar.</p>", "<h3>Data-Driven Development</h3><p>Real data, better decisions.</p>"),
 ("<h3>Uzun Vadeli Etki Vizyonu</h3><p>Sadece bugün için değil, yarın için.</p>", "<h3>Long-Term Impact</h3><p>Built for tomorrow, not just today.</p>"),
 # vizyon
 ('<p class="label">Vizyon ve misyon</p>', '<p class="label">Vision and mission</p>'),
 ('Teknolojinin insanlara <span class="nowrap">hizmet ettiği</span> bir dünya.', 'A world where technology <span class="nowrap">serves people.</span>'),
 ("Tide Mobile, teknolojinin kullanıcıların hayatını kolaylaştırdığı; sağlıklı, güvenli ve daha bilinçli bir gelecek için çalışır.",
  "Tide Mobile works toward a healthier, safer and more mindful future in which technology makes people's lives easier."),
 ("<p>“Teknoloji,<br>insan için vardır.”</p>", "<p>“Technology<br>exists for people.”</p>"),
 # uygulamalar
 ('<p class="label">Uygulamalarımız</p>', '<p class="label">Our apps</p>'),
 ("Hayatı kolaylaştıran <em>dört farklı dünya.</em>", "Four different worlds <em>that make life easier.</em>"),
 (">Sık sorulanlar <", ">Frequently asked <"),
 ('alt="LunaPara uygulama ikonu"', 'alt="LunaPara app icon"'), ('alt="TerraVisa uygulama ikonu"', 'alt="TerraVisa app icon"'),
 ('alt="Modi uygulama ikonu"', 'alt="Modi app icon"'), ('alt="Reframe uygulama ikonu"', 'alt="Reframe app icon"'),
 ('<p class="app-cat">Finans</p>', '<p class="app-cat">Finance</p>'),
 ("Gelir ve gider takibi, duygusal harcama örüntülerini keşfetme ve yapay zeka destekli analiz.", "Income and expense tracking, emotional spending patterns and AI-powered insights."),
 (">Teste katıl <", ">Join the test <"),
 ("<i class=\"dot\"></i>Kapalı test<br>aşamasında", "<i class=\"dot\"></i>In closed<br>testing"),
 ('<p class="app-cat">Seyahat</p>', '<p class="app-cat">Travel</p>'),
 ("Vize gereksinimleri, siyasi risk bilgileri, Schengen 90/180 hesaplayıcı ve seyahat sigortası erişimi.", "Visa requirements, political risk levels, a Schengen 90/180 calculator and access to travel insurance."),
 ('src="modi/assets/badges/google-play-tr-ic.png" width="135" height="40" alt="Google Play\'den indirin"', 'src="modi/assets/badges/google-play-en-ic.png" width="135" height="40" alt="Get it on Google Play"'),
 ("<span class=\"foot-note\">iOS sürümü<br>App Store onayında</span>", "<span class=\"foot-note\">iOS version<br>in App Store review</span>"),
 ('<p class="app-cat">Zihinsel İyi Oluş</p>', '<p class="app-cat">Mental Wellbeing</p>'),
 ("Psikolog onaylı yolculuklar, duygu günlüğü, meditasyonlar ve seni yargılamadan dinleyen bir sohbet arkadaşı.", "Psychologist-approved journeys, a mood journal, meditations and a chat companion that listens without judgment."),
 ('src="modi/assets/badges/app-store-tr-ic.svg" width="151" height="40" alt="App Store\'dan indirin"', 'src="modi/assets/badges/app-store-en.svg" width="120" height="40" alt="Download on the App Store"'),
 ('aria-label="Modi\'nin web sitesi"', 'aria-label="Modi website"'),
 ('<p class="app-cat">Bilişsel Davranışçı Terapi</p>', '<p class="app-cat">Cognitive Behavioral Therapy</p>'),
 ("BDT ilkelerine dayanan düşünce kayıtları, duygu takibi ve Sokratik sorgulama.", "Thought records, mood tracking and Socratic questioning based on CBT principles."),
 ("<b>Durum</b><span>Sunumdan önce</span>", "<b>Situation</b><span>Before a presentation</span>"),
 ("<b>Düşünce</b><span>“Kesin hata yapacağım.”</span>", "<b>Thought</b><span>“I'm going to mess this up.”</span>"),
 ("<b>Kanıt?</b><span>Son üç sunum iyi geçti.</span>", "<b>Evidence?</b><span>My last three went well.</span>"),
 ("<b>Yeniden çerçevele</b><span>“Hazırlandım, elimden geleni yapacağım.”</span>", "<b>Reframe</b><span>“I've prepared. I'll do my best.”</span>"),
 (">Haberdar ol <", ">Get notified <"),
 ("<i class=\"dot\"></i>Geliştirme<br>aşamasında", "<i class=\"dot\"></i>In<br>development"),
 # basında
 ('aria-label="Haberler.com röportajı: Tide Mobile Kurucu Ortağı C. Tanıl Tabakoğlu, ITS 2026"></video>',
  'aria-label="Haberler.com interview: Tide Mobile Co-Founder C. Tanıl Tabakoğlu, ITS 2026 (in Turkish with English subtitles)"><track kind="subtitles" srclang="en" label="English" src="assets/home/its-roportaj-en.vtt" default /></video>'),
 ('aria-label="Röportajı oynat"', 'aria-label="Play the interview"'),
 ("<figcaption>Görüntü: Haberler.com · ITS 2026, İstanbul</figcaption>", "<figcaption>Footage: Haberler.com · ITS 2026, Istanbul · In Turkish with English subtitles</figcaption>"),
 ('<span>Basında <span lang="en">Tide Mobile</span></span>', "<span>Tide Mobile in the press</span>"),
 ("ITS 2026'da <em>Modi'yi anlattık.</em>", "We introduced Modi <em>at ITS 2026.</em>"),
 ("3. Uluslararası İhracat ve Yatırım Zirvesi'nde (ITS 2026) Kurucu Ortağımız C. Tanıl Tabakoğlu, Haberler.com'a Tide Mobile'ın çıkış hikâyesini ve Modi'yi anlattı.",
  "At the 3rd International Export and Investment Summit (ITS 2026), our Co-Founder C. Tanıl Tabakoğlu told Haberler.com how Tide Mobile started and what Modi does."),
 ("<p>“Psikolojik destek arayışından önceki ilk adımı kolaylaştırmayı hedefliyoruz.”</p>", "<p>“We want to make the first step before seeking psychological support easier.”</p>"),
 ("<footer>C. Tanıl Tabakoğlu, Kurucu Ortak</footer>", "<footer>C. Tanıl Tabakoğlu, Co-Founder · translated from Turkish</footer>"),
 ("<span>Haberler.com · 9 Ekim 2026</span>", "<span>Haberler.com · October 9, 2026</span>"),
 (">Haberin tamamı <", ">Read the full story (TR) <"),
 # ekip
 ('<p class="label">Ekibimiz</p>', '<p class="label">Our team</p>'),
 ("Daha iyi bir gelecek için, <em>birlikte.</em>", "Together, for a <em>better future.</em>"),
 ("<p>Kurucu Ortak · Ürün ve Büyüme</p>", "<p>Co-Founder · Product & Growth</p>"),
 ("<p>Kurucu Ortak · Psikoloji ve İçerik</p>", "<p>Co-Founder · Psychology & Content</p>"),
 ("<p>Marka ve İletişim Lideri</p>", "<p>Brand & Communications Lead</p>"),
 ("<p>Görsel ve Web Tasarımcı</p>", "<p>Visual & Web Designer</p>"),
 ("<p>Yapay Zeka Mühendisi</p>", "<p>AI Engineer</p>"),
 # yol haritası
 ('<p class="label">2026 yol haritası</p>', '<p class="label">2026 roadmap</p>'),
 ("Daha fazlası için, <em>adım adım.</em>", "Step by step, <em>toward more.</em>"),
 ("<p>Marka altyapısını güçlendirme</p>", "<p>Strengthening the brand foundation</p>"),
 ("<p>Wellness ve psikoloji odaklı ürün geliştirmeleri</p>", "<p>Wellness and psychology product development</p>"),
 ("<p>İçerik ve topluluk katmanını büyütme</p>", "<p>Growing the content and community layer</p>"),
 ("<p>Yeni deneyimleri yayına hazırlama</p>", "<p>Preparing new experiences for launch</p>"),
 # uzman + ai
 ('aria-label="Uzman desteği"', 'aria-label="Expert support"'),
 ('<p class="label">Uzman desteği</p>', '<p class="label">Expert support</p>'),
 ("Modi'nin psikoloji yaklaşımına <em>güçlü bir destek.</em>", "Strong expert backing for <em>Modi's psychology.</em>"),
 ("<span>Uzman Psikolog</span>İlknur Yılmazgil", "<span>Licensed Psychologist</span>İlknur Yılmazgil"),
 (">Detayları Gör <", ">See Details <"),
 ('<p class="label">Tümü daha iyi bir sen için</p>', '<p class="label">All for a better you</p>'),
 ("Yapay zeka destekli, <em>insan odaklı</em> mobil ürünler.", "AI-powered, <em>human-centered</em> mobile products."),
 ("Tide Mobile, psikoloji, veri ve tasarım gücüyle daha iyi bir dijital deneyim sunar.", "Tide Mobile combines psychology, data and design to deliver a better digital experience."),
 # teknik ortaklık
 ('<p class="label">Teknik ortaklık</p>', '<p class="label">Technical partnership</p>'),
 ("Fikirlerinizi birlikte <em>ürüne dönüştürelim.</em>", "Let's turn your ideas <em>into products.</em>"),
 ("Yapay zeka destekli mobil uygulamalar, premium UI/UX ve interaktif deneyimler için ajanslar ve markalarla iş birliği yapıyoruz.",
  "We partner with agencies and brands on AI-powered mobile apps, premium UI/UX and interactive experiences."),
 ('href="teknik-ortaklik.html">İletişime Geç <', 'href="teknik-ortaklik-en.html">Work With Us <'),
 # sss
 ('aria-label="Sık sorulan sorular ve iletişim"', 'aria-label="Frequently asked questions and contact"'),
 ('<p class="label">Sıkça sorulan sorular</p>', '<p class="label">Frequently asked questions</p>'),
 ("Merak ettiklerinizin <em>cevapları burada.</em>", "Answers to <em>your questions.</em>"),
 ("<summary>Tide Mobile nedir?", "<summary>What is Tide Mobile?"),
 ("Tide Mobile (Tidemobile), Adana merkezli bağımsız bir mobil uygulama stüdyosudur. Ruh sağlığı uygulaması Modi'yi ve seyahat ve vize planlama uygulaması TerraVisa'yı geliştirir. Ürünlerinde psikoloji, veri ve tasarımı bir araya getirir.",
  "Tide Mobile (Tidemobile) is an independent mobile app studio based in Adana, Türkiye. It builds Modi, a mental health app, and TerraVisa, a visa and travel planning app, bringing together psychology, data and design."),
 ("<summary>Hangi uygulamalar geliştiriliyor?", "<summary>Which apps does Tide Mobile build?"),
 ("Modi (ruh sağlığı, App Store ve Google Play'de yayında), TerraVisa (vize ve seyahat planlama, Google Play'de yayında, iOS sürümü App Store onay sürecinde), LunaPara (finansal farkındalık, kapalı test aşamasında) ve Reframe (BDT temelli düşünce kaydı, geliştirme aşamasında).",
  "Modi (mental health, live on the App Store and Google Play), TerraVisa (visa and travel planning, live on Google Play, iOS version in App Store review), LunaPara (financial awareness, in closed testing) and Reframe (CBT-based thought records, in development)."),
 ("<summary>Modi nereden indirilir?", "<summary>Where can I download Modi?"),
 ("Modi, <a href=\"https://apps.apple.com/tr/app/id6762211248\" rel=\"noopener\">App Store</a> ve <a href=\"https://play.google.com/store/apps/details?id=com.tidemobile.modi\" rel=\"noopener\">Google Play</a>'de ücretsiz olarak yayında. İndirmesi ve temel özellikleri ücretsizdir; isteğe bağlı Modi Premium ek içerik sunar. Ayrıntılar için <a href=\"modi/\">Modi'nin web sitesine</a> göz atabilirsin.",
  "Modi is available for free on the <a href=\"https://apps.apple.com/tr/app/id6762211248\" rel=\"noopener\">App Store</a> and <a href=\"https://play.google.com/store/apps/details?id=com.tidemobile.modi\" rel=\"noopener\">Google Play</a>. Downloading and the core features are free; the optional Modi Premium adds extra content. See <a href=\"modi/\">Modi's website</a> for details."),
 ("<summary>Teknik ortaklık için nasıl iletişim kurulur?", "<summary>How can we work with Tide Mobile?"),
 ("Ajanslar ve markalar için mobil uygulama geliştirme, UI/UX ve interaktif deneyim üretiminde teknik ortaklık sunuyoruz. Ayrıntılar <a href=\"teknik-ortaklik-en.html\">Technical Partnership</a> sayfasında; tidemobile.contact@gmail.com adresinden ya da yandaki formdan da ulaşabilirsin.",
  "We offer technical partnership to agencies and brands in mobile app development, UI/UX and interactive experiences. See the <a href=\"teknik-ortaklik-en.html\">Technical Partnership</a> page, or reach us at tidemobile.contact@gmail.com or through the form on this page."),
 ("<summary>Modi terapinin yerine geçer mi?", "<summary>Does Modi replace therapy?"),
 ("Hayır. Modi terapi yerine geçmez ve tanı koymaz. Günlük iyi oluşu destekleyen bir araçtır. Sohbette risk fark edildiğinde kullanıcıyı 112 Acil Çağrı ve 182 MHRS gibi profesyonel destek kaynaklarına yönlendirir.",
  "No. Modi does not replace therapy and does not diagnose. It is a tool that supports everyday wellbeing. When risk is detected in a conversation, it directs the user to professional support such as the 112 emergency line and the 182 MHRS line in Türkiye."),
 ("<summary>TerraVisa nedir ve ücretsiz mi?", "<summary>What is TerraVisa and is it free?"),
 ("TerraVisa, pasaportuna göre ülkelerin vize gereksinimlerini ve siyasi risk seviyelerini interaktif bir dünya haritasında gösteren bir seyahat uygulamasıdır. Schengen 90/180 gün hesaplayıcı, vize maliyet hesaplayıcı, evrak sihirbazı ve VFS/BLS konsolosluk randevu bildirimleri içerir. Uygulama ücretsizdir; isteğe bağlı premium abonelik ek özellikler sunar.",
  "TerraVisa is a travel app that shows visa requirements and political risk levels for your passport on an interactive world map. It includes a Schengen 90/180 day calculator, a visa cost calculator, a document wizard and VFS/BLS consulate appointment alerts. The app is free; an optional premium subscription adds extra features."),
 ("<summary>Schengen 90/180 gün kuralını nasıl takip edebilirim?", "<summary>How can I track the Schengen 90/180 rule?"),
 ("Schengen bölgesinde herhangi bir 180 günlük dönem içinde en fazla 90 gün kalınabilir. TerraVisa'daki Schengen 90/180 gün hesaplayıcısına giriş ve çıkış tarihlerini eklediğinde kalan gün hakkını otomatik olarak hesaplar.",
  "You can stay in the Schengen area for up to 90 days in any 180-day period. Add your entry and exit dates to TerraVisa's Schengen 90/180 calculator and it works out your remaining days automatically."),
 ("<summary>LunaPara ne zaman herkese açık olacak?", "<summary>When will LunaPara be publicly available?"),
 ("LunaPara şu anda kapalı test aşamasındadır. Erken erişim için <a href=\"https://groups.google.com/g/lunapara-testers\" rel=\"noopener\">test grubuna katılıp</a> <a href=\"https://play.google.com/apps/testing/com.lunapara.app\" rel=\"noopener\">Google Play üzerinden test kullanıcısı</a> olabilirsin.",
  "LunaPara is currently in closed testing. For early access, <a href=\"https://groups.google.com/g/lunapara-testers\" rel=\"noopener\">join the test group</a> and <a href=\"https://play.google.com/apps/testing/com.lunapara.app\" rel=\"noopener\">become a tester on Google Play</a>."),
 (">Tüm soruları göster <", ">Show all questions <"),
 # iletişim
 ('<p class="label">İletişim</p>', '<p class="label">Contact</p>'),
 ("Bizimle <em>iletişime geçin.</em>", "Get <em>in touch.</em>"),
 ("Sorularınız, iş birliği talepleriniz veya geri bildirimleriniz için buradayız.", "We're here for your questions, collaboration requests and feedback."),
 ('for="f-name">Adınız Soyadınız<', 'for="f-name">Full name<'), ('placeholder="Adınız Soyadınız"', 'placeholder="Full name"'),
 ('for="f-mail">E-posta adresiniz<', 'for="f-mail">Email address<'), ('placeholder="E-posta Adresiniz"', 'placeholder="Email address"'),
 ('for="f-sub">Konu<', 'for="f-sub">Subject<'), ('placeholder="Konu"', 'placeholder="Subject"'),
 ('for="f-msg">Mesajınız<', 'for="f-msg">Message<'), ('placeholder="Mesajınız"', 'placeholder="Message"'),
 (">Gönder <", ">Send <"),
 ('name="kvkk_onay" value="evet"', 'name="kvkk_consent" value="yes"'),
 ("<span><a href=\"kvkk.html\">KVKK Aydınlatma Metni</a>'ni ve <a href=\"gizlilik.html\">Gizlilik Politikası</a>'nı okudum, kabul ediyorum.</span>",
  "<span>I have read and accept the <a href=\"kvkk.html\">KVKK Privacy Notice</a> and the <a href=\"gizlilik.html\">Privacy Policy</a> (in Turkish).</span>"),
 # footer
 ("© 2026 Tide Mobile. Tüm hakları saklıdır.", "© 2026 Tide Mobile. All rights reserved."),
 ('<li><a href="kvkk.html">KVKK Aydınlatma Metni</a></li>', '<li><a href="kvkk.html">KVKK Privacy Notice (TR)</a></li>'),
 ('<li><a href="gizlilik.html">Gizlilik Politikası</a></li>', '<li><a href="gizlilik.html">Privacy Policy (TR)</a></li>'),
 ('<li><a href="modi-kullanim-kosullari.html">Modi Kullanım Koşulları</a></li>', '<li><a href="modi-kullanim-kosullari.html">Modi Terms of Use (TR)</a></li>'),
]

# Türkçe kalmasına izin verilen özel adlar
ALLOWED_TR = ["Türkçe sürüm", "Tanıl", "Tabakoğlu", "Yılmazgil", "İlknur", "Aslı", "Kılıç", "Serçe", "Doğukan", "Kıymet", "Türkiye", "İY", "Haberler.com"]


def faq_ld(page_html, lang):
    items = []
    for q, a in re.findall(r"<summary>(.*?)<svg.*?</summary><p class=\"ans\">(.*?)</p>", page_html, re.S):
        items.append({"@type": "Question", "name": html.unescape(q.strip()),
                      "acceptedAnswer": {"@type": "Answer", "text": html.unescape(re.sub(r"<[^>]+>", "", a)).strip()}})
    url = SITE + ("/" if lang == "tr" else "/index-en.html")
    return {"@type": "FAQPage", "@id": url + "#faq", "mainEntity": items}


def set_ld(page_html, graph):
    blob = json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False, separators=(",", ":"))
    return re.sub(r'<script type="application/ld\+json">.*?</script>', lambda m: '<script type="application/ld+json">\n  ' + blob + "\n  </script>", page_html, count=1, flags=re.S)


def get_ld(page_html):
    return json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>', page_html, re.S).group(1))


def main():
    tr = (ROOT / "index.html").read_text(encoding="utf-8")
    # TR: SSS verisini görünen içerikten yeniden kur
    ld = get_ld(tr)
    ld["@graph"] = [g for g in ld["@graph"] if g.get("@type") != "FAQPage"] + [faq_ld(tr, "tr")]
    tr = set_ld(tr, ld["@graph"])
    (ROOT / "index.html").write_text(tr, encoding="utf-8", newline="\n")

    en = tr
    missing = []
    for a, b in PAIRS:
        if a not in en:
            missing.append(a[:90])
            continue
        en = en.replace(a, b)
    for t, e in IDS:
        en = en.replace(f'id="{t}"', f'id="{e}"').replace(f'href="#{t}"', f'href="#{e}"')
    if missing:
        sys.exit("Bulunamayan parçalar:\n  " + "\n  ".join(missing))

    # EN yapısal veri: eski EN grafiği + video + görünen SSS
    old = json.loads((ROOT / "content" / "index-en-jsonld.json").read_text(encoding="utf-8"))["@graph"]
    tr_graph = get_ld(tr)["@graph"]
    video = next(g for g in tr_graph if g.get("@type") == "VideoObject")
    video = dict(video, name="ITS 2026: Tide Mobile Co-Founder C. Tanıl Tabakoğlu interviewed by Haberler.com",
                 description="At the 3rd International Export and Investment Summit (ITS 2026), Tide Mobile Co-Founder C. Tanıl Tabakoğlu tells Haberler.com how Tide Mobile started and introduces Modi, a gamified psychology app. In Turkish.")
    graph = []
    for g in old:
        if g.get("@type") == "FAQPage":
            continue
        if g.get("@type") == "Organization":
            g["slogan"] = "We build human-centered mobile products."
        if g.get("@type") == "WebPage":
            g["dateModified"] = __import__("datetime").date.today().isoformat()
        graph.append(g)
    graph += [video, faq_ld(en, "en")]
    en = set_ld(en, graph)

    body = re.sub(r"<script.*?</script>|<style.*?</style>", "", en[en.index("<body>"):], flags=re.S)
    text = " ".join(re.findall(r">([^<>]+)<", body)) + " " + " ".join(re.findall(r'(?:alt|aria-label|placeholder)="([^"]+)"', body))
    for w in ALLOWED_TR:
        text = text.replace(w, "")
    left = sorted(set(re.findall(r"\w*[çğıöşüÇĞİÖŞÜ]\w*", text)))
    if left:
        sys.exit("Çevrilmemiş Türkçe kalıntı: " + ", ".join(left))
    for ch in "—–":
        if ch in en or ch in tr:
            sys.exit("Em/en dash bulundu")
    (ROOT / "index-en.html").write_text(en, encoding="utf-8", newline="\n")
    print("index-en.html yazıldı,", len(PAIRS), "parça çevrildi")


if __name__ == "__main__":
    main()

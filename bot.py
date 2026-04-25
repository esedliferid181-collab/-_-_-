import discord
from discord.ext import commands
from discord import ui
import datetime
import asyncio
import random
import os
import json

# --- AYARLAR ---
TOKEN = os.environ.get("DISCORD_TOKEN")
KAP_KANAL_ID = 1489650264389587004
KAYIT_KANAL_ID = 1479825240401117296
PREFIX = "."
intents = discord.Intents.all()
bot = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=None)

# ====================== ROLEPLAY AYARLARI ======================
KAYIT_YETKILI_ROL_ID = 1479820024658137221
DEGER_YETKILI_ROL_ID = 1479819855182954506
DEGER_LOG_KANAL_ID = 1488467755370811482
ANTRENMAN_KANAL_ID = 1489650216398356614
ROL_YETKILI_ROL_ID = 1480224190752620636
KAYITLI_ROL = "Kayıtlı"
KAYITSIZ_ROL = "Kayıtsız"
ROL_UYE = "Üye"
ROL_FUTBOLCU = "Futbolcu"
ROL_TAKIM_BASKANI = "Takım Başkanı"
LIG_COMMANDER_ROL_ADI = "League Commander"

# Bot sahibi ID'leri (vk komutunu kullanabilecekler)
VK_YETKILI_IDS = [1438202822897434738]

# ====================== TAKIM ROL ID'LERİ ======================
TAKIM_ROLLERI = {
    "FC Barcelona": 1479835203668148325,
    "Real Madrid CF": 1479835100693663955,
    "ATLETİCO MADRİD": 1479835299319255172,
    "LİVERPOOL": 1479835413286752367,
    "MANCHESTER CİTY": 1479835961742589963,
    "MANCHESTER UNİTED": 1479836203397288088,
    "BAYERN MÜNİH": 1479838152691814534,
    "GALATASARAY": 1479838753676857546,
    "FENERBAHÇE": 1479838832580104263,
    "BEŞİKTAŞ": 1479840026622955621,
    "DORTMUND": 1480442890042736793,
    "PSG": 1480443652852682752,
    "JUVENTUS": 1480442964848414801,
    "AC MİLAN": 1480443773493448807,
    "İNTER": 1480443987302289530,
    "LYON": 1480444106999205959,
}

# ================================================================
# Veri Saklama Alanları (bellekte)
son_silinenler = {}
afk_kullanicilar = {}
kap_bellek = {}
kayit_sayaci = {}
deger_sayaci = {}
mesaj_sayaci = {}
gunluk_mesaj_sayaci = {}
snipe_all_listesi = {}
aktif_bilgi_oyunu = {}
aktif_vampir_oyunu = {}
cark_gunluk = {}          # {user_id: {"tarih": "YYYY-MM-DD", "sayi": int}}
son_cark_sonucu = {}      # {user_id: son_sonuc_index} — tekrar engellemek için
kariyer_verileri = {}     # {user_id: {"takimlar": [...], "goller": int, "asistler": int}}

# ====================== KALICI VERİ (JSON) ======================
ANTRENMAN_DOSYA = "antrenman_sayac.json"
KARIYER_DOSYA = "kariyer_verileri.json"

def antrenman_yukle():
    if os.path.exists(ANTRENMAN_DOSYA):
        try:
            with open(ANTRENMAN_DOSYA, "r") as f:
                data = json.load(f)
                return {int(k): v for k, v in data.items()}
        except:
            pass
    return {}

def antrenman_kaydet(sayac):
    try:
        with open(ANTRENMAN_DOSYA, "w") as f:
            json.dump({str(k): v for k, v in sayac.items()}, f)
    except:
        pass

def kariyer_yukle():
    if os.path.exists(KARIYER_DOSYA):
        try:
            with open(KARIYER_DOSYA, "r") as f:
                data = json.load(f)
                return {int(k): v for k, v in data.items()}
        except:
            pass
    return {}

def kariyer_kaydet(veriler):
    try:
        with open(KARIYER_DOSYA, "w") as f:
            json.dump({str(k): v for k, v in veriler.items()}, f, ensure_ascii=False)
    except:
        pass

# Başlangıçta yükle
antrenman_sayac = antrenman_yukle()
kariyer_verileri = kariyer_yukle()

# ====================== YARDIMCI FONKSİYONLAR ======================
def rol_bul_esnek(guild, rol_adi):
    """Büyük/küçük harf farkı gözetmeksizin rol bulur."""
    for rol in guild.roles:
        if rol.name.lower() == rol_adi.lower():
            return rol
    return None

# ====================== OLAYLAR ======================
@bot.event
async def on_ready():
    print(f'--------------------------------------------------')
    print(f'🚀 NOVA PLUS SİSTEMİ %100 KAPASİTEYLE ÇALIŞIYOR!')
    print(f'🤖 Bot Kullanıcı Adı: {bot.user.name}')
    print(f'🆔 Bot ID: {bot.user.id}')
    print(f'📅 Tarih: {datetime.datetime.now().strftime("%d/%m/%Y")}')
    print(f'--------------------------------------------------')
    await bot.change_presence(activity=discord.Streaming(name=".yardım | NOVA PLUS", url="https://twitch.tv/NOVA"))


@bot.event
async def on_message_delete(message):
    if message.author.bot:
        return
    son_silinenler[message.channel.id] = {
        "icerik": message.content,
        "yazar": message.author,
        "zaman": datetime.datetime.now()
    }


@bot.event
async def on_message(message):
    if message.author.bot:
        return

    mesaj_sayaci[message.author.id] = mesaj_sayaci.get(message.author.id, 0) + 1

    bugun = datetime.date.today().isoformat()
    if bugun not in gunluk_mesaj_sayaci:
        gunluk_mesaj_sayaci[bugun] = {}
    gunluk_mesaj_sayaci[bugun][message.author.id] = gunluk_mesaj_sayaci[bugun].get(message.author.id, 0) + 1

    kanal_id = message.channel.id
    if kanal_id not in snipe_all_listesi:
        snipe_all_listesi[kanal_id] = []
    snipe_all_listesi[kanal_id].append({
        "yazar": message.author,
        "icerik": message.content,
        "zaman": datetime.datetime.now()
    })
    simdi = datetime.datetime.now()
    snipe_all_listesi[kanal_id] = [
        m for m in snipe_all_listesi[kanal_id]
        if (simdi - m["zaman"]).total_seconds() < 300
    ]

    if message.author.id in afk_kullanicilar:
        del afk_kullanicilar[message.author.id]
        await message.channel.send(
            f"👋 Tekrar hoş geldin {message.author.mention}! AFK modundan çıkarıldın.",
            delete_after=5,
            allowed_mentions=discord.AllowedMentions(everyone=False, roles=False, users=True)
        )

    for mention in message.mentions:
        if mention.id in afk_kullanicilar:
            sebep = afk_kullanicilar[mention.id]
            await message.channel.send(
                f"⚠️ {mention.name} şu an AFK durumda! \n📝 Sebep: **{sebep}**",
                allowed_mentions=discord.AllowedMentions(everyone=False, roles=False, users=True)
            )

    mesaj = message.content.strip()
    if mesaj in ["sa", "Sa"]:
        await message.channel.send(f"{message.author.mention} **Aleykümselam, hoş geldin!**")

    await bot.process_commands(message)


# ====================== ÜYE GİRİŞ EVENTİ ======================
class UstelenView(discord.ui.View):
    def __init__(self, uye: discord.Member):
        super().__init__(timeout=600)
        self.uye = uye
        self.kilitli_kisi = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if self.kilitli_kisi is None:
            self.kilitli_kisi = interaction.user.id
            return True
        if interaction.user.id != self.kilitli_kisi:
            await interaction.response.send_message(
                "❌ Bu üyeyi şu an başkası kaydediyor, 10 dakika sonra tekrar deneyin!",
                ephemeral=True
            )
            return False
        return True

    @discord.ui.button(label="ÜSTLEN", style=discord.ButtonStyle.success, emoji="✅")
    async def ustlen_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not kayit_yetkisi_var_mi(interaction.user):
            await interaction.response.send_message(
                "❌ Bu butonu kullanmak için **Kayıt Yetkilisi** rolüne sahip olmalısın!",
                ephemeral=True
            )
            return
        button.disabled = True
        button.label = f"{interaction.user.display_name} üstlendi"
        embed = interaction.message.embeds[0]
        embed.description = (
            f"**{self.uye.mention}** kullanıcısının kaydı **{interaction.user.mention}** tarafından üstlenildi!\n\n"
            f"📝 Kayıt komutu: .k {self.uye.mention} İsim | Değer | Takım"
        )
        embed.color = 0x2ECC71
        await interaction.response.edit_message(embed=embed, view=self)

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True


@bot.event
async def on_member_join(member):
    if KAYIT_KANAL_ID == 0:
        return
    kanal = bot.get_channel(KAYIT_KANAL_ID)
    if not kanal:
        return

    kayit_yetkili_rol = member.guild.get_role(KAYIT_YETKILI_ROL_ID)
    if kayit_yetkili_rol:
        try:
            await kanal.send(f"⚠️ **Yeni Üye Katıldı!** {kayit_yetkili_rol.mention}")
        except:
            pass

    embed = discord.Embed(
        title="NOVA",
        description=(
            f"**{member.mention}** sunucuya katıldı!\n\n"
            f"Aşağıdaki **ÜSTLEN** butonuna basarak bu üyenin kaydını yapabilirsin."
        ),
        color=0xFF6B00,
        timestamp=datetime.datetime.now()
    )
    embed.add_field(name="👤 Kullanıcı", value=f"{member.name}#{member.discriminator}", inline=True)
    embed.add_field(name="🆔 ID", value=f"{member.id}", inline=True)
    embed.add_field(name="📅 Katılım Tarihi", value=f"<t:{int(datetime.datetime.now().timestamp())}:R>", inline=True)
    embed.set_footer(text="Üstlenen kişi 10 dakika boyunca kayıt yapabilir")

    view = UstelenView(member)
    await kanal.send(embed=embed, view=view)


# ====================== MODERASYON KOMUTLARI ======================
@bot.command()
@commands.has_permissions(manage_channels=True)
async def lock(ctx):
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False)
    embed = discord.Embed(
        title="🔒 Kanal Kilidlendi",
        description=f"Bu kanal {ctx.author.mention} tarafından mesaj gönderimine kapatıldı.",
        color=0xff0000
    )
    await ctx.send(embed=embed)


@bot.command()
@commands.has_permissions(manage_channels=True)
async def unlock(ctx):
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=True)
    embed = discord.Embed(
        title="🔓 Kanal Kilidi Açıldı",
        description=f"Bu kanal {ctx.author.mention} tarafından tekrar mesaj gönderimine açıldı.",
        color=0x00ff00
    )
    await ctx.send(embed=embed)


@bot.command()
@commands.has_permissions(ban_members=True)
async def unban(ctx, user_id: int):
    try:
        user = await bot.fetch_user(user_id)
        await ctx.guild.unban(user)
        embed = discord.Embed(
            title="✅ Ban Kaldırıldı",
            description=f"{user.name}#{user.discriminator} adlı kullanıcının yasağı kaldırıldı.",
            color=0x2ecc71
        )
        await ctx.send(embed=embed)
    except discord.NotFound:
        await ctx.send("❌ Bu ID'ye sahip bir yasaklama bulunamadı.")
    except Exception as e:
        await ctx.send(f"❌ Bir hata oluştu: {e}")


@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, sebep="Belirtilmedi"):
    await member.kick(reason=sebep)
    embed = discord.Embed(title="👢 Kullanıcı Sunucudan Atıldı", color=0xe67e22)
    embed.add_field(name="Atılan Kişi", value=member.mention, inline=True)
    embed.add_field(name="Yetkili", value=ctx.author.mention, inline=True)
    embed.add_field(name="Sebep", value=sebep, inline=False)
    await ctx.send(embed=embed)


@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, sebep="Belirtilmedi"):
    await member.ban(reason=sebep)
    embed = discord.Embed(title="🚫 Kullanıcı Yasaklandı", color=0xff0000)
    embed.add_field(name="Yasaklanan", value=member.mention, inline=True)
    embed.add_field(name="Yetkili", value=ctx.author.mention, inline=True)
    embed.add_field(name="Sebep", value=sebep, inline=False)
    await ctx.send(embed=embed)


@bot.command()
@commands.has_permissions(moderate_members=True)
async def mute(ctx, member: discord.Member, sure: int, *, sebep="Belirtilmedi"):
    try:
        duration = datetime.timedelta(minutes=sure)
        await member.timeout(duration, reason=sebep)
        embed = discord.Embed(title="🔇 Susturma İşlemi", color=0xffa500)
        embed.description = f"{member.mention} kullanıcısı susturuldu."
        embed.add_field(name="Süre", value=f"{sure} Dakika", inline=True)
        embed.add_field(name="Sebep", value=sebep, inline=True)
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"❌ Mute hatası: {e}")


@bot.command()
@commands.has_permissions(moderate_members=True)
async def unmute(ctx, member: discord.Member, *, sebep="Belirtilmedi"):
    try:
        if member.timed_out_until is None:
            return await ctx.send(f"❌ {member.mention} zaten susturulmamış.")
        await member.edit(timed_out_until=None, reason=sebep)
        embed = discord.Embed(title="🔊 Susturma Kaldırıldı", color=0x00ff00)
        embed.description = f"{member.mention} kullanıcısının susturulması kaldırıldı."
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"❌ Unmute hatası: {e}")


@bot.command()
@commands.has_permissions(manage_nicknames=True)
async def isim(ctx, member: discord.Member, *, yeni_isim):
    try:
        await member.edit(nick=yeni_isim)
        await ctx.send(f"✅ {member.name} kullanıcısının yeni ismi: {yeni_isim}")
    except:
        await ctx.send("❌ Yetki yetersiz!")


@bot.command()
@commands.has_permissions(manage_channels=True)
async def nuke(ctx):
    pos = ctx.channel.position
    yeni_kanal = await ctx.channel.clone()
    await ctx.channel.delete()
    await yeni_kanal.edit(position=pos)
    await yeni_kanal.send("💥 **Kanal Sıfırlandı!** Tüm mesajlar havaya uçtu.")


# ====================== ROL YETKİSİ KONTROL ======================
def rol_yetkisi_var_mi(kisi):
    if kisi.guild_permissions.administrator:
        return True
    if ROL_YETKILI_ROL_ID != 0:
        return any(rol.id == ROL_YETKILI_ROL_ID for rol in kisi.roles)
    return kisi.guild_permissions.manage_roles

def lig_commander_mi(kisi):
    if kisi.guild_permissions.administrator:
        return True
    return any(rol.name.lower() == LIG_COMMANDER_ROL_ADI.lower() for rol in kisi.roles)


# ====================== ROL KOMUTLARI ======================
@bot.command()
async def rolver(ctx, member: discord.Member, *, rol_adi: str):
    if not rol_yetkisi_var_mi(ctx.author):
        return await ctx.send("❌ Bu komutu kullanmak için yetkiniz yok!")
    rol = rol_bul_esnek(ctx.guild, rol_adi)
    if not rol:
        return await ctx.send(f"❌ **{rol_adi}** adında bir rol bulunamadı!")
    try:
        await member.add_roles(rol)
        embed = discord.Embed(
            title="🎭 Rol Verildi",
            description=f"{member.mention} kullanıcısına {rol.mention} rolü verildi.",
            color=0x3498db
        )
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"❌ Hata: {e}")


@bot.command()
async def rolal(ctx, member: discord.Member, *, rol_adi: str):
    if not rol_yetkisi_var_mi(ctx.author):
        return await ctx.send("❌ Bu komutu kullanmak için yetkiniz yok!")
    rol = rol_bul_esnek(ctx.guild, rol_adi)
    if not rol:
        return await ctx.send(f"❌ **{rol_adi}** adında bir rol bulunamadı!")
    try:
        await member.remove_roles(rol)
        embed = discord.Embed(
            title="🎭 Rol Alındı",
            description=f"{member.mention} kullanıcısından {rol.mention} rolü geri alındı.",
            color=0xe67e22
        )
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"❌ Hata: {e}")


@bot.command()
async def toplurolver(ctx, *, girdi: str):
    if not rol_yetkisi_var_mi(ctx.author):
        return await ctx.send("❌ Bu komutu kullanmak için yetkiniz yok!")
    try:
        parcalar = girdi.split(' ', 1)
        if len(parcalar) < 2:
            return await ctx.send(
                "❌ Hatalı Kullanım!\nÖrnek: .toplurolver @Kullanıcı Rol 1, Rol 2 veya .toplurolver hepsi Oyuncu"
            )
        hedef = parcalar[0]
        roller_metni = parcalar[1]
        rol_adlari = [r.strip() for r in roller_metni.split(',')]
        verilecek_rollar = []
        for ad in rol_adlari:
            rol = rol_bul_esnek(ctx.guild, ad)
            if rol:
                verilecek_rollar.append(rol)
        if not verilecek_rollar:
            return await ctx.send("❌ Belirttiğiniz isimde hiçbir rol sunucuda bulunamadı!")
        targets = []
        if hedef.lower() == "hepsi":
            targets = [m for m in ctx.guild.members if not m.bot]
        elif ctx.message.mentions:
            targets = [ctx.message.mentions[0]]
        else:
            return await ctx.send("❌ Lütfen birini etiketleyin veya hepsi yazın.")
        islem_mesaji = await ctx.send(f"⏳ **{len(targets)}** kişi taranıyor, roller ekleniyor...")
        sayac = 0
        for member in targets:
            try:
                eklenecekler = [r for r in verilecek_rollar if r not in member.roles]
                if eklenecekler:
                    await member.add_roles(*eklenecekler)
                    sayac += 1
                    if len(targets) > 1:
                        await asyncio.sleep(0.5)
            except:
                continue
        await islem_mesaji.edit(
            content=f"✅ İşlem Tamamlandı!\n👥 Toplam **{sayac}** kişiye "
                    f"{', '.join([r.name for r in verilecek_rollar])} rolleri başarıyla tanımlandı."
        )
    except Exception as e:
        await ctx.send(f"⚠️ Kritik bir hata oluştu: {e}")


@bot.command()
async def toplurolal(ctx, *, girdi: str):
    if not rol_yetkisi_var_mi(ctx.author):
        return await ctx.send("❌ Bu komutu kullanmak için yetkiniz yok!")
    try:
        parcalar = girdi.split(' ', 1)
        hedef = parcalar[0]
        roller_metni = parcalar[1]
        rol_adlari = [r.strip() for r in roller_metni.split(',')]
        alinacak_rollar = []
        for ad in rol_adlari:
            rol = rol_bul_esnek(ctx.guild, ad)
            if rol:
                alinacak_rollar.append(rol)
        if not alinacak_rollar:
            return await ctx.send("❌ Çıkarılacak geçerli bir rol bulunamadı.")
        targets = []
        if hedef.lower() == "hepsi":
            targets = [m for m in ctx.guild.members if not m.bot]
        elif ctx.message.mentions:
            targets = [ctx.message.mentions[0]]
        else:
            return await ctx.send("❌ Lütfen birini etiketleyin veya hepsi yazın.")
        islem_mesaji = await ctx.send(f"⏳ Roller geri alınıyor, lütfen bekleyin...")
        sayac = 0
        for member in targets:
            try:
                await member.remove_roles(*alinacak_rollar)
                sayac += 1
                if len(targets) > 1:
                    await asyncio.sleep(0.5)
            except:
                continue
        await islem_mesaji.edit(content=f"✅ Başarılı!\n👥 **{sayac}** kişiden belirtilen roller geri alındı.")
    except Exception as e:
        await ctx.send(f"⚠️ Hata: {e}")


# ====================== EĞLENCE KOMUTLARI ======================
@bot.command()
async def roll(ctx, *, secenekler: str):
    liste = [s.strip() for s in secenekler.split(',')]
    if len(liste) < 2:
        return await ctx.send("❌ Lütfen en az iki seçeneği virgül ile ayırın!")
    secim = random.choice(liste)
    embed = discord.Embed(
        title="🎲 Karar Verildi!",
        description=f"Seçenekler: {', '.join(liste)}\n\n✨ Sonuç: **{secim}**",
        color=discord.Color.purple()
    )
    embed.set_footer(text=f"İsteyen: {ctx.author.name}")
    await ctx.send(embed=embed)


@bot.command()
async def ping(ctx):
    await ctx.send(f"🏓 Pong! Gecikme: **{round(bot.latency * 1000)}ms**")


@bot.command()
async def avatar(ctx, member: discord.Member = None):
    member = member or ctx.author
    embed = discord.Embed(title=f"{member.name} Profil Resmi", color=discord.Color.random())
    embed.set_image(url=member.display_avatar.url)
    await ctx.send(embed=embed)


@bot.command()
async def snipe(ctx):
    data = son_silinenler.get(ctx.channel.id)
    if data:
        embed = discord.Embed(title="🎯 Son Silinen Mesaj", description=data['icerik'], color=0x3498db)
        embed.set_footer(text=f"Sahibi: {data['yazar'].name} | Zaman: {data['zaman'].strftime('%H:%M:%S')}")
        await ctx.send(embed=embed)
    else:
        await ctx.send("❌ Bu kanalda silinen mesaj yok.")


@bot.command()
async def afk(ctx, *, sebep="Meşgul/Uzakta"):
    yasaklar = ["@everyone", "@here"]
    for yasak in yasaklar:
        sebep = sebep.replace(yasak, "")
    sebep = " ".join(sebep.split()) or "Meşgul/Uzakta"
    afk_kullanicilar[ctx.author.id] = sebep
    await ctx.send(
        f"✅ {ctx.author.mention} artık AFK! Sebep: **{sebep}**",
        allowed_mentions=discord.AllowedMentions(everyone=False, roles=False, users=True)
    )


@bot.command()
async def ship(ctx, member: discord.Member):
    oran = random.randint(0, 100)
    emoji = "❤️" if oran > 50 else "💔"
    await ctx.send(f"📊 {ctx.author.mention} ❤️ {member.mention}\n💘 Aşk Uyumu: **%{oran}** {emoji}")


@bot.command()
async def ara(ctx, *, isim: str):
    bulananlar = []
    aranan_kucuk = isim.lower()
    for member in ctx.guild.members:
        if member.bot:
            continue
        if aranan_kucuk in member.display_name.lower() or aranan_kucuk in member.name.lower():
            bulananlar.append(member)
    if not bulananlar:
        return await ctx.send(f"❌ **{isim}** adında veya içinde geçen isimde sunucuda kimse bulunamadı!")
    kalan_mesaj = ""
    if len(bulananlar) > 15:
        kalan_mesaj = f"\n\n*...ve {len(bulananlar) - 15} kişi daha (toplam {len(bulananlar)} kişi)*"
        bulananlar = bulananlar[:15]
    liste_metni = "\n".join([f"• {m.mention}  (Takma ad: {m.display_name})" for m in bulananlar])
    embed = discord.Embed(
        title=f"🔍 Arama Sonuçları: \"{isim}\"",
        description=f"{liste_metni}{kalan_mesaj}",
        color=0x3498db
    )
    embed.set_footer(text=f"Toplam {len(bulananlar)} eşleşme bulundu")
    await ctx.send(embed=embed)


# ====================== ROLEPLAY (RP) KOMUTLARI ======================
def hata_embed(mesaj):
    return discord.Embed(title="❌ Hata", description=mesaj, color=0xff0000)


def basari_embed(mesaj):
    return discord.Embed(title="✅ Başarılı", description=mesaj, color=0x00ff00)


def parse_deger(metin):
    metin = metin.upper().replace(",", "").replace(" ", "")
    multi = 1
    if metin.endswith("B"):
        multi = 1_000_000_000
        metin = metin[:-1]
    elif metin.endswith("M"):
        multi = 1_000_000
        metin = metin[:-1]
    elif metin.endswith("K"):
        multi = 1_000
        metin = metin[:-1]
    try:
        return float(metin) * multi
    except ValueError:
        return None


def format_deger(sayi):
    if sayi >= 1_000_000_000:
        val = sayi / 1_000_000_000
        return f"{int(val)}B" if val.is_integer() else f"{val:.1f}B"
    elif sayi >= 1_000_000:
        val = sayi / 1_000_000
        return f"{int(val)}M" if val.is_integer() else f"{val:.1f}M"
    elif sayi >= 1_000:
        val = sayi / 1_000
        return f"{int(val)}K" if val.is_integer() else f"{val:.1f}K"
    return str(int(sayi))


def deger_isle(isim, miktar_str, islem):
    parcalar = [p.strip() for p in isim.split("|")]
    if len(parcalar) < 2:
        return None, "İsim formatı hatalı! Format: Ad | 1M | ..."
    mevcut = parse_deger(parcalar[1])
    if mevcut is None:
        return None, "Mevcut değer okunamadı!"
    eklenecek = parse_deger(miktar_str)
    if eklenecek is None:
        return None, f"{miktar_str} geçersiz bir değer!"
    yeni = mevcut + eklenecek if islem == "ekle" else mevcut - eklenecek
    if yeni < 0:
        yeni = 0
    parcalar[1] = format_deger(yeni)
    islem_str = f"+{miktar_str}" if islem == "ekle" else f"-{miktar_str}"
    return " | ".join(parcalar), islem_str


def antrenman_deger_ekle(isim, miktar_m):
    yeni_isim, _ = deger_isle(isim, str(miktar_m) + "M", "ekle")
    if yeni_isim is None:
        return None, None, None
    parcalar = [p.strip() for p in yeni_isim.split("|")]
    eski_parcalar = [p.strip() for p in isim.split("|")]
    eski_d = eski_parcalar[1].strip() if len(eski_parcalar) >= 2 else "?"
    yeni_d = parcalar[1].strip() if len(parcalar) >= 2 else "?"
    return yeni_isim, eski_d, yeni_d


async def log_deger_gonder(guild, yetkili, uye, eski, yeni, tur, sebep="Belirtilmedi"):
    if DEGER_LOG_KANAL_ID == 0:
        return
    kanal = bot.get_channel(DEGER_LOG_KANAL_ID)
    if not kanal:
        return
    embed = discord.Embed(title=tur, color=0x5865F2, timestamp=datetime.datetime.now())
    embed.add_field(name="Yetkili", value=yetkili.mention, inline=True)
    embed.add_field(name="Üye", value=uye.mention, inline=True)
    embed.add_field(name="Eski Değer", value=eski, inline=True)
    embed.add_field(name="Yeni Değer", value=yeni, inline=True)
    embed.add_field(name="Sebep", value=sebep, inline=False)
    await kanal.send(embed=embed)


def kayit_yetkisi_var_mi(kisi):
    if kisi.guild_permissions.administrator:
        return True
    return any(rol.id == KAYIT_YETKILI_ROL_ID for rol in kisi.roles)


def deger_yetkisi_var_mi(kisi):
    if kisi.guild_permissions.administrator:
        return True
    return any(rol.id == DEGER_YETKILI_ROL_ID for rol in kisi.roles)


# --- DEĞER KOMUTLARI ---
@bot.command(name="dver")
async def dver(ctx, uye: discord.Member, miktar: str, *, sebep: str = "Belirtilmedi"):
    try:
        if not deger_yetkisi_var_mi(ctx.author):
            return await ctx.send(embed=hata_embed("Bu komutu kullanmak için **Değer Yetkilisi** rolüne sahip olmalısın!"))
        mevcut_isim = uye.display_name
        parcalar = mevcut_isim.split("|")
        if len(parcalar) < 2:
            return await ctx.send(embed=hata_embed(
                f"❌ **{uye.display_name}** isminde '|' işareti yok!\nFormat: Ad | 1M | Takım olmalı."
            ))
        eski_deger = parcalar[1].strip()
        yeni_isim, islem_detay = deger_isle(mevcut_isim, miktar, "ekle")
        if yeni_isim is None:
            return await ctx.send(embed=hata_embed(islem_detay))
        try:
            await uye.edit(nick=yeni_isim)
        except discord.Forbidden:
            return await ctx.send(embed=hata_embed("❌ İsim değiştirilemedi! Botun rolü bu üyenin rolünden yüksek olmalı."))
        except Exception as hata:
            return await ctx.send(embed=hata_embed(f"❌ Discord hatası: {hata}"))
        deger_sayaci[ctx.author.id] = deger_sayaci.get(ctx.author.id, 0) + 1
        yeni_parcalar = yeni_isim.split("|")
        yeni_deger = yeni_parcalar[1].strip() if len(yeni_parcalar) >= 2 else "?"
        await ctx.send(embed=basari_embed(
            f"**{uye.mention}** değeri güncellendi: {islem_detay}\n📝 Yeni isim: {yeni_isim}"
        ))
        await log_deger_gonder(ctx.guild, ctx.author, uye, eski_deger, yeni_deger, "➕ Değer Eklendi", sebep)
    except Exception as e:
        await ctx.send(embed=hata_embed(f"Hata: {e}"))


@bot.command(name="dsil")
async def dsil(ctx, uye: discord.Member, miktar: str = None, *, sebep: str = "Belirtilmedi"):
    try:
        if not deger_yetkisi_var_mi(ctx.author):
            return await ctx.send(embed=hata_embed("Bu komutu kullanmak için **Değer Yetkilisi** rolüne sahip olmalısın!"))
        mevcut_isim = uye.display_name
        parcalar = mevcut_isim.split("|")
        if len(parcalar) < 2:
            return await ctx.send(embed=hata_embed(
                f"❌ **{uye.display_name}** isminde '|' işareti yok!\nFormat: Ad | 1M | Takım olmalı."
            ))
        eski_deger = parcalar[1].strip()
        if miktar is None:
            parcalar[1] = "0M"
            yeni_isim = " | ".join(parcalar)
            try:
                await uye.edit(nick=yeni_isim)
            except discord.Forbidden:
                return await ctx.send(embed=hata_embed("❌ İsim değiştirilemedi! Botun rolü bu üyenin rolünden yüksek olmalı."))
            except Exception as hata:
                return await ctx.send(embed=hata_embed(f"❌ Discord hatası: {hata}"))
            deger_sayaci[ctx.author.id] = deger_sayaci.get(ctx.author.id, 0) + 1
            await ctx.send(embed=basari_embed(
                f"**{uye.mention}** değeri sıfırlandı: {eski_deger} → 0M\n📝 Yeni isim: {yeni_isim}"
            ))
            await log_deger_gonder(ctx.guild, ctx.author, uye, eski_deger, "0M", "🔄 Değer Sıfırlandı", sebep)
            return
        yeni_isim, islem_detay = deger_isle(mevcut_isim, miktar, "çıkar")
        if yeni_isim is None:
            return await ctx.send(embed=hata_embed(islem_detay))
        try:
            await uye.edit(nick=yeni_isim)
        except discord.Forbidden:
            return await ctx.send(embed=hata_embed("❌ İsim değiştirilemedi! Botun rolü bu üyenin rolünden yüksek olmalı."))
        except Exception as hata:
            return await ctx.send(embed=hata_embed(f"❌ Discord hatası: {hata}"))
        deger_sayaci[ctx.author.id] = deger_sayaci.get(ctx.author.id, 0) + 1
        yeni_parcalar = yeni_isim.split("|")
        yeni_deger = yeni_parcalar[1].strip() if len(yeni_parcalar) >= 2 else "?"
        await ctx.send(embed=basari_embed(
            f"**{uye.mention}** değeri güncellendi: {islem_detay}\n📝 Yeni isim: {yeni_isim}"
        ))
        await log_deger_gonder(ctx.guild, ctx.author, uye, eski_deger, yeni_deger, "➖ Değer Çıkarıldı", sebep)
    except Exception as e:
        await ctx.send(embed=hata_embed(f"Hata: {e}"))


# ====================== KARİYER SİSTEMİ ======================
@bot.command(name="kariyer")
async def kariyer(ctx, uye: discord.Member = None):
    hedef = uye or ctx.author
    veri = kariyer_verileri.get(hedef.id, {"takimlar": [], "goller": 0, "asistler": 0})
    
    embed = discord.Embed(
        title=f"⚽ {hedef.display_name} — Kariyer İstatistikleri",
        color=0x5865F2,
        timestamp=datetime.datetime.now()
    )
    embed.set_thumbnail(url=hedef.display_avatar.url)
    
    takimlar_metni = "\n".join([f"• {t}" for t in veri["takimlar"]]) if veri["takimlar"] else "Henüz takım yok"
    embed.add_field(name="🏟️ Oynadığı Takımlar", value=takimlar_metni, inline=False)
    embed.add_field(name="⚽ Gol", value=f"**{veri['goller']}**", inline=True)
    embed.add_field(name="🎯 Asist", value=f"**{veri['asistler']}**", inline=True)
    embed.add_field(name="🏆 Toplam Katkı", value=f"**{veri['goller'] + veri['asistler']}**", inline=True)
    embed.set_footer(text=f"Kariyer verisi | ID: {hedef.id}")
    
    await ctx.send(embed=embed)


@bot.command(name="golekle")
async def golekle(ctx, uye: discord.Member, miktar: int = 1):
    if not lig_commander_mi(ctx.author):
        return await ctx.send(embed=hata_embed("Bu komutu kullanmak için **League Commander** rolüne sahip olmalısın!"))
    if miktar <= 0:
        return await ctx.send(embed=hata_embed("Gol sayısı 0'dan büyük olmalı!"))
    
    if uye.id not in kariyer_verileri:
        kariyer_verileri[uye.id] = {"takimlar": [], "goller": 0, "asistler": 0}
    
    kariyer_verileri[uye.id]["goller"] += miktar
    kariyer_kaydet(kariyer_verileri)
    
    await ctx.send(embed=basari_embed(
        f"⚽ **{uye.display_name}** için **+{miktar}** gol eklendi!\n"
        f"📊 Toplam Gol: **{kariyer_verileri[uye.id]['goller']}**"
    ))


@bot.command(name="asistekle")
async def asistekle(ctx, uye: discord.Member, miktar: int = 1):
    if not lig_commander_mi(ctx.author):
        return await ctx.send(embed=hata_embed("Bu komutu kullanmak için **League Commander** rolüne sahip olmalısın!"))
    if miktar <= 0:
        return await ctx.send(embed=hata_embed("Asist sayısı 0'dan büyük olmalı!"))
    
    if uye.id not in kariyer_verileri:
        kariyer_verileri[uye.id] = {"takimlar": [], "goller": 0, "asistler": 0}
    
    kariyer_verileri[uye.id]["asistler"] += miktar
    kariyer_kaydet(kariyer_verileri)
    
    await ctx.send(embed=basari_embed(
        f"🎯 **{uye.display_name}** için **+{miktar}** asist eklendi!\n"
        f"📊 Toplam Asist: **{kariyer_verileri[uye.id]['asistler']}**"
    ))


@bot.command(name="takimekle")
async def takimekle(ctx, uye: discord.Member, *, takim_adi: str):
    if not lig_commander_mi(ctx.author):
        return await ctx.send(embed=hata_embed("Bu komutu kullanmak için **League Commander** rolüne sahip olmalısın!"))
    
    if uye.id not in kariyer_verileri:
        kariyer_verileri[uye.id] = {"takimlar": [], "goller": 0, "asistler": 0}
    
    kariyer_verileri[uye.id]["takimlar"].append(takim_adi)
    kariyer_kaydet(kariyer_verileri)
    
    await ctx.send(embed=basari_embed(
        f"🏟️ **{uye.display_name}** için **{takim_adi}** takımı kaydedildi!\n"
        f"📋 Kariyer geçmişi: {', '.join(kariyer_verileri[uye.id]['takimlar'])}"
    ))


# ====================== TAKIM BASKANI DROPDOWN ======================
class TakimSecDropdown(ui.Select):
    def __init__(self, hedef: discord.Member, yeni_nick: str, yapan_id: int):
        self.hedef = hedef
        self.yeni_nick = yeni_nick
        self.yapan_id = yapan_id
        options = [
            discord.SelectOption(label=takim_adi, value=takim_adi)
            for takim_adi in TAKIM_ROLLERI.keys()
        ]
        super().__init__(placeholder="Takımı seçin...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.yapan_id:
            return await interaction.response.send_message(
                embed=hata_embed("Bu seçimi yalnızca komutu kullanan kişi yapabilir!"), ephemeral=True
            )
        takim_adi = self.values[0]
        guild = interaction.guild
        hedef = self.hedef
        yeni_nick = self.yeni_nick
        kayitli_rol = discord.utils.get(guild.roles, name=KAYITLI_ROL)
        kayitsiz_rol = discord.utils.get(guild.roles, name=KAYITSIZ_ROL)
        baskan_rol = discord.utils.get(guild.roles, name=ROL_TAKIM_BASKANI)
        takim_rol = guild.get_role(TAKIM_ROLLERI.get(takim_adi, 0))
        eksik = []
        if not takim_rol: eksik.append(takim_adi)
        if not kayitli_rol: eksik.append(KAYITLI_ROL)
        if not baskan_rol: eksik.append(ROL_TAKIM_BASKANI)
        if eksik:
            return await interaction.response.edit_message(
                embed=hata_embed(f"Sunucuda şu roller bulunamadı: {', '.join(eksik)}"), view=None
            )
        if kayitsiz_rol and kayitsiz_rol in hedef.roles:
            try:
                await hedef.remove_roles(kayitsiz_rol)
            except:
                pass
        try:
            await hedef.add_roles(baskan_rol, kayitli_rol, takim_rol)
        except Exception as e:
            return await interaction.response.edit_message(embed=hata_embed(f"Rol verilemedi: {e}"), view=None)
        nick_hata = None
        try:
            await hedef.edit(nick=yeni_nick)
        except discord.Forbidden:
            nick_hata = "⚠️ Nick değiştirilemedi: Botun rolü üyenin rolünden yukarıda olmalı."
        except discord.HTTPException as e:
            nick_hata = f"⚠️ Nick değiştirilemedi: {e}"
        renk = 0x2ECC71 if not nick_hata else 0xFFA500
        sonuc = discord.Embed(title="✅ Başkan Kaydı Tamamlandı", color=renk, timestamp=datetime.datetime.now())
        sonuc.add_field(name="👤 Üye", value=hedef.mention, inline=True)
        sonuc.add_field(name="📝 Nick", value=f"{yeni_nick}", inline=True)
        sonuc.add_field(name="🎭 Verilen Roller", value=f"{ROL_TAKIM_BASKANI}, {KAYITLI_ROL}, {takim_adi}", inline=False)
        if nick_hata:
            sonuc.add_field(name="❗ Uyarı", value=nick_hata, inline=False)
        sonuc.set_footer(text=f"Kaydeden: {interaction.user.display_name}")
        self.disabled = True
        await interaction.response.edit_message(embed=sonuc, view=None)


class TakimSecView(ui.View):
    def __init__(self, hedef: discord.Member, yeni_nick: str, yapan_id: int):
        super().__init__(timeout=60)
        self.add_item(TakimSecDropdown(hedef=hedef, yeni_nick=yeni_nick, yapan_id=yapan_id))

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True


# ====================== KAYIT KOMUTU ======================
class KayitSecimView(discord.ui.View):
    def __init__(self, hedef: discord.Member, yeni_nick: str, yapan: discord.Member):
        super().__init__(timeout=60)
        self.hedef = hedef
        self.yeni_nick = yeni_nick
        self.yapan = yapan
        self.kullanildi = False

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.yapan.id:
            await interaction.response.send_message(
                embed=hata_embed("Bu butonları yalnızca komutu kullanan kişi kullanabilir!"), ephemeral=True
            )
            return False
        return True

    async def kayit_yap(self, interaction: discord.Interaction, rol_adi: str):
        if self.kullanildi:
            return await interaction.response.send_message(
                embed=hata_embed("Bu kayıt zaten tamamlandı!"), ephemeral=True
            )
        self.kullanildi = True
        kayit_sayaci[self.yapan.id] = kayit_sayaci.get(self.yapan.id, 0) + 1
        guild = interaction.guild
        hedef = self.hedef
        yeni_nick = self.yeni_nick
        secilen_rol = discord.utils.get(guild.roles, name=rol_adi)
        kayitli_rol = discord.utils.get(guild.roles, name=KAYITLI_ROL)
        kayitsiz_rol = discord.utils.get(guild.roles, name=KAYITSIZ_ROL)
        if not secilen_rol or not kayitli_rol:
            await interaction.response.edit_message(embed=hata_embed("Rol bulunamadı!"), view=None)
            return
        if kayitsiz_rol and kayitsiz_rol in hedef.roles:
            try:
                await hedef.remove_roles(kayitsiz_rol)
            except:
                pass
        try:
            await hedef.add_roles(secilen_rol, kayitli_rol)
        except Exception as e:
            await interaction.response.edit_message(embed=hata_embed(f"Rol verilemedi: {e}"), view=None)
            return
        nick_hata = None
        try:
            await hedef.edit(nick=yeni_nick)
        except discord.Forbidden:
            nick_hata = "⚠️ Bot bu üyeyi düzenleyemiyor."
        except discord.HTTPException as e:
            nick_hata = f"⚠️ Nick değiştirilemedi: {e}"
        renk = 0x2ECC71 if not nick_hata else 0xFFA500
        sonuc = discord.Embed(title="✅ Kayıt Tamamlandı", color=renk, timestamp=datetime.datetime.now())
        sonuc.add_field(name="👤 Üye", value=hedef.mention, inline=True)
        sonuc.add_field(name="📝 Nick", value=f"{yeni_nick}", inline=True)
        sonuc.add_field(name="🎭 Verilen Rol", value=f"{rol_adi} + {KAYITLI_ROL}", inline=False)
        if nick_hata:
            sonuc.add_field(name="❗ Uyarı", value=nick_hata, inline=False)
        sonuc.set_footer(text=f"Kaydeden: {interaction.user.display_name}")
        await interaction.response.edit_message(embed=sonuc, view=None)

    @discord.ui.button(label="Üye", style=discord.ButtonStyle.primary, emoji="👤")
    async def uye_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.kayit_yap(interaction, ROL_UYE)

    @discord.ui.button(label="Futbolcu", style=discord.ButtonStyle.success, emoji="⚽")
    async def futbolcu_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.kayit_yap(interaction, ROL_FUTBOLCU)

    @discord.ui.button(label="Takım Başkanı", style=discord.ButtonStyle.danger, emoji="👑")
    async def takim_baskani_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.kullanildi:
            return await interaction.response.send_message(
                embed=hata_embed("Bu kayıt zaten başlatıldı!"), ephemeral=True
            )
        self.kullanildi = True
        takim_view = TakimSecView(hedef=self.hedef, yeni_nick=self.yeni_nick, yapan_id=self.yapan.id)
        embed = discord.Embed(
            title="👑 Takım Başkanı — Takım Seçin",
            description=(
                f"**{self.hedef.mention}** için hangi takımın başkanı olacağını aşağıdaki menüden seçin.\n"
                f"📝 Nick: {self.yeni_nick}"
            ),
            color=0x5865F2
        )
        embed.set_footer(text="Menüden bir takım seçin")
        await interaction.response.edit_message(embed=embed, view=takim_view)

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True


@bot.command(name="k")
async def kayit(ctx, uye: discord.Member, *, bilgi: str):
    if not kayit_yetkisi_var_mi(ctx.author):
        return await ctx.send(embed=hata_embed("Bu komutu kullanmak için **Kayıt Yetkilisi** rolüne sahip olmalısın!"))
    yeni_nick = bilgi.strip()
    if not yeni_nick:
        return await ctx.send(embed=hata_embed("Kullanım: .k @üye L.Messi | 1M | SNT"))
    embed = discord.Embed(
        title="📋 Kayıt Türü Seç",
        description=f"**{uye.mention}** için kayıt türü seçin.\n📝 Nick: {yeni_nick}",
        color=0x5865F2
    )
    embed.set_footer(text="Aşağıdaki butonlardan birini seçin")
    view = KayitSecimView(hedef=uye, yeni_nick=yeni_nick, yapan=ctx.author)
    await ctx.send(embed=embed, view=view)


# --- ANTRENMAN KOMUTU --- (JSON ile kalıcı)
@bot.command(name="antrenman")
async def antrenman(ctx):
    if ANTRENMAN_KANAL_ID != 0 and ctx.channel.id != ANTRENMAN_KANAL_ID:
        return await ctx.send("❌ Bu komutu sadece antrenman kanalında kullanabilirsin!")
    uye = ctx.author
    mevcut = antrenman_sayac.get(uye.id, 0) + 1
    if mevcut > 10:
        mevcut = 1
    antrenman_sayac[uye.id] = mevcut
    antrenman_kaydet(antrenman_sayac)

    dolu = "🟩" * mevcut
    bos = "⬜" * (10 - mevcut)
    embed = discord.Embed(
        title="🏋️ Antrenman",
        description=f"{uye.mention} antrenman yapıyor!\n\n**{mevcut}/10**\n{dolu}{bos}",
        color=0xF1C40F if mevcut < 10 else 0x2ECC71
    )
    if mevcut < 10:
        embed.set_footer(text=f"{10 - mevcut} antrenman daha kaldı!")
        await ctx.send(embed=embed)
    else:
        embed.set_footer(text="✅ Antrenman tamamlandı! +3M ekleniyor...")
        await ctx.send(embed=embed)
        try:
            uye = await ctx.guild.fetch_member(ctx.author.id)
        except Exception:
            uye = ctx.author
        guncel_isim = uye.nick if uye.nick else uye.name
        yeni_isim, eski_d, yeni_d = antrenman_deger_ekle(guncel_isim, 3)
        if yeni_isim is not None:
            try:
                await uye.edit(nick=yeni_isim)
                await ctx.send(embed=basari_embed(
                    f"💰 {uye.mention} antrenman ödülü aldı: **+3M**\n"
                    f"📊 Değer: {eski_d} → {yeni_d}\n"
                    f"📝 Yeni isim: {yeni_isim}"
                ))
                await log_deger_gonder(
                    ctx.guild, ctx.author, uye, eski_d, yeni_d,
                    "🏋️ Antrenman Tamamlandı (+3M)", "Antrenman ödülü verildi"
                )
            except (discord.Forbidden, discord.HTTPException):
                await ctx.send(embed=basari_embed(
                    f"💰 {uye.mention} antrenman ödülü: **+3M** kazandı!\n"
                    f"📊 Değer: {eski_d} → {yeni_d}\n"
                    f"⚠️ İsim güncellenemedi, manuel güncelle: {yeni_isim}"
                ))
                await log_deger_gonder(
                    ctx.guild, ctx.author, uye, eski_d, yeni_d,
                    "🏋️ Antrenman Tamamlandı (+3M)", "Antrenman ödülü (İsim değiştirilemedi)"
                )
        else:
            await ctx.send(embed=hata_embed(
                f"{uye.mention} 10/10 tamamladı fakat isim formatı hatalı!\n"
                f"Format: Ad | 1M | takım | SNT olmalı."
            ))
        antrenman_sayac[uye.id] = 0
        antrenman_kaydet(antrenman_sayac)


# ====================== KAP SİSTEMİ ======================
def boslari_x(deger):
    return deger.strip() if deger and deger.strip() else "x"


def takim_kontrol(takim_adi):
    for listedeki in TAKIM_ROLLERI.keys():
        if takim_adi.upper() == listedeki.upper():
            return listedeki
    return None


async def kap_rol_islemi(member: discord.Member, eski_takim: str, yeni_takim: str = None):
    try:
        if eski_takim and eski_takim.lower() != "x":
            eski_adi = takim_kontrol(eski_takim)
            if eski_adi:
                eski_rol_id = TAKIM_ROLLERI[eski_adi]
                eski_rol = member.guild.get_role(eski_rol_id)
                if eski_rol and eski_rol in member.roles:
                    await member.remove_roles(eski_rol)
        if yeni_takim and yeni_takim.lower() != "x":
            yeni_adi = takim_kontrol(yeni_takim)
            if yeni_adi:
                yeni_rol_id = TAKIM_ROLLERI[yeni_adi]
                yeni_rol = member.guild.get_role(yeni_rol_id)
                if yeni_rol and yeni_rol not in member.roles:
                    await member.add_roles(yeni_rol)
            else:
                return False, yeni_takim
    except:
        pass
    return True, None


class TransferDevamView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label="Devam Et (2. Kısım)", style=discord.ButtonStyle.success, emoji="➡️")
    async def devam_buton(self, interaction: discord.Interaction, button: ui.Button):
        user_data = kap_bellek.get(interaction.user.id)
        if not user_data:
            return await interaction.response.send_message("❌ Bir hata oluştu.", ephemeral=True)
        await interaction.response.send_modal(TransferIkinci(user_data))


class TransferBirinci(ui.Modal, title="📌 TRANSFER (1/2)"):
    oid = ui.TextInput(label="Oyuncu Discord ID", min_length=17, max_length=20)
    oyuncu_ismi = ui.TextInput(label="Oyuncu İsmi")
    eski_takim = ui.TextInput(label="Eski Takımı", placeholder="Örn: GALATASARAY")
    bonservis = ui.TextInput(label="Bonservis Bedeli")
    yillik_maas = ui.TextInput(label="Yıllık Maaş")

    async def on_submit(self, interaction: discord.Interaction):
        eski = self.eski_takim.value.strip()
        if eski.lower() != "x" and not takim_kontrol(eski):
            await interaction.response.send_message(
                f"❌ **{eski}** geçersiz bir takım adı!\n\n📋 Geçerli takımlar:\n" +
                "\n".join([f"• {t}" for t in TAKIM_ROLLERI.keys()]),
                ephemeral=True
            )
            return
        kap_bellek[interaction.user.id] = {
            "oid": self.oid.value, "oyuncu": self.oyuncu_ismi.value,
            "eski": self.eski_takim.value, "bonservis": self.bonservis.value,
            "yillik_maas": self.yillik_maas.value
        }
        await interaction.response.send_message(
            "✅ 1. kısım alındı. 2. kısma geçmek için butona basın.",
            ephemeral=True, view=TransferDevamView()
        )


class TransferIkinci(ui.Modal, title="📌 TRANSFER (2/2)"):
    def __init__(self, data1):
        super().__init__()
        self.data1 = data1
        self.yeni_takim = ui.TextInput(label="Yeni Takımı", placeholder="Örn: FENERBAHÇE")
        self.sozlesme_suresi = ui.TextInput(label="Sözleşme Süresi")
        self.bitis_sezonu = ui.TextInput(label="Sözleşme Bitiş Sezonu")
        self.fesh_tazminati = ui.TextInput(label="Tek Taraflı Fesh Tazminatı")
        self.serbest_kalma = ui.TextInput(label="Serbest Kalma Bedeli")
        for item in [self.yeni_takim, self.sozlesme_suresi, self.bitis_sezonu, self.fesh_tazminati, self.serbest_kalma]:
            self.add_item(item)

    async def on_submit(self, interaction: discord.Interaction):
        yeni = self.yeni_takim.value.strip()
        if yeni.lower() != "x" and not takim_kontrol(yeni):
            await interaction.response.send_message(
                f"❌ **{yeni}** geçersiz bir takım adı!\n\n📋 Geçerli takımlar:\n" +
                "\n".join([f"• {t}" for t in TAKIM_ROLLERI.keys()]),
                ephemeral=True
            )
            return
        await gonder_transfer(interaction, self)


async def gonder_transfer(interaction, modal):
    try:
        user_id = interaction.user.id
        if user_id in kap_bellek:
            del kap_bellek[user_id]
        member = await interaction.guild.fetch_member(int(modal.data1["oid"]))
        eski = boslari_x(modal.data1["eski"])
        yeni = boslari_x(modal.yeni_takim.value)
        basarili, hatali_takim = await kap_rol_islemi(member, eski, yeni)
        if not basarili:
            await interaction.response.send_message(
                f"❌ **{hatali_takim}** geçersiz bir takım! Rol verilmedi.", ephemeral=True
            )
            return
        embed = discord.Embed(title="**TRANSFER KAP AÇIKLAMASI**", color=0x3498db, timestamp=datetime.datetime.now())
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="Oyuncu İsmi", value=boslari_x(modal.data1["oyuncu"]), inline=False)
        embed.add_field(name="Eski Takımı", value=eski, inline=True)
        embed.add_field(name="Bonservis Bedeli", value=boslari_x(modal.data1["bonservis"]), inline=True)
        embed.add_field(name="Yıllık Maaş", value=boslari_x(modal.data1["yillik_maas"]), inline=True)
        embed.add_field(name="Yeni Takımı", value=yeni, inline=True)
        embed.add_field(name="Sözleşme Süresi", value=boslari_x(modal.sozlesme_suresi.value), inline=True)
        embed.add_field(name="Sözleşme Bitiş Sezonu", value=boslari_x(modal.bitis_sezonu.value), inline=True)
        embed.add_field(name="Tek Taraflı Fesh Tazminatı", value=boslari_x(modal.fesh_tazminati.value), inline=True)
        embed.add_field(name="Serbest Kalma Bedeli", value=boslari_x(modal.serbest_kalma.value), inline=True)
        kanal = bot.get_channel(KAP_KANAL_ID)
        if kanal:
            await kanal.send(embed=embed)
            await interaction.response.send_message("✅ Transfer KAP kanalına gönderildi!", ephemeral=True)
        else:
            await interaction.response.send_message("❌ KAP kanalı bulunamadı!", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ Hata: {e}", ephemeral=True)


class KiralikDevamView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label="Devam Et (2. Kısım)", style=discord.ButtonStyle.success, emoji="➡️")
    async def devam_buton(self, interaction: discord.Interaction, button: ui.Button):
        user_data = kap_bellek.get(interaction.user.id)
        if not user_data:
            return await interaction.response.send_message("❌ Bir hata oluştu.", ephemeral=True)
        await interaction.response.send_modal(KiralikIkinci(user_data))


class KiralikBirinci(ui.Modal, title="📌 KİRALIK (1/2)"):
    oid = ui.TextInput(label="Oyuncu Discord ID", min_length=17, max_length=20)
    oyuncu_ismi = ui.TextInput(label="Oyuncu İsmi")
    eski_takim = ui.TextInput(label="Eski Takımı", placeholder="Örn: GALATASARAY")
    kiralama_bedeli = ui.TextInput(label="Kiralama Bedeli")
    yillik_maas = ui.TextInput(label="Yıllık Maaş ve Ödeyicisi", placeholder="Örn: 5M / Galatasaray")

    async def on_submit(self, interaction: discord.Interaction):
        eski = self.eski_takim.value.strip()
        if eski.lower() != "x" and not takim_kontrol(eski):
            await interaction.response.send_message(
                f"❌ **{eski}** geçersiz bir takım adı!\n\n📋 Geçerli takımlar:\n" +
                "\n".join([f"• {t}" for t in TAKIM_ROLLERI.keys()]),
                ephemeral=True
            )
            return
        kap_bellek[interaction.user.id] = {
            "oid": self.oid.value, "oyuncu": self.oyuncu_ismi.value,
            "eski": self.eski_takim.value, "kiralama_bedeli": self.kiralama_bedeli.value,
            "yillik_maas": self.yillik_maas.value
        }
        await interaction.response.send_message(
            "✅ 1. kısım alındı. 2. kısma geçmek için butona basın.",
            ephemeral=True, view=KiralikDevamView()
        )


class KiralikIkinci(ui.Modal, title="📌 KİRALIK (2/2)"):
    def __init__(self, data1):
        super().__init__()
        self.data1 = data1
        self.yeni_takim = ui.TextInput(label="Yeni Takımı", placeholder="Örn: FENERBAHÇE")
        self.imza_primi = ui.TextInput(label="İmza Primi")
        self.sure_ve_bitis = ui.TextInput(label="Sözleşme Süresi ve Bitiş Sezonu", placeholder="Örn: 2 Yıl / 2026")
        self.geri_cagirma = ui.TextInput(label="Geri Çağırma Bedeli")
        for item in [self.yeni_takim, self.imza_primi, self.sure_ve_bitis, self.geri_cagirma]:
            self.add_item(item)

    async def on_submit(self, interaction: discord.Interaction):
        yeni = self.yeni_takim.value.strip()
        if yeni.lower() != "x" and not takim_kontrol(yeni):
            await interaction.response.send_message(
                f"❌ **{yeni}** geçersiz bir takım adı!\n\n📋 Geçerli takımlar:\n" +
                "\n".join([f"• {t}" for t in TAKIM_ROLLERI.keys()]),
                ephemeral=True
            )
            return
        await gonder_kiralik(interaction, self)


async def gonder_kiralik(interaction, modal):
    try:
        user_id = interaction.user.id
        if user_id in kap_bellek:
            del kap_bellek[user_id]
        member = await interaction.guild.fetch_member(int(modal.data1["oid"]))
        eski = boslari_x(modal.data1["eski"])
        yeni = boslari_x(modal.yeni_takim.value)
        basarili, hatali_takim = await kap_rol_islemi(member, eski, yeni)
        if not basarili:
            await interaction.response.send_message(
                f"❌ **{hatali_takim}** geçersiz bir takım! Rol verilmedi.", ephemeral=True
            )
            return
        maas_parcalari = [p.strip() for p in modal.data1["yillik_maas"].split("/")]
        maas = maas_parcalari[0] if len(maas_parcalari) > 0 else "?"
        odeyici = maas_parcalari[1] if len(maas_parcalari) > 1 else "?"
        sure_parcalari = [p.strip() for p in modal.sure_ve_bitis.value.split("/")]
        sure = sure_parcalari[0] if len(sure_parcalari) > 0 else "?"
        bitis = sure_parcalari[1] if len(sure_parcalari) > 1 else "?"
        embed = discord.Embed(title="**KİRALIK KAP AÇIKLAMASI**", color=0xf1c40f, timestamp=datetime.datetime.now())
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="Oyuncu İsmi", value=boslari_x(modal.data1["oyuncu"]), inline=False)
        embed.add_field(name="Eski Takımı", value=eski, inline=True)
        embed.add_field(name="Kiralama Bedeli", value=boslari_x(modal.data1["kiralama_bedeli"]), inline=True)
        embed.add_field(name="Yıllık Maaş", value=boslari_x(maas), inline=True)
        embed.add_field(name="Maaş Ödeyicisi", value=boslari_x(odeyici), inline=True)
        embed.add_field(name="İmza Primi", value=boslari_x(modal.imza_primi.value), inline=True)
        embed.add_field(name="Yeni Takımı", value=yeni, inline=True)
        embed.add_field(name="Sözleşme Süresi", value=boslari_x(sure), inline=True)
        embed.add_field(name="Sözleşme Bitiş Sezonu", value=boslari_x(bitis), inline=True)
        embed.add_field(name="Geri Çağırma Bedeli", value=boslari_x(modal.geri_cagirma.value), inline=True)
        kanal = bot.get_channel(KAP_KANAL_ID)
        if kanal:
            await kanal.send(embed=embed)
            await interaction.response.send_message("✅ Kiralama KAP kanalına gönderildi!", ephemeral=True)
        else:
            await interaction.response.send_message("❌ KAP kanalı bulunamadı!", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ Hata: {e}", ephemeral=True)


class YenilemeModal(ui.Modal, title="✍️ SÖZLEŞME YENİLEME"):
    oid = ui.TextInput(label="Oyuncu Discord ID", min_length=17, max_length=20)
    oyuncu_ismi = ui.TextInput(label="Oyuncu İsmi")
    eski_maas = ui.TextInput(label="Eski Yıllık Maaşı")
    yeni_maas = ui.TextInput(label="Yeni Yıllık Maaşı")
    takim = ui.TextInput(label="Takım", placeholder="Örn: GALATASARAY")

    async def on_submit(self, interaction: discord.Interaction):
        try:
            takim_adi = self.takim.value.strip()
            if takim_adi.lower() != "x" and not takim_kontrol(takim_adi):
                await interaction.response.send_message(
                    f"❌ **{takim_adi}** geçersiz bir takım adı!\n\n📋 Geçerli takımlar:\n" +
                    "\n".join([f"• {t}" for t in TAKIM_ROLLERI.keys()]),
                    ephemeral=True
                )
                return
            member = await interaction.guild.fetch_member(int(self.oid.value))
            await kap_rol_islemi(member, boslari_x(self.takim.value))
            embed = discord.Embed(
                title="**SÖZLEŞME YENİLEME KAP AÇIKLAMASI**",
                color=0x2ecc71,
                timestamp=datetime.datetime.now()
            )
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.add_field(name="Oyuncu İsmi", value=boslari_x(self.oyuncu_ismi.value), inline=False)
            embed.add_field(name="Eski Yıllık Maaşı", value=boslari_x(self.eski_maas.value), inline=True)
            embed.add_field(name="Yeni Yıllık Maaşı", value=boslari_x(self.yeni_maas.value), inline=True)
            embed.add_field(name="Takım", value=boslari_x(self.takim.value), inline=True)
            kanal = bot.get_channel(KAP_KANAL_ID)
            if kanal:
                await kanal.send(embed=embed)
                await interaction.response.send_message("✅ Sözleşme yenileme gönderildi!", ephemeral=True)
            else:
                await interaction.response.send_message("❌ KAP kanalı bulunamadı!", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Hata: {e}", ephemeral=True)


class FESHModal(ui.Modal, title="🚫 SÖZLEŞME FESİH"):
    oid = ui.TextInput(label="Oyuncu Discord ID", min_length=17, max_length=20)
    oyuncu_ismi = ui.TextInput(label="Oyuncu İsmi")
    fesh_bedeli = ui.TextInput(label="Fesh Bedeli")
    eski_takim = ui.TextInput(label="Eski Takım", placeholder="Örn: GALATASARAY")
    fesh_sebebi = ui.TextInput(label="Fesh Sebebi", style=discord.TextStyle.paragraph)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            takim_adi = self.eski_takim.value.strip()
            if takim_adi.lower() != "x" and not takim_kontrol(takim_adi):
                await interaction.response.send_message(
                    f"❌ **{takim_adi}** geçersiz bir takım adı!\n\n📋 Geçerli takımlar:\n" +
                    "\n".join([f"• {t}" for t in TAKIM_ROLLERI.keys()]),
                    ephemeral=True
                )
                return
            member = await interaction.guild.fetch_member(int(self.oid.value))
            await kap_rol_islemi(member, boslari_x(self.eski_takim.value))
            embed = discord.Embed(
                title="**FESİH KAP AÇIKLAMASI**",
                color=0xe74c3c,
                timestamp=datetime.datetime.now()
            )
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.add_field(name="Oyuncu İsmi", value=boslari_x(self.oyuncu_ismi.value), inline=False)
            embed.add_field(name="Fesh Bedeli", value=boslari_x(self.fesh_bedeli.value), inline=True)
            embed.add_field(name="Eski Takım", value=boslari_x(self.eski_takim.value), inline=True)
            embed.add_field(name="Fesh Sebebi", value=boslari_x(self.fesh_sebebi.value), inline=False)
            kanal = bot.get_channel(KAP_KANAL_ID)
            if kanal:
                await kanal.send(embed=embed)
                await interaction.response.send_message("✅ FESH işlemi KAP kanalına gönderildi!", ephemeral=True)
            else:
                await interaction.response.send_message("❌ KAP kanalı bulunamadı!", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Hata: {e}", ephemeral=True)


class KAPPaneli(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label="Transfer", style=discord.ButtonStyle.primary, emoji="🔄")
    async def transfer(self, interaction: discord.Interaction, button):
        await interaction.response.send_modal(TransferBirinci())

    @ui.button(label="Kiralama", style=discord.ButtonStyle.secondary, emoji="🔑")
    async def kiralama(self, interaction: discord.Interaction, button):
        await interaction.response.send_modal(KiralikBirinci())

    @ui.button(label="Sözleşme Yenile", style=discord.ButtonStyle.success, emoji="✍️")
    async def yenileme(self, interaction: discord.Interaction, button):
        await interaction.response.send_modal(YenilemeModal())

    @ui.button(label="FESH", style=discord.ButtonStyle.danger, emoji="✂️")
    async def fesh(self, interaction: discord.Interaction, button):
        await interaction.response.send_modal(FESHModal())


@bot.command()
async def kap(ctx):
    takim_listesi = "\n".join([f"• {t}" for t in TAKIM_ROLLERI.keys()])
    embed = discord.Embed(
        title="📣 NOVA PLUS | KAP YÖNETİM PANELİ",
        description=(
            f"Aşağıdan istediğiniz işlemi seçin:\n"
            f"*(Transfer ve Kiralama işlemleri 2 aşamalıdır)*\n\n"
            f"📋 **Geçerli Takımlar:**\n{takim_listesi}"
        ),
        color=0x2f3136
    )
    await ctx.send(embed=embed, view=KAPPaneli())


# ====================== ETKİNLİK SİSTEMİ ======================
OYUNLAR = {
    "🎯 Değer Tahmini": {
        "aciklama": "Yetkili rastgele bir oyuncu seçer, herkes o oyuncunun değerini tahmin eder. En yakın olan kazanır!",
        "nasil": "Yetkili .ara [isim] ile oyuncuyu bulur. Herkes sohbete tahminini yazar. En yakın tahmin eden kazanır!",
        "katilimci": "2–16 kişi",
        "sure": "5–10 dakika",
        "emoji": "🎯"
    },
    "🃏 Yüksek / Düşük": {
        "aciklama": "Yetkili bir oyuncu gösterir, sıradaki oyuncunun değeri daha mı yüksek, daha mı düşük?",
        "nasil": "Sırayla **Yüksek** veya **Düşük** yazılır. Yetkili doğruluğu kontrol eder. 3 yanlış yapan elenecek!",
        "katilimci": "2+ kişi",
        "sure": "5–20 dakika",
        "emoji": "🃏"
    },
    "🏆 Kim Olduğunu Bil": {
        "aciklama": "Yetkili bir oyuncu hakkında ipuçları verir (takımı, değeri, mevkii). En hızlı tahmin eden puan alır!",
        "nasil": "İpuçları birer birer verilir. Takım → Değer → Mevki sırasıyla açıklanır. İlk doğru cevaplayan **1 puan** alır!",
        "katilimci": "2+ kişi",
        "sure": "10–20 dakika",
        "emoji": "🏆"
    },
    "🎲 Şans Çarkı": {
        "aciklama": "Bot çarkı çevirir! Çıkan sonuca göre ödül veya ceza uygulanır. Kim ne çekecek, bilinmez!",
        "nasil": "Sırayla her kişi .cark yazar. Bot rastgele bir sonuç seçer. Ödül mü, ceza mı? Şansına bak!",
        "katilimci": "Herkes",
        "sure": "Sınırsız",
        "emoji": "🎲"
    },
    "⚡ Hızlı Bilgi": {
        "aciklama": "Bot futbol soruları sorar! 20 saniye içinde doğru cevaplayan puan kazanır. En çok puan toplayan şampiyon!",
        "nasil": ".bilgi komutuyla soru gelir. Herkes cevabını yazar. İlk ve doğru cevap veren 1 puan alır. 5 puana ulaşan kazanır!",
        "katilimci": "2+ kişi",
        "sure": "10–15 dakika",
        "emoji": "⚡"
    },
    "🔀 Kim Kimle Eşleşir?": {
        "aciklama": "Bot sunucudaki iki oyuncuyu rastgele eşleştirir! Antrenman partneri, transfer tahmini veya saf eğlence için!",
        "nasil": ".eslestir komutuyla bot iki kişiyi rastgele eşleştirir ve uyum yüzdesini açıklar. Eğlenceli sonuçlar garantili!",
        "katilimci": "2+ kişi",
        "sure": "5 dakika",
        "emoji": "🔀"
    },
    "🧛 Vampir Köylü": {
        "aciklama": "Klasik Vampir Köylü oyunu! Vampirler gizlice birini öldürür, Köylüler ve Doktor ise vampiri bulmaya çalışır.",
        "nasil": ".vk komutu ile başlatın ve katılın. Bot size özel rolünüzü (Vampir/Köylü/Doktor) DM'den söyler.",
        "katilimci": "4–20 kişi",
        "sure": "15–30 dakika",
        "emoji": "🧛"
    },
}

CARK_SONUCLARI = [
    ("🏆 BÜYÜK ÖDÜL", "Tebrikler! Bir yetkili sana **+5M** değer ekleyecek!", "odul", 0x2ECC71),
    ("⭐ KÜÇÜK ÖDÜL", "Tebrikler! Bir yetkili sana **+1M** değer ekleyecek!", "odul", 0x27AE60),
    ("😂 UTANÇ CEZASI", "5 dakika boyunca profilinde en utanç verici fotoğrafı kullanacaksın!", "ceza", 0xE67E22),
    ("💀 SUSTURMA CEZASI", "1 dakika sessize alındın! Çarkın adaleti böyle!", "ceza", 0xE74C3C),
    ("🔁 TEKRAR ÇEVİR", "Şans sana gülmedi! Bir kez daha çevirme hakkın var.", "notr", 0x3498DB),
    ("🌟 ŞAMPIYON UNVANI", "Bu haftalık 'Çark Şampiyonu' unvanı senin! Tebrikler!", "odul", 0xF1C40F),
]

# ====================== 200 BİLGİ SORUSU ======================
BILGI_SORULARI = [
    ("1954 Dünya Kupası'nda 'Büyük Facia' olarak bilinen olayda hangi takım favori olduğu halde ilk turda elenmiştir?", "macaristan", "🇭🇺 Macaristan — Favori olmasına rağmen elendi!"),
    ("FIFA Dünya Kupası tarihinde 'Maracanazo' olarak bilinen şok sonuca hangi maç damga vurmuştur?", "uruguay", "🇺🇾 1950'de Uruguay, Brezilya'yı kendi evinde yendi!"),
    ("Arsenal'in 'Invincibles' sezonunda kaç maçlık yenilmezlik serisi elde etti?", "49", "🏆 49 maç yenilmedi!"),
    ("Lionel Messi'nin tek sezonda en fazla gol attığı rekor kaç gol?", "91", "⚽ 2012 takvim yılında 91 gol!"),
    ("'Calciopoli' skandalı sonucu şampiyonluğu elinden alınan takım hangisidir?", "juventus", "⚫⚪ Juventus!"),
    ("2005 Şampiyonlar Ligi finalinde 3-0'dan dönen takım hangisidir?", "liverpool", "🔴 Liverpool İstanbul Mucizesi!"),
    ("Galatasaray 2000 UEFA Kupası finalinde hangi takımı yendi?", "arsenal", "🦁 Arsenal'i penaltılarla!"),
    ("Real Madrid'in ilk 'Los Galácticos' transferi kimdir?", "figo", "⭐ Luís Figo!"),
    ("FIFA kurallarına göre futbol topunun çevresi kaç cm?", "68", "📏 68-70 cm arasında!"),
    ("Türkiye'de ilk profesyonel futbol ligi hangi yılda kuruldu?", "1959", "🇹🇷 1959 yılında!"),
    ("Cristiano Ronaldo'nun Premier League'de en fazla gol attığı sezon kaç gol?", "31", "⚽ 2007-08 sezonunda 31 gol!"),
    ("Pele kaç kez Dünya Kupası kazandı?", "3", "🏆 1958, 1962, 1970!"),
    ("Hangi takım Şampiyonlar Ligi tarihinde en fazla şampiyonluğa sahiptir?", "real madrid", "👑 Real Madrid!"),
    ("Diego Maradona'nın 'Tanrı'nın Eli' golünü attığı maçta hangi takıma karşıydı?", "ingiltere", "🇦🇷 1986 Dünya Kupası İngiltere'ye karşı!"),
    ("Hangi ülke en fazla FIFA Dünya Kupası kazanmıştır?", "brezilya", "🇧🇷 Brezilya, 5 kez!"),
    ("Ronaldinho hangi takımla 2005 yılında Ballon d'Or ödülü aldı?", "barcelona", "🔵🔴 Barcelona!"),
    ("Zlatan Ibrahimovic kaç farklı Avrupa liginde gol atmıştır?", "7", "🔥 İsveç, Hollanda, İtalya, İspanya, Fransa, İngiltere, Amerika!"),
    ("Süper Lig tarihinde en fazla şampiyonluğu olan takım hangisidir?", "galatasaray", "🦁 Galatasaray!"),
    ("Fenerbahçe hangi yıl kuruludu?", "1907", "🟡🔵 1907!"),
    ("Beşiktaş'ın şampiyonluk sayısı kaçtır (yaklaşık)?", "16", "⚫⚪ 16 şampiyonluk!"),
    ("İlk Dünya Kupası hangi ülkede düzenlendi?", "uruguay", "🇺🇾 1930 Uruguay!"),
    ("UEFA Şampiyonlar Ligi tarihinin en pahalı transferi kimdir?", "neymar", "💰 Neymar 222M Euro!"),
    ("Messi kaç kez Ballon d'Or kazandı?", "8", "🌟 Rekor 8 kez!"),
    ("2022 Dünya Kupası'nı hangi takım kazandı?", "arjantin", "🇦🇷 Arjantin!"),
    ("Türkiye Milli Takımı hangi Dünya Kupası'nda 3. oldu?", "2002", "🇹🇷 2002 Güney Kore-Japonya!"),
    ("Premier League'in en fazla gol atan oyuncusu kimdir?", "alan shearer", "⚽ Alan Shearer 260 gol!"),
    ("Hangi kaleci Şampiyonlar Ligi tarihinde en fazla maç kazandı?", "iker casillas", "🧤 Iker Casillas!"),
    ("İlk UEFA Kupası'nı hangi takım kazandı?", "tottenham", "⚽ Tottenham 1972!"),
    ("Haaland hangi takımdan Manchester City'ye transfer oldu?", "dortmund", "🟡⚫ Borussia Dortmund!"),
    ("Mbappé'nin milli takımı hangi ülkedir?", "fransa", "🇫🇷 Fransa!"),
    ("Türkiye'de ilk yabancı futbolcu kısıtlaması kaç kişiydi?", "3", "📋 3 yabancı oyuncu limiti!"),
    ("Hangi Türk futbolcu Premier League'de oynamıştır?", "tugay kerimoglu", "🇹🇷 Tugay Kerimoğlu!"),
    ("Liverpool'un tarihi rakibi kimdir?", "manchester united", "🔴 Manchester United!"),
    ("El Clásico hangi iki takım arasında oynanır?", "barcelona real madrid", "🔵🔴 Barcelona vs Real Madrid!"),
    ("İlk Black Friday (transfer yasağı) döneminde hangi kural uygulandı?", "transfer yasagi", "📋 Sezon ortasında transfer yasağı!"),
    ("Münih Trajedisi hangi takımı etkiledi?", "manchester united", "✈️ Manchester United 1958!"),
    ("Yeşil kartın futbolda ne anlama geldiği bilinmektedir?", "fair play", "💚 Fair Play ödülü!"),
    ("Penaltı atışı ne zaman icat edildi?", "1891", "⚽ 1891 yılında!"),
    ("Süper Lig'de en fazla gol atan oyuncu kimdir?", "hakan sukur", "🇹🇷 Hakan Şükür!"),
    ("Galatasaray'ın tarihi şarkısı ne ile başlar?", "cimbom", "🦁 Cimbom!"),
    ("Futbolda ofsayt kuralı hangi organla belirlenir?", "fifa", "📋 FIFA!"),
    ("VAR sistemi hangi yıl Dünya Kupası'nda ilk kullanıldı?", "2018", "📹 2018 Rusya!"),
    ("Şampiyonlar Ligi marşının adı nedir?", "anthem", "🎵 UEFA Şampiyonlar Ligi Marşı!"),
    ("Tiki-taka oyun stilini dünyaya hangi takım tanıttı?", "barcelona", "🔵🔴 Barcelona!"),
    ("Hakan Şükür'ün Dünya Kupası tarihindeki en hızlı golü kaç saniyedeydi?", "11", "⚡ 11 saniye!"),
    ("Süper Lig'in ilk şampiyonu kimdir?", "fenerbahce", "🟡🔵 Fenerbahçe!"),
    ("Trabzonspor hangi yıllarda peş peşe şampiyon oldu?", "1976 1977 1978", "🏆 76-77-78!"),
    ("Serie A'yı en fazla kazanan takım hangisidir?", "juventus", "⚫⚪ Juventus!"),
    ("La Liga'yı en fazla kazanan takım hangisidir?", "real madrid", "👑 Real Madrid!"),
    ("Bundesliga'yı en fazla kazanan takım hangisidir?", "bayern", "🔴 Bayern Münih!"),
    ("Fransa Ligue 1'i en fazla kazanan takım hangisidir?", "saint etienne", "🟢 Saint-Étienne!"),
    ("Portekiz'in en büyük futbol kulübü hangisidir?", "benfica", "🦅 Benfica!"),
    ("Ajax hangi şehrin takımıdır?", "amsterdam", "🇳🇱 Amsterdam!"),
    ("Roma ile Lazio'nun derbisinin adı nedir?", "derby della capitale", "🏟️ Derby della Capitale!"),
    ("Milan derbisi kimler arasında oynanır?", "ac milan inter", "🔴⚫ AC Milan vs Inter!"),
    ("Boca Juniors ile River Plate derbisinin adı nedir?", "superclasico", "🇦🇷 Superclásico!"),
    ("Celtic ile Rangers derbisinin adı nedir?", "old firm", "🏴󠁧󠁢󠁳󠁣󠁴󠁿 Old Firm!"),
    ("Şampiyonlar Ligi'nde en hızlı hat-trick kim yaptı?", "sadio mane", "⚡ Bale ve başkaları — Hızlı hat-trickler!"),
    ("İlk Avrupa Şampiyonası'nı hangi takım kazandı?", "sovyetler birligi", "🇷🇺 Sovyetler Birliği 1960!"),
    ("İspanya kaç kez Avrupa Şampiyonu oldu?", "3", "🇪🇸 2008, 2012, ve sonrası!"),
    ("Almanya kaç kez Dünya Kupası kazandı?", "4", "🇩🇪 4 kez!"),
    ("İtalya kaç kez Dünya Kupası kazandı?", "4", "🇮🇹 4 kez!"),
    ("Fransa kaç kez Dünya Kupası kazandı?", "2", "🇫🇷 1998 ve 2018!"),
    ("Arjantin kaç kez Dünya Kupası kazandı?", "3", "🇦🇷 1978, 1986, 2022!"),
    ("Katar Dünya Kupası hangi yılda düzenlendi?", "2022", "🇶🇦 2022!"),
    ("2018 Dünya Kupası'nı hangi takım kazandı?", "fransa", "🇫🇷 Fransa!"),
    ("2014 Dünya Kupası'nı hangi takım kazandı?", "almanya", "🇩🇪 Almanya!"),
    ("2010 Dünya Kupası'nı hangi takım kazandı?", "ispanya", "🇪🇸 İspanya!"),
    ("2006 Dünya Kupası finalini kaybeden takım hangisidir?", "fransa", "🇫🇷 Fransa (Zidane olayı)!"),
    ("Zidane'ın 2006 Dünya Kupası finalinde kafa attığı oyuncu kimdir?", "materazzi", "🤦 Marco Materazzi!"),
    ("Gana'nın en ünlü futbolcusu kimdir?", "essien", "🇬🇭 Michael Essien!"),
    ("Afrika'dan Ballon d'Or kazanan ilk oyuncu kimdir?", "george weah", "🌍 George Weah!"),
    ("İngiltere Premier Ligi ne zaman kuruldu?", "1992", "🏴󠁧󠁢󠁥󠁮󠁧󠁿 1992!"),
    ("Manchester City'nin lakabı nedir?", "the citizens", "🔵 The Citizens!"),
    ("Arsenal'in stadyumunun adı nedir?", "emirates", "🔴 Emirates Stadium!"),
    ("Chelsea'nin lakabı nedir?", "the blues", "🔵 The Blues!"),
    ("Tottenham'ın yeni stadyumunun adı nedir?", "tottenham hotspur stadium", "🏟️ Tottenham Hotspur Stadium!"),
    ("Liverpool'un stadyumunun adı nedir?", "anfield", "🔴 Anfield!"),
    ("Borussia Dortmund'un stadyumunun adı nedir?", "signal iduna park", "🟡 Signal Iduna Park!"),
    ("Bayern Münih'in stadyumunun adı nedir?", "allianz arena", "🔴 Allianz Arena!"),
    ("Camp Nou hangi takımın stadyumudur?", "barcelona", "🔵🔴 Barcelona!"),
    ("Bernabéu hangi takımın stadyumudur?", "real madrid", "⚪ Real Madrid!"),
    ("San Siro hangi iki takımın stadyumudur?", "ac milan inter", "🔴⚫ AC Milan ve Inter!"),
    ("Galatasaray'ın stadyumunun adı nedir?", "rams park", "🦁 Rams Park!"),
    ("Fenerbahçe'nin stadyumunun adı nedir?", "sukru saracoglu", "🟡🔵 Şükrü Saracoğlu!"),
    ("Beşiktaş'ın stadyumunun adı nedir?", "besiktas park", "⚫⚪ Beşiktaş Park!"),
    ("Trabzonspor'un stadyumunun adı nedir?", "papara park", "🔵🟤 Papara Park!"),
    ("İlk Süper Lig sezonu hangi yılda oynandı?", "1959", "📅 1959!"),
    ("Rıdvan Dilmen hangi takımlarda oynadı?", "fenerbahce", "⭐ Fenerbahçe ve diğerleri!"),
    ("Tuncay Şanlı hangi İngiliz takımında oynadı?", "middlesbrough", "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Middlesbrough!"),
    ("Arda Turan hangi büyük İspanya takımında oynadı?", "barcelona", "🔵🔴 Barcelona!"),
    ("Caner Erkin hangi Rus takımında oynadı?", "cska moskova", "🔴 CSKA Moskova!"),
    ("Volkan Demirel hangi takımın efsane kalecisidir?", "fenerbahce", "🟡🔵 Fenerbahçe!"),
    ("Rustu Recber hangi takımda oynadı?", "barcelona", "🔵🔴 Barcelona!"),
    ("İlhan Mansız 2002 Dünya Kupası'nda hangi pozisyonda oynadı?", "forvet", "⚽ Forvet!"),
    ("Naim Süleymanoğlu futbolcu mu?", "hayir", "🏋️ Hayır, halterci!"),
    ("Türkiye'nin Dünya Kupası'ndaki en büyük galibiyeti kaç farklı?", "6", "🇹🇷 2002'de 6-0 Çin!"),
    ("Şenol Güneş hangi ülkenin teknik direktörüydü?", "turkiye", "🇹🇷 Türkiye!"),
    ("Fatih Terim'in lakabı nedir?", "imparator", "👑 İmparator!"),
    ("Mustafa Denizli'nin lakabı nedir?", "aslan parca", "🦁 Aslan Parça!"),
    ("Aykut Kocaman hangi takımı çalıştırdı?", "fenerbahce", "🟡🔵 Fenerbahçe!"),
    ("Hamza Hamzaoğlu hangi takımı 2015'te şampiyon yaptı?", "galatasaray", "🦁 Galatasaray!"),
    ("Premier League'in en kısa süreli teknik direktörü kim?", "les reed", "📋 Les Reed - 41 gün!"),
    ("Mourinho'nun lakabı nedir?", "the special one", "😎 The Special One!"),
    ("Guardiola'nın ilk şampiyonluğunu aldığı takım hangisidir?", "barcelona b", "🔵🔴 Barcelona B takımı!"),
    ("Klopp'un Dortmund'da aldığı en büyük başarı nedir?", "bundesliga", "🏆 Bundesliga şampiyonluğu!"),
    ("Wenger Arsenal'de kaç yıl görev yaptı?", "22", "📅 22 yıl!"),
    ("Futbolda 'pressing' taktik sistemini kim popülerleştirdi?", "klopp", "⚽ Jürgen Klopp!"),
    ("İlk kadın futbol Dünya Kupası hangi yılda düzenlendi?", "1991", "⚽ 1991 Çin!"),
    ("ABD kadın milli takımının en ünlü oyuncusu kimdir?", "mia hamm", "🇺🇸 Mia Hamm!"),
    ("Fußball Bundesliga ne zaman kuruldu?", "1963", "🇩🇪 1963!"),
    ("Hollanda'nın 'Turuncu' lakabı ne anlama gelir?", "ulusal renk", "🇳🇱 Hollanda'nın ulusal rengi!"),
    ("Ajax'ın taktik felsefesinin adı nedir?", "total football", "⚽ Total Football!"),
    ("Johan Cruyff hangi ülkedendir?", "hollanda", "🇳🇱 Hollanda!"),
    ("Franz Beckenbauer'ın lakabı nedir?", "der kaiser", "👑 Der Kaiser!"),
    ("Ronaldo (Nazario) kaç Dünya Kupası kazandı?", "2", "🏆 1994 ve 2002!"),
    ("Romario kaç Dünya Kupası golü attı?", "5", "⚽ 1994'te 5 gol!"),
    ("Zinedine Zidane hangi ülkedendir?", "fransa", "🇫🇷 Fransa!"),
    ("Ronaldinho'nun gerçek adı nedir?", "ronaldo assis", "🇧🇷 Ronaldo de Assis Moreira!"),
    ("Kaka hangi kulüpten Real Madrid'e transfer oldu?", "ac milan", "🔴⚫ AC Milan!"),
    ("Thierry Henry hangi ülkenin milli takımında oynadı?", "fransa", "🇫🇷 Fransa!"),
    ("Didier Drogba hangi ülkedendir?", "fildisi sahili", "🇨🇮 Fildişi Sahili!"),
    ("Samuel Eto'o hangi ülkedendir?", "kamerun", "🇨🇲 Kamerun!"),
    ("Michael Owen kaç yaşında Dünya Kupası'nda gol attı?", "18", "⚽ 18 yaşında!"),
    ("Wayne Rooney Premier League'de kaç gol attı?", "208", "🏴󠁧󠁢󠁥󠁮󠁧󠁿 208 gol!"),
    ("Steven Gerrard hangi takımda oynadı?", "liverpool", "🔴 Liverpool!"),
    ("Frank Lampard Chelsea'de kaç gol attı?", "211", "🔵 211 gol!"),
    ("Patrick Vieira hangi takımla zirveye çıktı?", "arsenal", "🔴 Arsenal!"),
    ("Paul Scholes hangi takımın efsanesidir?", "manchester united", "🔴 Manchester United!"),
    ("Roy Keane hangi takımın efsane kaptanıdır?", "manchester united", "🔴 Manchester United!"),
    ("Eric Cantona hangi İngiliz takımında oynadı?", "manchester united", "🔴 Manchester United!"),
    ("Dennis Bergkamp hangi şeyden korktuğu bilinir?", "ucak", "✈️ Uçaktan korkar!"),
    ("Roberto Carlos'un en ünlü golü hangi ülkeye atılmıştır?", "fransa", "🇫🇷 Fransa'ya karşı 1997!"),
    ("Cafu hangi pozisyonda oynadı?", "sag bek", "🏃 Sağ bek!"),
    ("İlk Altın Ayak ödülünü kim aldı?", "eusebio", "🏆 Eusébio 1968!"),
    ("Eusébio hangi ülkedendir?", "portekiz", "🇵🇹 Portekiz!"),
    ("Lev Yashin hangi ülkedendir?", "sovyetler birligi", "🇷🇺 Sovyetler Birliği!"),
    ("Lev Yashin kaç penaltı kurtardığı bilinir?", "150", "🧤 ~150 penaltı!"),
    ("İlk futbol kulübü hangisidir?", "sheffield fc", "⚽ Sheffield FC 1857!"),
    ("FIFA kaç ülke tarafından kuruldu?", "7", "🌍 7 ülke!"),
    ("FIFA ne zaman kuruldu?", "1904", "📅 1904!"),
    ("UEFA ne zaman kuruldu?", "1954", "📅 1954!"),
    ("Türk Futbol Federasyonu ne zaman kuruldu?", "1923", "🇹🇷 1923!"),
    ("Süper Lig'de sezonluk en fazla gol rekorunu kim tutmaktadır?", "hakan sukur", "🇹🇷 Hakan Şükür!"),
    ("Süper Lig'de en fazla asist rekorunu kim tutmaktadır?", "ali tandogan", "🎯 Ali Tandoğan!"),
    ("Türkiye'nin UEFA kupası tarihindeki en büyük başarısı nedir?", "galatasaray 2000", "🦁 Galatasaray 2000 UEFA Kupası!"),
    ("Galatasaray 2000 UEFA Süper Kupası'nı hangi takımla oynadı?", "real madrid", "⭐ Real Madrid!"),
    ("Beşiktaş'ın UEFA Şampiyonlar Ligi'nde en iyi sonucu nedir?", "ceyrek final", "⚫⚪ Çeyrek final!"),
    ("Fenerbahçe UEFA Şampiyonlar Ligi'nde hangi gruptan çıktı?", "grup asama", "🟡🔵 Grup aşamasına kaldı!"),
    ("Trabzonspor'un Avrupa'daki en başarılı dönemi hangi yıllardır?", "1976 1977 1978", "🏆 1976-1978!"),
    ("Türkiye Süper Kupası'nı en fazla kazanan takım hangisidir?", "galatasaray", "🦁 Galatasaray!"),
    ("Ziraat Türkiye Kupası'nı en fazla kazanan takım hangisidir?", "galatasaray", "🦁 Galatasaray!"),
    ("İlk resmi futbol maçı hangi yılda oynandı?", "1872", "⚽ İskoçya-İngiltere 1872!"),
    ("Wembley ne zaman açıldı?", "1923", "🏟️ 1923!"),
    ("Maradona'nın 1986 Dünya Kupası finalinde karşı takım kimdi?", "bati almanya", "🇩🇪 Batı Almanya!"),
    ("Roger Milla kaç yaşında Dünya Kupası'nda gol attı?", "42", "🎂 42 yaşında!"),
    ("Kamerun 1990 Dünya Kupası'nda hangi turda elendi?", "ceyrek final", "🦁 Çeyrek finalde!"),
    ("1950 Dünya Kupası'nda Brezilya'nın Uruguay'a kaybettiği maçın skoru neydi?", "2-1", "🇧🇷 Brezilya 1-2 Uruguay!"),
    ("Pelé Dünya Kupası'nda toplam kaç gol attı?", "12", "⚽ 12 gol!"),
    ("Miroslav Klose Dünya Kupası tarihinin en golcüsüdür. Kaç gol attı?", "16", "🇩🇪 16 gol!"),
    ("Ronaldo Nazario Dünya Kupası'nda toplam kaç gol attı?", "15", "🇧🇷 15 gol!"),
    ("2002 Dünya Kupası'nda Türkiye yarı finalde hangi takıma kaybetti?", "brezilya", "🇧🇷 Brezilya!"),
    ("Kemal Aydoğdu hangi Türk takımında oynadı?", "fenerbahce", "🟡🔵 Fenerbahçe!"),
    ("Okan Buruk şu anda hangi takımın teknik direktörüdür?", "galatasaray", "🦁 Galatasaray!"),
    ("Viktor İsayev Galatasaray'da hangi ülkeden geldi?", "rusya", "🇷🇺 Rusya!"),
    ("Türkiye'nin En Uzun Maç serisi kaç gündü?", "bilinmiyor", "📋 Tarihsel bilgi!"),
    ("Pelé'nin gerçek adı nedir?", "edson arantes", "🇧🇷 Edson Arantes do Nascimento!"),
    ("Johan Cruyff'un 14 numaralı formasıyla özdeşleştiği kulüp hangisidir?", "ajax", "🇳🇱 Ajax!"),
    ("Messi'nin ilk profosyonel sözleşmesi hangi yaşta imzalandı?", "13", "📝 13 yaşında!"),
    ("Ronaldo'nun Juventus'a transfer bedeli ne kadardı?", "100 milyon", "💶 ~100 Milyon Euro!"),
    ("Kylian Mbappé'nin Dünya Kupası'nı kazandığı yaş kaçtır?", "19", "🌟 19 yaşında!"),
    ("Neymar'ın Barcelona'ya transfer bedeli ne kadardı?", "57 milyon", "💶 57 Milyon Euro!"),
    ("Kevin De Bruyne hangi takımda oynar?", "manchester city", "🔵 Manchester City!"),
    ("Virgil van Dijk hangi takımda oynar?", "liverpool", "🔴 Liverpool!"),
    ("Mohamed Salah hangi ülkedendir?", "misir", "🇪🇬 Mısır!"),
    ("Robert Lewandowski kaç kez Bundesliga golcüsü oldu?", "9", "🇵🇱 9 kez!"),
    ("Luka Modrić hangi ülkedendir?", "hirvatistan", "🇭🇷 Hırvatistan!"),
    ("Modrić Ballon d'Or'u hangi yıl kazandı?", "2018", "🏆 2018!"),
    ("İvan Rakitić hangi ülkedendir?", "hirvatistan", "🇭🇷 Hırvatistan!"),
    ("Xavi Hernandez hangi takımın teknik direktörüdür?", "barcelona", "🔵🔴 Barcelona!"),
    ("Iniesta son kulübü hangi ülkedeydi?", "japonya", "🇯🇵 Japonya - Vissel Kobe!"),
    ("Sergio Busquets kariyerinin büyük bölümünü nerede geçirdi?", "barcelona", "🔵🔴 Barcelona!"),
    ("Casemiro hangi takıma transfer oldu?", "manchester united", "🔴 Manchester United!"),
    ("Marcelo Brozovic hangi ülkedendir?", "hirvatistan", "🇭🇷 Hırvatistan!"),
    ("Şampiyonlar Ligi finali 2023'ü hangi takım kazandı?", "manchester city", "🔵 Manchester City!"),
    ("Şampiyonlar Ligi finali 2022'yi hangi takım kazandı?", "real madrid", "👑 Real Madrid!"),
    ("Şampiyonlar Ligi finali 2021'i hangi takım kazandı?", "chelsea", "🔵 Chelsea!"),
    ("Şampiyonlar Ligi finali 2020'yi hangi takım kazandı?", "bayern", "🔴 Bayern Münih!"),
    ("Şampiyonlar Ligi finali 2019'u hangi takım kazandı?", "liverpool", "🔴 Liverpool!"),
    ("Hangi ülke hiç Dünya Kupası'na katılamamıştır?", "cin", "🇨🇳 Çin 2002 hariç!"),
    ("En küçük ülke olarak Dünya Kupası'na katılan hangisidir?", "trinidad", "🌍 Trinidad ve Tobago!"),
    ("EURO 2024'ü hangi takım kazandı?", "ispanya", "🇪🇸 İspanya!"),
    ("2024 Kopa Amerika'yı hangi takım kazandı?", "arjantin", "🇦🇷 Arjantin!"),
    ("Futbolda 'Gegenpressing' taktiğini kim geliştirdi?", "klopp", "⚽ Jürgen Klopp!"),
    ("Hangi teknik direktör hem oyuncu hem teknik direktör olarak Dünya Kupası kazandı?", "didier deschamps", "🇫🇷 Didier Deschamps!"),
    ("Mario Balotelli hangi ülkenin milli takımında oynadı?", "italya", "🇮🇹 İtalya!"),
    ("Zlatan Ibrahimovic'in en çok golü olan kulübü hangisidir?", "psg", "🔵🔴 PSG!"),
    ("Antoine Griezmann hangi takımda oynamaktadır?", "atletico madrid", "🔴⚪ Atletico Madrid!"),
    ("Karim Benzema hangi ülkedendir?", "fransa", "🇫🇷 Fransa!"),
    ("Benzema Ballon d'Or'u hangi yıl kazandı?", "2022", "🏆 2022!"),
    ("Luis Suarez hangi ülkedendir?", "uruguay", "🇺🇾 Uruguay!"),
    ("Suarez'in ısırma skandalı hangi Dünya Kupası'nda oldu?", "2014", "😬 2014 Brezilya!"),
    ("Gareth Bale hangi ülkenin milli takımında oynadı?", "galler", "🏴󠁧󠁢󠁷󠁬󠁳󠁿 Galler!"),
    ("Bale'in Real Madrid'e transfer bedeli ne kadardı?", "100 milyon", "💶 ~100 Milyon Euro!"),
    ("David Beckham hangi takımla kariyer yaptı?", "manchester united", "🔴 Manchester United ve diğerleri!"),
    ("Beckham hangi ülkenin milli takımında oynadı?", "ingiltere", "🏴󠁧󠁢󠁥󠁮󠁧󠁿 İngiltere!"),
    ("Paolo Maldini kaç yıl AC Milan'da oynadı?", "25", "🔴⚫ 25 yıl!"),
    ("Alessandro Nesta hangi kulübün efsanesidir?", "ac milan", "🔴⚫ AC Milan!"),
    ("Gianluigi Buffon kaç kez Serie A şampiyonu oldu?", "10", "⚫⚪ 10 kez Juventus ile!"),
    ("Francesco Totti hangi kulüpte kariyerini geçirdi?", "roma", "🟡🔴 Roma!"),
    ("Adriano 'İmparator' lakabını hangi takımda aldı?", "inter", "⚫🔵 Inter!"),
    ("Eto'o Şampiyonlar Ligi'ni kaç farklı takımla kazandı?", "3", "🏆 Barcelona, Inter, Chelsea!"),
    ("Didier Drogba Chelsea'de kaç gol attı?", "164", "🔵 164 gol!"),
    ("Cesc Fabregas Arsenal'e kaç yaşında katıldı?", "16", "📋 16 yaşında!"),
    ("Fabregas kariyerinde kaç takımda oynadı?", "4", "⚽ Arsenal, Barça, Chelsea, Monaco!"),
    ("Claudio Ranieri Leicester City'yi şampiyon yaptığı sezon kaçıncıydı?", "2016", "🦊 2016!"),
    ("Leicester City şampiyonluk oranı ne kadardı?", "5000", "🎲 5000/1!"),
    ("Jaime Vardy bu sezon kaç gol attı?", "24", "📋 Leicester şampiyonluk sezonunda 24 gol!"),
    ("N'Golo Kante hangi küçük kulüpten keşfedildi?", "caen", "🇫🇷 Caen!"),
    ("Dimitar Berbatov hangi ülkedendir?", "bulgaristan", "🇧🇬 Bulgaristan!"),
    ("Nicolas Anelka kaç takımda oynadı?", "12", "⚽ Birçok kulüp!"),
]

kullanilan_bilgi_sorulari = []


class OyunSecDropdown(ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label=oyun_adi,
                description=veri["aciklama"][:80] + ("..." if len(veri["aciklama"]) > 80 else ""),
                emoji=veri["emoji"]
            )
            for oyun_adi, veri in OYUNLAR.items()
        ]
        super().__init__(placeholder="🎮 Bir etkinlik oyunu seçin...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        secilen = self.values[0]
        veri = OYUNLAR[secilen]
        embed = discord.Embed(
            title=f"{secilen} Etkinliği Başladı!",
            description=f"**{interaction.user.mention}** bir etkinlik başlattı!\n\n📖 **Açıklama:**\n{veri['aciklama']}",
            color=0xFF6B00,
            timestamp=datetime.datetime.now()
        )
        embed.add_field(name="📋 Nasıl Oynanır?", value=veri["nasil"], inline=False)
        embed.add_field(name="👥 Katılımcı", value=veri["katilimci"], inline=True)
        embed.add_field(name="⏱️ Süre", value=veri["sure"], inline=True)
        embed.set_footer(text=f"Başlatan: {interaction.user.display_name} | Herkes katılabilir!")
        await interaction.response.edit_message(
            embed=discord.Embed(
                title="✅ Etkinlik Başlatıldı!",
                description=f"**{secilen}** etkinliği seçildi.",
                color=0x2ECC71
            ),
            view=None
        )
        await interaction.channel.send(embed=embed)


class EtkinlikView(ui.View):
    def __init__(self):
        super().__init__(timeout=60)
        self.add_item(OyunSecDropdown())

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True


@bot.command(name="etkinlik")
async def etkinlik(ctx):
    embed = discord.Embed(
        title="🎉 ETKİNLİK PANELİ",
        description=(
            "Sunucuda eğlenceli bir etkinlik başlatmak mı istiyorsunuz?\n"
            "Aşağıdan bir oyun seçin! 🔥\n\n"
            "**Mevcut Oyunlar:**\n" +
            "\n".join([f"{v['emoji']} **{k.split(' ', 1)[1]}** — {v['aciklama'][:50]}..." for k, v in OYUNLAR.items()])
        ),
        color=0xFF6B00,
        timestamp=datetime.datetime.now()
    )
    embed.set_footer(text="Menüden bir oyun seçerek etkinliği başlatın")
    await ctx.send(embed=embed, view=EtkinlikView())


# --- ŞANS ÇARKI KOMUTU --- (Günlük limit 5, tekrar engellemesi)
@bot.command(name="cark")
async def cark(ctx, uye: discord.Member = None):
    hedef = uye or ctx.author
    bugun = datetime.date.today().isoformat()
    
    # Günlük limit kontrolü
    kullanici_cark = cark_gunluk.get(hedef.id, {"tarih": "", "sayi": 0})
    if kullanici_cark["tarih"] == bugun and kullanici_cark["sayi"] >= 5:
        return await ctx.send(embed=hata_embed(
            f"⏰ **{hedef.display_name}** günlük çark limitine ulaştı! (5/5)\nYarın tekrar dene!"
        ))
    
    if kullanici_cark["tarih"] != bugun:
        cark_gunluk[hedef.id] = {"tarih": bugun, "sayi": 0}
    
    # Aynı sonucu arka arkaya verme
    son_sonuc = son_cark_sonucu.get(hedef.id, -1)
    kullanilabilir = [i for i in range(len(CARK_SONUCLARI)) if i != son_sonuc]
    secilen_index = random.choice(kullanilabilir)
    son_cark_sonucu[hedef.id] = secilen_index
    
    cark_gunluk[hedef.id]["sayi"] += 1
    kalan = 5 - cark_gunluk[hedef.id]["sayi"]
    
    animasyon = await ctx.send(f"🎲 **{hedef.display_name}** için çark çevriliyor...")
    await asyncio.sleep(0.8)
    await animasyon.edit(content="🌀 **Çark dönüyor...** ◐")
    await asyncio.sleep(0.6)
    await animasyon.edit(content="🌀 **Çark dönüyor...** ◓")
    await asyncio.sleep(0.6)
    await animasyon.edit(content="🌀 **Çark dönüyor...** ◑")
    await asyncio.sleep(0.6)
    await animasyon.edit(content="🌀 **Çark yavaşlıyor...** ◒")
    await asyncio.sleep(0.8)
    
    sonuc_adi, sonuc_aciklama, tur, renk = CARK_SONUCLARI[secilen_index]
    embed = discord.Embed(title="🎡 ŞANS ÇARKI SONUCU", color=renk, timestamp=datetime.datetime.now())
    embed.add_field(name="👤 Oyuncu", value=hedef.mention, inline=True)
    embed.add_field(name="🎯 Sonuç", value=f"**{sonuc_adi}**", inline=True)
    embed.add_field(name="📋 Ne Olacak?", value=sonuc_aciklama, inline=False)
    if tur == "odul":
        embed.set_footer(text=f"🎉 Tebrikler! Şans sana güldü! | Kalan hakkın: {kalan}/5")
    elif tur == "ceza":
        embed.set_footer(text=f"😈 Çarkın adaleti işledi! | Kalan hakkın: {kalan}/5")
    else:
        embed.set_footer(text=f"🔄 Ne ödül ne ceza, ortada kaldın! | Kalan hakkın: {kalan}/5")
    await animasyon.delete()
    await ctx.send(embed=embed)


# --- HIZLI BİLGİ KOMUTU --- (200 farklı soru)
@bot.command(name="bilgi")
async def bilgi(ctx):
    if ctx.channel.id in aktif_bilgi_oyunu:
        return await ctx.send("❌ Bu kanalda zaten aktif bir bilgi oyunu var! Bitmesini bekleyin.")
    
    # Tüm sorular kullanıldıysa sıfırla
    if len(kullanilan_bilgi_sorulari) >= len(BILGI_SORULARI):
        kullanilan_bilgi_sorulari.clear()
    
    kullanilmayanlar = [i for i, _ in enumerate(BILGI_SORULARI) if i not in kullanilan_bilgi_sorulari]
    if not kullanilmayanlar:
        kullanilan_bilgi_sorulari.clear()
        kullanilmayanlar = list(range(len(BILGI_SORULARI)))
    
    secilen_index = random.choice(kullanilmayanlar)
    kullanilan_bilgi_sorulari.append(secilen_index)
    soru, cevap, aciklama = BILGI_SORULARI[secilen_index]
    
    aktif_bilgi_oyunu[ctx.channel.id] = {"cevap": cevap, "aciklama": aciklama, "soruldu": True}
    embed = discord.Embed(
        title="⚡ HIZLI BİLGİ SORUSU!",
        description=f"**{soru}**\n\n⏰ 20 saniye içinde cevapla!",
        color=0xF1C40F,
        timestamp=datetime.datetime.now()
    )
    embed.set_footer(text=f"İlk doğru cevap veren kazanır! | Soru {len(kullanilan_bilgi_sorulari)}/{len(BILGI_SORULARI)}")
    await ctx.send(embed=embed)

    def kontrol(m):
        if m.channel.id != ctx.channel.id or m.author.bot:
            return False
        return cevap.lower() in m.content.lower()

    try:
        mesaj = await bot.wait_for("message", timeout=20.0, check=kontrol)
        del aktif_bilgi_oyunu[ctx.channel.id]
        kazanan_embed = discord.Embed(
            title="✅ DOĞRU CEVAP!",
            description=f"🏆 {mesaj.author.mention} doğru cevabı buldu!\n\n💡 **Cevap:** {aciklama}",
            color=0x2ECC71
        )
        await ctx.send(embed=kazanan_embed)
    except asyncio.TimeoutError:
        if ctx.channel.id in aktif_bilgi_oyunu:
            del aktif_bilgi_oyunu[ctx.channel.id]
        sure_bitti = discord.Embed(
            title="⏰ SÜRE DOLDU!",
            description=f"Kimse doğru cevaplayamadı!\n\n💡 **Doğru Cevap:** {aciklama}",
            color=0xE74C3C
        )
        await ctx.send(embed=sure_bitti)


# --- RASTGELE EŞLEŞTİR KOMUTU ---
@bot.command(name="eslestir")
async def eslestir(ctx):
    uyeler = [m for m in ctx.guild.members if not m.bot and m.id != ctx.author.id]
    if len(uyeler) < 1:
        return await ctx.send("❌ Eşleştirme için yeterli üye yok!")
    eslesen = random.choice(uyeler)
    uyum = random.randint(1, 100)
    if uyum >= 80:
        yorum = "Mükemmel bir ikili! Sahada durdurulamaz olursunuz! 🔥"
        renk = 0x2ECC71
        emoji = "💚"
    elif uyum >= 60:
        yorum = "İyi bir eşleşme! Biraz antrenmanla harika olabilirsiniz! ⭐"
        renk = 0xF1C40F
        emoji = "💛"
    elif uyum >= 40:
        yorum = "Ortalama bir uyum. Daha fazla çalışmaya ihtiyacınız var! 💪"
        renk = 0xE67E22
        emoji = "🧡"
    else:
        yorum = "Bu eşleşme pek iyi olmadı... Ama sahada her şey mümkün! 😅"
        renk = 0xE74C3C
        emoji = "❤️"
    embed = discord.Embed(title="🔀 RASTGELE EŞLEŞTİRME", color=renk, timestamp=datetime.datetime.now())
    embed.add_field(name="👤 Oyuncu 1", value=ctx.author.mention, inline=True)
    embed.add_field(name=emoji, value=f"**%{uyum}**", inline=True)
    embed.add_field(name="👤 Oyuncu 2", value=eslesen.mention, inline=True)
    embed.add_field(name="💬 Yorum", value=yorum, inline=False)
    embed.set_footer(text="Rastgele eşleştirme sistemi")
    await ctx.send(embed=embed)


# ====================== HİKAYE KOMUTU ======================
hikaye_bekleyen = {}  # {kanal_id: True/False}

@bot.command(name="hikaye")
async def hikaye(ctx):
    hikaye_bekleyen[ctx.channel.id] = ctx.author.id
    embed = discord.Embed(
        title="📖 HİKAYE OLUŞTURUCU",
        description=(
            "Harika! Sana özel bir hikaye oluşturacağım.\n\n"
            "✍️ Lütfen bir **cümle veya söz** yaz — o cümle etrafında sürükleyici bir hikaye kuracağım!\n\n"
            "*Örnek: 'Sahaya çıkan son oyuncuydu' veya 'Penaltı atışı öncesi elleri titriyordu'*"
        ),
        color=0x9B59B6
    )
    embed.set_footer(text="60 saniye içinde cümleni yaz!")
    await ctx.send(embed=embed)

    def kontrol(m):
        return m.channel.id == ctx.channel.id and m.author.id == ctx.author.id and not m.author.bot

    try:
        mesaj = await bot.wait_for("message", timeout=60.0, check=kontrol)
        cumle = mesaj.content.strip()
        del hikaye_bekleyen[ctx.channel.id]

        yukleniyor = await ctx.send("✍️ Hikayeniz yazılıyor, lütfen bekleyin...")

        # Hikayeyi bot kendi üretir (sabit şablon + dinamik içerik)
        hikayeler = [
            f"""
🌙 **Karanlık Saha**

Sahalar boştu. Seyirciler çoktan evlerine dönmüştü. Yalnızca fenerler yanıyordu.

*"{cumle}"*

O gece kimse onu görmüyordu. Ama o, kendini izliyordu. İçindeki ses her atışta büyüdü, her koşuda güçlendi.

Sabah olduğunda saha hâlâ boştu. Ama o artık aynı kişi değildi. Bir şey değişmişti — belki dünya, belki yalnızca o.

Ve o değişim, her şeyin başlangıcıydı.
""",
            f"""
⚽ **Son Dakika**

Maçın 90. dakikasıydı. Skor 0-0. Seyirciler nefeslerini tutuyordu.

*"{cumle}"*

Kimse bilmiyordu bu anın ne anlama geldiğini. Ama o biliyordu. Yıllarca bu an için çalışmıştı.

Top ağlara girdiğinde stadyum çatladı. Gözlerinden yaşlar aktı — sevinçten mi, yorgunluktan mı, bilinmez.

O gece herkes onun adını haykırdı. Ve o ad, artık tarihe geçmişti.
""",
            f"""
🏆 **Efsanenin Doğuşu**

Küçük bir kasabada, küçük bir çocuk vardı. Herkes ona "başaramazsın" diyordu.

*"{cumle}"*

Yıllar geçti. Kasaba büyümedi, ama çocuk büyüdü. Büyüdükçe güçlendi, güçlendikçe inandı.

Bir gün o küçük kasabadan büyük bir şehre adım attı. Sahada ilk topu tuttuğunda, geçmişindeki tüm sözler kafasında yankılandı.

Ama bu sefer gülümsedi. Çünkü artık o sözlerin önemi yoktu. Sahada yalnızca o vardı. Ve o, gerçekten hazırdı.
""",
            f"""
🌅 **Yeni Başlangıç**

Transfer dönemi kapanmıştı. Bavullar hazırlanmıştı. Yeni bir şehir, yeni bir takım.

*"{cumle}"*

İlk antrenman soğuktu. Takım arkadaşları onu tanımıyordu. Koç ona şüpheyle bakıyordu.

Ama o sabah antrenmanı bitirdiğinde bir şey fark edildi — bu oyuncu farklıydı.

Sezon sona erdiğinde en çok gol atan oyuncu oydu. Ve o sözler... O sözler hâlâ içinde yankılanıyordu. Onu oraya taşıyan da buydu zaten.
""",
            f"""
🩸 **Dönüşüm**

Yaralanma ağırdı. Doktorlar 6 ay sahalara dönemeyeceğini söyledi.

*"{cumle}"*

6 ay boyunca her gün fizik tedaviye gitti. Ağladığı geceler oldu. Vazgeçmek istediği anlar oldu.

Ama o cümle aklından hiç çıkmadı. Her güne o cümleyle uyandı.

6. ayın sonunda sahaya çıktığında stadyum ayakta alkışladı. Çünkü onun hikayesi, yeniden doğuşun hikayesiydi.
"""
        ]

        secilen_hikaye = random.choice(hikayeler)

        embed = discord.Embed(
            title="📖 Hikayen Hazır!",
            description=secilen_hikaye.strip(),
            color=0x9B59B6,
            timestamp=datetime.datetime.now()
        )
        embed.set_footer(text=f"Cümle: \"{cumle[:50]}{'...' if len(cumle)>50 else ''}\" | {ctx.author.display_name} için yazıldı")
        await yukleniyor.delete()
        await ctx.send(embed=embed)

    except asyncio.TimeoutError:
        if ctx.channel.id in hikaye_bekleyen:
            del hikaye_bekleyen[ctx.channel.id]
        await ctx.send("⏰ Süre doldu! `.hikaye` komutunu tekrar kullanabilirsin.", delete_after=10)


# ====================== VAMPİR KÖYLÜ SİSTEMİ (DOKTOR EKLENDİ) ======================

def vampir_katilan_listesi_yap(guild, oyuncular):
    liste = []
    for oid in oyuncular:
        uye = guild.get_member(oid)
        if uye:
            liste.append(f"🧛 {uye.display_name}")
    return "\n".join(liste) if liste else "Henüz kimse katılmadı."


class VampirKatilimView(ui.View):
    def __init__(self, kanal_id, guild):
        super().__init__(timeout=120)
        self.kanal_id = kanal_id
        self.guild = guild

    @discord.ui.button(label="Oyuna Katıl", style=discord.ButtonStyle.danger, emoji="🧛")
    async def katil_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.kanal_id not in aktif_vampir_oyunu:
            return await interaction.response.send_message(
                "❌ Oyun zaman aşımına uğradı veya iptal edildi!", ephemeral=True
            )
        oyuncular = aktif_vampir_oyunu[self.kanal_id]["oyuncular"]
        if interaction.user.id in oyuncular:
            return await interaction.response.send_message("❌ Zaten oyuna katıldın!", ephemeral=True)
        if len(oyuncular) >= 20:
            return await interaction.response.send_message("❌ Oyun dolu! (Max 20 kişi)", ephemeral=True)

        oyuncular.append(interaction.user.id)
        await interaction.response.send_message(
            "✅ Oyuna başarıyla katıldın! Rolün DM olarak gelecek.", ephemeral=True
        )

        guncel_sayi = len(oyuncular)
        katilan_metni = vampir_katilan_listesi_yap(interaction.guild, oyuncular)
        embed = discord.Embed(
            title="🧛 VAMPİR KÖYLÜ — KATILIM AŞAMASI",
            description=(
                "Köy karanlığa gömüldü... Aranızda gizli **Vampirler** var!\n"
                "Hayatta kalmak için aşağıdaki butona basıp katıl!"
            ),
            color=0x8E44AD,
            timestamp=datetime.datetime.now()
        )
        embed.add_field(name="👥 Katılımcı Sayısı", value=f"**{guncel_sayi} / 20**", inline=True)
        embed.add_field(name="⏳ Kalan Süre", value="**2 Dakika**", inline=True)
        embed.add_field(name="📋 Katılanlar", value=katilan_metni, inline=False)
        embed.set_footer(text="Minimum 4 kişi | Oyun 2 dk veya 5 kişide otomatik başlar")
        await interaction.message.edit(embed=embed, view=self)

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True


class VampirGeceSecimView(ui.View):
    def __init__(self, kanal_id, hedef_listesi, vampir_id):
        super().__init__(timeout=25)
        self.kanal_id = kanal_id
        self.vampir_id = vampir_id
        self.secim_yapildi = False
        for hedef_id, hedef_isim in hedef_listesi:
            self.add_item(VampirHedefButon(kanal_id, hedef_id, hedef_isim, vampir_id, self))


class VampirHedefButon(ui.Button):
    def __init__(self, kanal_id, hedef_id, hedef_isim, vampir_id, parent_view):
        super().__init__(label=hedef_isim, style=discord.ButtonStyle.danger, emoji="🩸")
        self.kanal_id = kanal_id
        self.hedef_id = hedef_id
        self.vampir_id = vampir_id
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.vampir_id:
            return await interaction.response.send_message("❌ Bu buton sana ait değil!", ephemeral=True)
        if self.parent_view.secim_yapildi:
            return await interaction.response.send_message("❌ Zaten seçim yaptın!", ephemeral=True)

        self.parent_view.secim_yapildi = True
        if self.kanal_id in aktif_vampir_oyunu:
            if "gece_secimler" not in aktif_vampir_oyunu[self.kanal_id]:
                aktif_vampir_oyunu[self.kanal_id]["gece_secimler"] = {}
            aktif_vampir_oyunu[self.kanal_id]["gece_secimler"][self.vampir_id] = self.hedef_id

        for item in self.parent_view.children:
            item.disabled = True

        onay_embed = discord.Embed(
            title="🩸 Hedef Seçildi!",
            description=f"**{self.label}** adlı kişiyi hedef aldın!\nTakım arkadaşının da seçim yapmasını bekle...",
            color=0x8E44AD
        )
        await interaction.response.edit_message(embed=onay_embed, view=self.parent_view)
        self.parent_view.stop()


# --- DOKTOR dropdown view ---
class DoktorKoruyuView(ui.View):
    def __init__(self, kanal_id, hedef_listesi, doktor_id):
        super().__init__(timeout=25)
        self.kanal_id = kanal_id
        self.doktor_id = doktor_id
        self.secim_yapildi = False
        for hedef_id, hedef_isim in hedef_listesi:
            self.add_item(DoktorKoruyuButon(kanal_id, hedef_id, hedef_isim, doktor_id, self))


class DoktorKoruyuButon(ui.Button):
    def __init__(self, kanal_id, hedef_id, hedef_isim, doktor_id, parent_view):
        super().__init__(label=hedef_isim, style=discord.ButtonStyle.success, emoji="💉")
        self.kanal_id = kanal_id
        self.hedef_id = hedef_id
        self.doktor_id = doktor_id
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.doktor_id:
            return await interaction.response.send_message("❌ Bu buton sana ait değil!", ephemeral=True)
        if self.parent_view.secim_yapildi:
            return await interaction.response.send_message("❌ Zaten seçim yaptın!", ephemeral=True)

        self.parent_view.secim_yapildi = True
        if self.kanal_id in aktif_vampir_oyunu:
            aktif_vampir_oyunu[self.kanal_id]["doktor_koruma"] = self.hedef_id

        for item in self.parent_view.children:
            item.disabled = True

        onay_embed = discord.Embed(
            title="💉 Koruma Yapıldı!",
            description=f"**{self.label}** adlı kişiyi bu gece korudun!",
            color=0x2ECC71
        )
        await interaction.response.edit_message(embed=onay_embed, view=self.parent_view)
        self.parent_view.stop()


class VampirOylamaView(ui.View):
    def __init__(self, kanal_id, hayatta_oyuncular, guild):
        super().__init__(timeout=25)
        self.kanal_id = kanal_id
        self.guild = guild
        self.oylar = {}
        self.oy_verenler = set()
        for oid in hayatta_oyuncular:
            uye = guild.get_member(oid)
            if uye:
                self.add_item(VampirOyButon(kanal_id, oid, uye.display_name, self))

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True


class VampirOyButon(ui.Button):
    def __init__(self, kanal_id, hedef_id, hedef_isim, parent_view):
        super().__init__(label=hedef_isim[:80], style=discord.ButtonStyle.secondary, emoji="☠️")
        self.kanal_id = kanal_id
        self.hedef_id = hedef_id
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        if self.kanal_id not in aktif_vampir_oyunu:
            return await interaction.response.send_message("❌ Oyun bitti!", ephemeral=True)
        veri = aktif_vampir_oyunu[self.kanal_id]
        if interaction.user.id not in veri["hayatta"]:
            return await interaction.response.send_message("❌ Oyun dışısın, oy kullanamazsın!", ephemeral=True)
        if interaction.user.id == self.hedef_id:
            return await interaction.response.send_message("❌ Kendine oy veremezsin!", ephemeral=True)
        if interaction.user.id in self.parent_view.oy_verenler:
            return await interaction.response.send_message("❌ Zaten oy kullandın!", ephemeral=True)

        self.parent_view.oy_verenler.add(interaction.user.id)
        self.parent_view.oylar[self.hedef_id] = self.parent_view.oylar.get(self.hedef_id, 0) + 1
        hedef_uye = interaction.guild.get_member(self.hedef_id)
        await interaction.response.send_message(
            f"✅ **{hedef_uye.display_name}** için oy kullandın!", ephemeral=True
        )


async def baslat_vampir_oyunu(ctx):
    kanal_id = ctx.channel.id
    aktif_vampir_oyunu[kanal_id] = {
        "oyuncular": [ctx.author.id],
        "roller": {},
        "hayatta": [],
        "vampirler": [],
        "doktor": None,
        "doktor_koruma": None,
        "basladi": False,
        "gece_secimler": {}
    }

    katilan_metni = f"🧛 {ctx.author.display_name}"
    embed = discord.Embed(
        title="🧛 VAMPİR KÖYLÜ — KATILIM AŞAMASI",
        description=(
            "Köy karanlığa gömüldü... Aranızda gizli **Vampirler** var!\n"
            "Hayatta kalmak için aşağıdaki butona basıp katıl!"
        ),
        color=0x8E44AD,
        timestamp=datetime.datetime.now()
    )
    embed.add_field(name="👥 Katılımcı Sayısı", value="**1 / 20**", inline=True)
    embed.add_field(name="⏳ Kalan Süre", value="**2 Dakika**", inline=True)
    embed.add_field(name="📋 Katılanlar", value=katilan_metni, inline=False)
    embed.set_footer(text="Minimum 4 kişi | Oyun 2 dk veya 5 kişide otomatik başlar")

    view = VampirKatilimView(kanal_id, ctx.guild)
    ana_mesaj = await ctx.send(embed=embed, view=view)

    for _ in range(24):
        await asyncio.sleep(5)
        if kanal_id not in aktif_vampir_oyunu:
            return
        if len(aktif_vampir_oyunu[kanal_id]["oyuncular"]) >= 5:
            break

    if kanal_id not in aktif_vampir_oyunu:
        return

    mevcut_oyuncular = aktif_vampir_oyunu[kanal_id]["oyuncular"]
    if len(mevcut_oyuncular) < 4:
        del aktif_vampir_oyunu[kanal_id]
        iptal_embed = discord.Embed(
            title="❌ Oyun İptal Edildi",
            description="Yeterli katılımcı yok! **(Minimum 4 kişi gerekli)**",
            color=0xFF0000
        )
        await ana_mesaj.edit(embed=iptal_embed, view=None)
        return

    # --- ROLLER DAĞIT ---
    aktif_vampir_oyunu[kanal_id]["hayatta"] = mevcut_oyuncular.copy()
    random.shuffle(mevcut_oyuncular)

    vampir_sayisi = 1 if len(mevcut_oyuncular) <= 6 else 2
    secilen_vampirler = mevcut_oyuncular[:vampir_sayisi]
    aktif_vampir_oyunu[kanal_id]["vampirler"] = secilen_vampirler

    # Doktor: Vampir olmayan oyunculardan biri (yeterince kişi varsa)
    doktor = None
    kalan_koyluler = [p for p in mevcut_oyuncular if p not in secilen_vampirler]
    if len(kalan_koyluler) >= 2:
        doktor = random.choice(kalan_koyluler)
        aktif_vampir_oyunu[kanal_id]["doktor"] = doktor

    for oid in mevcut_oyuncular:
        if oid in secilen_vampirler:
            aktif_vampir_oyunu[kanal_id]["roller"][oid] = "Vampir"
        elif oid == doktor:
            aktif_vampir_oyunu[kanal_id]["roller"][oid] = "Doktor"
        else:
            aktif_vampir_oyunu[kanal_id]["roller"][oid] = "Köylü"

    # --- DM BİLDİRİMLERİ ---
    for oid in mevcut_oyuncular:
        uye = ctx.guild.get_member(oid)
        if not uye:
            continue
        try:
            if oid in secilen_vampirler:
                diger_vampirler = [ctx.guild.get_member(v) for v in secilen_vampirler if v != oid]
                diger_isimler = ", ".join([d.display_name for d in diger_vampirler if d]) or "Yok"
                dm_embed = discord.Embed(title="🩸 VAMPİR KÖYLÜ — ROLÜN: VAMPİR", color=0xE74C3C)
                dm_embed.description = (
                    "**Rolün: 🧛 VAMPİR**\n\n"
                    "Görevin: Geceleyin köylülerden birini öldürmek ve gündüz yakalanmamak!\n\n"
                    f"🧛 **Vampir Takım Arkadaşların:** `{diger_isimler}`\n\n"
                    "⚠️ Birlikte hareket edin! Gece hedef seçiminde butonlara basın."
                )
                dm_embed.set_footer(text="Kimseye rolünü söyleme!")
                await uye.send(embed=dm_embed)
            elif oid == doktor:
                dm_embed = discord.Embed(title="💉 VAMPİR KÖYLÜ — ROLÜN: DOKTOR", color=0x2ECC71)
                dm_embed.description = (
                    "**Rolün: 💉 DOKTOR**\n\n"
                    "Görevin: Her gece bir kişiyi vampirlerden koru!\n\n"
                    "🛡️ Eğer vampirler koruduğun kişiyi seçerse, o kişi ölmez!\n"
                    "⚠️ Her gece DM'den bir kişi seçerek koruma sağlarsın."
                )
                dm_embed.set_footer(text="Kimseye rolünü söyleme!")
                await uye.send(embed=dm_embed)
            else:
                dm_embed = discord.Embed(title="🛡️ VAMPİR KÖYLÜ — ROLÜN: KÖYLÜ", color=0x3498DB)
                dm_embed.description = (
                    "**Rolün: 🧑‍🌾 KÖYLÜ**\n\n"
                    "Görevin: Gündüz yapılan oylamalarda vampirleri bulmak ve köyü kurtarmak!\n\n"
                    "⚠️ Dikkatli ol, kimseye güvenme..."
                )
                dm_embed.set_footer(text="Vampiri bul, köyü kurtar!")
                await uye.send(embed=dm_embed)
        except discord.Forbidden:
            pass

    aktif_vampir_oyunu[kanal_id]["basladi"] = True

    baslangic_embed = discord.Embed(
        title="🌙 GECE ÇÖKTÜ — OYUN BAŞLADI!",
        description=(
            f"**{len(mevcut_oyuncular)}** kişiyle oyun başladı!\n"
            f"Herkese rolleri DM olarak gönderildi.\n\n"
            f"🧛 **{vampir_sayisi} Vampir** gizlice görev yapıyor...\n"
            f"💉 **1 Doktor** gece bir kişiyi koruyacak..."
        ),
        color=0x2C3E50
    )
    baslangic_embed.add_field(
        name="📋 Katılımcılar",
        value=vampir_katilan_listesi_yap(ctx.guild, mevcut_oyuncular),
        inline=False
    )
    baslangic_embed.set_footer(text="Vampirler ve Doktor hedeflerini seçiyor... (25 saniye)")
    await ana_mesaj.edit(embed=baslangic_embed, view=None)

    await asyncio.sleep(2)
    await vampir_gece_fazi(ctx, kanal_id, ana_mesaj)


async def vampir_gece_fazi(ctx, kanal_id, ana_mesaj):
    if kanal_id not in aktif_vampir_oyunu:
        return

    veri = aktif_vampir_oyunu[kanal_id]
    if not veri["basladi"]:
        return

    hayatta_koyluler = [oid for oid in veri["hayatta"] if oid not in veri["vampirler"]]
    if not hayatta_koyluler:
        await vampir_oyunu_bitti(ctx, kanal_id, ana_mesaj, "vampir")
        return

    # Gece bildirimi
    gece_embed = discord.Embed(
        title="🌙 GECE FAZI",
        description="Vampirler hedeflerini seçiyor... Doktor ise birini koruyor!\n**DM kutunuzu kontrol edin!** (25 saniye)",
        color=0x2C3E50
    )
    hayatta_metni = "\n".join([
        f"• {ctx.guild.get_member(oid).display_name}"
        for oid in veri["hayatta"]
        if ctx.guild.get_member(oid)
    ])
    gece_embed.add_field(name="🫀 Hayatta Olanlar", value=hayatta_metni, inline=False)
    await ctx.channel.send(embed=gece_embed)

    # Gece seçimleri sıfırla
    veri["gece_secimler"] = {}
    veri["doktor_koruma"] = None

    # Vampirlere DM gönder
    for vid in veri["vampirler"]:
        if vid not in veri["hayatta"]:
            continue
        vampir_uye = ctx.guild.get_member(vid)
        if not vampir_uye:
            continue

        hedef_listesi = [
            (oid, ctx.guild.get_member(oid).display_name)
            for oid in hayatta_koyluler
            if ctx.guild.get_member(oid)
        ]
        dm_embed = discord.Embed(
            title="🌙 GECE FAZI — HEDEF SEÇ!",
            description="Öldürmek istediğin köylüyü seç!\nTakım arkadaşınla aynı kişiyi seçmeye çalışın!",
            color=0x8E44AD
        )
        dm_embed.set_footer(text="25 saniyeniz var!")
        v_view = VampirGeceSecimView(kanal_id, hedef_listesi, vid)
        try:
            await vampir_uye.send(embed=dm_embed, view=v_view)
        except discord.Forbidden:
            pass

    # Doktora DM gönder
    doktor_id = veri.get("doktor")
    if doktor_id and doktor_id in veri["hayatta"]:
        doktor_uye = ctx.guild.get_member(doktor_id)
        if doktor_uye:
            # Doktor tüm hayatta olanları koruyabilir (kendisi dahil)
            koruma_listesi = [
                (oid, ctx.guild.get_member(oid).display_name)
                for oid in veri["hayatta"]
                if ctx.guild.get_member(oid)
            ]
            dm_embed = discord.Embed(
                title="💉 GECE FAZI — KİMİ KORUYACAKSIN?",
                description="Bu gece kimi vampirlerden koruyacaksın? Aşağıdan seç!",
                color=0x2ECC71
            )
            dm_embed.set_footer(text="25 saniyeniz var!")
            d_view = DoktorKoruyuView(kanal_id, koruma_listesi, doktor_id)
            try:
                await doktor_uye.send(embed=dm_embed, view=d_view)
            except discord.Forbidden:
                pass

    # 25 saniye bekle
    await asyncio.sleep(25)

    # Öldürme mantığı (Doktor koruması kontrol)
    oy_sayilari = {}
    for _, hedef in veri.get("gece_secimler", {}).items():
        oy_sayilari[hedef] = oy_sayilari.get(hedef, 0) + 1

    korunan = veri.get("doktor_koruma")

    if oy_sayilari:
        en_cok_oy = max(oy_sayilari.values())
        olasi_hedefler = [k for k, v in oy_sayilari.items() if v == en_cok_oy]
        kurban_id = random.choice(olasi_hedefler)

        # Doktor korumasını kontrol et
        if kurban_id == korunan:
            korunan_uye = ctx.guild.get_member(kurban_id)
            koruma_embed = discord.Embed(
                title="💉 DOKTOR KURTARDI!",
                description=(
                    f"Vampirler bu gece **{korunan_uye.mention}** adlı kişiyi öldürmeye çalıştı!\n"
                    f"Ama Doktor zamanında yetişti ve onu kurtardı! 🛡️"
                ),
                color=0x2ECC71
            )
            await ctx.channel.send(embed=koruma_embed)
        else:
            if kurban_id in veri["hayatta"]:
                veri["hayatta"].remove(kurban_id)
            kurban_uye = ctx.guild.get_member(kurban_id)
            if kurban_uye:
                gunduz_embed = discord.Embed(
                    title="☀️ GÜNDÜZ DOĞDU!",
                    description=(
                        f"Gece boyunca korkunç çığlıklar duyuldu...\n\n"
                        f"🩸 **{kurban_uye.mention}** vampirler tarafından acımasızca öldürüldü!"
                    ),
                    color=0xE67E22
                )
                gunduz_embed.set_footer(text="Vampirleri bulmak için oylama başlıyor! (20 saniye)")
                await ctx.channel.send(embed=gunduz_embed)
                try:
                    olum_embed = discord.Embed(
                        title="💀 ÖLDÜRÜLDÜN!",
                        description="Vampirler seni gece vahşice yok etti! Artık oyun dışısın.",
                        color=0x000000
                    )
                    await kurban_uye.send(embed=olum_embed)
                except:
                    pass
    else:
        kimse_embed = discord.Embed(
            title="🌅 Sessiz Bir Gece...",
            description="Vampirler bu gece kimseyi öldürmedi!",
            color=0xF1C40F
        )
        await ctx.channel.send(embed=kimse_embed)

    await asyncio.sleep(2)

    kalan_vampir = len([v for v in veri["vampirler"] if v in veri["hayatta"]])
    kalan_koylu = len([o for o in veri["hayatta"] if o not in veri["vampirler"]])
    if kalan_vampir == 0:
        await vampir_oyunu_bitti(ctx, kanal_id, ana_mesaj, "koylu")
        return
    if kalan_vampir >= kalan_koylu:
        await vampir_oyunu_bitti(ctx, kanal_id, ana_mesaj, "vampir")
        return

    await vampir_gunduz_oylamasi(ctx, kanal_id, ana_mesaj)


async def vampir_gunduz_oylamasi(ctx, kanal_id, ana_mesaj):
    if kanal_id not in aktif_vampir_oyunu:
        return

    veri = aktif_vampir_oyunu[kanal_id]
    hayatta_oyuncular = veri["hayatta"]

    if len(hayatta_oyuncular) == 0:
        return

    oylama_embed = discord.Embed(
        title="⚖️ GÜNDÜZ OYLAMASI!",
        description=(
            "Vampir olduğunu düşündüğün kişiye aşağıdaki butondan oy ver!\n"
            "En çok oyu alan kişi idam edilecek!\n\n"
            "⏰ **20 saniye** süreniz var!"
        ),
        color=0x3498DB
    )
    hayatta_metni = "\n".join([
        f"• {ctx.guild.get_member(oid).display_name}"
        for oid in hayatta_oyuncular
        if ctx.guild.get_member(oid)
    ])
    oylama_embed.add_field(name="🫀 Hayatta Olanlar", value=hayatta_metni, inline=False)
    oylama_embed.set_footer(text="Herkes oy kullanabilir! Sadece 1 oy hakkın var.")

    oylama_view = VampirOylamaView(kanal_id, hayatta_oyuncular, ctx.guild)
    oylama_mesaj = await ctx.channel.send(embed=oylama_embed, view=oylama_view)

    await asyncio.sleep(20)

    for item in oylama_view.children:
        item.disabled = True
    try:
        await oylama_mesaj.edit(view=oylama_view)
    except:
        pass

    oy_sayilari = oylama_view.oylar

    if not oy_sayilari:
        hic_oy_embed = discord.Embed(
            title="🤷 Kimse Oy Vermedi!",
            description="Oylama atlandı, gece tekrar başlıyor...",
            color=0xF1C40F
        )
        await ctx.channel.send(embed=hic_oy_embed)
        await asyncio.sleep(2)
        await vampir_gece_fazi(ctx, kanal_id, ana_mesaj)
        return

    en_cok_oy = max(oy_sayilari.values())
    birinci_adaylar = [k for k, v in oy_sayilari.items() if v == en_cok_oy]
    secilen_id = random.choice(birinci_adaylar)

    secilen_uye = ctx.guild.get_member(secilen_id)
    gercek_rol = veri["roller"].get(secilen_id, "Bilinmiyor")

    if gercek_rol == "Vampir":
        veri["hayatta"].remove(secilen_id)
        sonuc_embed = discord.Embed(
            title="🛡️ VAMPİR YAKALANDI!",
            description=(
                f"**{secilen_uye.mention}** {en_cok_oy} oy aldı!\n\n"
                f"🩸 Kartı açıldı: **VAMPİR** 🧛\n"
                f"Köylüler zafere bir adım daha yaklaştı!"
            ),
            color=0x2ECC71
        )
    elif gercek_rol == "Doktor":
        veri["hayatta"].remove(secilen_id)
        sonuc_embed = discord.Embed(
            title="😱 DOKTOR İDAM EDİLDİ!",
            description=(
                f"**{secilen_uye.mention}** {en_cok_oy} oy aldı!\n\n"
                f"💉 Kartı açıldı: **DOKTOR** 💉\n"
                f"Koruyucu yokluğunda vampirler daha da güçlendi..."
            ),
            color=0xE74C3C
        )
        # Doktoru listeden çıkar, bir dahaki gece aktif olmayacak
        veri["doktor"] = None
    else:
        veri["hayatta"].remove(secilen_id)
        sonuc_embed = discord.Embed(
            title="😭 MASUM KÖYLÜ İDAM EDİLDİ!",
            description=(
                f"**{secilen_uye.mention}** {en_cok_oy} oy aldı!\n\n"
                f"🛡️ Kartı açıldı: **KÖYLÜ** 🧑‍🌾\n"
                f"Vampirler kıkırdıyor..."
            ),
            color=0xE74C3C
        )

    await ctx.channel.send(embed=sonuc_embed)

    kalan_vampir = len([v for v in veri["vampirler"] if v in veri["hayatta"]])
    kalan_koylu = len([o for o in veri["hayatta"] if o not in veri["vampirler"]])

    if kalan_vampir == 0:
        await vampir_oyunu_bitti(ctx, kanal_id, ana_mesaj, "koylu")
    elif kalan_vampir >= kalan_koylu:
        await vampir_oyunu_bitti(ctx, kanal_id, ana_mesaj, "vampir")
    else:
        await asyncio.sleep(3)
        await vampir_gece_fazi(ctx, kanal_id, ana_mesaj)


async def vampir_oyunu_bitti(ctx, kanal_id, ana_mesaj, kazanan):
    if kanal_id in aktif_vampir_oyunu:
        veri = aktif_vampir_oyunu[kanal_id]
        rol_listesi = []
        for oid, rol in veri["roller"].items():
            uye = ctx.guild.get_member(oid)
            if uye:
                if rol == "Vampir":
                    emoji = "🧛"
                elif rol == "Doktor":
                    emoji = "💉"
                else:
                    emoji = "🧑‍🌾"
                rol_listesi.append(f"{emoji} **{uye.display_name}** — {rol}")
        del aktif_vampir_oyunu[kanal_id]
    else:
        rol_listesi = []

    if kazanan == "koylu":
        bitis_embed = discord.Embed(
            title="🎉 KÖYLÜLER KAZANDI!",
            description="Tüm vampirler temizlendi! Köyde huzur yeniden sağlandı. ☀️",
            color=0x2ECC71
        )
        bitis_embed.set_footer(text="Tebrikler masum köylüler!")
    else:
        bitis_embed = discord.Embed(
            title="🩸 VAMPİRLER KAZANDI!",
            description="Vampirler köyün kontrolünü tamamen ele geçirdi! Karanlık çöktü... 🌙",
            color=0x8E44AD
        )
        bitis_embed.set_footer(text="Köylüler için çok geçti...")

    if rol_listesi:
        bitis_embed.add_field(name="📋 Tüm Roller", value="\n".join(rol_listesi), inline=False)

    await ctx.channel.send(embed=bitis_embed)


@bot.command(name="vk")
async def vk(ctx):
    yetkili = ctx.author.id == ctx.guild.owner_id or ctx.author.id in VK_YETKILI_IDS
    if not yetkili:
        return await ctx.send(embed=hata_embed("Bu komutu sadece **sunucu sahibi** veya yetkili kişiler kullanabilir!"))
    if ctx.channel.id in aktif_vampir_oyunu:
        return await ctx.send("❌ Bu kanalda zaten aktif bir Vampir Köylü oyunu devam ediyor!")
    await baslat_vampir_oyunu(ctx)


# ====================== GÜNLÜK MESAJ KOMUTU ======================
@bot.command(name="günlükmesaj")
async def gunluk_mesaj(ctx):
    bugun = datetime.date.today().isoformat()
    bugunun_verileri = gunluk_mesaj_sayaci.get(bugun, {})

    if not bugunun_verileri:
        return await ctx.send(embed=discord.Embed(
            title="📊 Günlük Mesaj İstatistikleri",
            description="Bugün henüz hiç mesaj istatistiği kaydedilmedi!",
            color=0x3498DB
        ))

    sirali = sorted(bugunun_verileri.items(), key=lambda x: x[1], reverse=True)
    liste_satirlari = []
    toplam = 0
    sira = 1
    for uid, sayi in sirali:
        uye = ctx.guild.get_member(uid)
        if not uye or uye.bot:
            continue
        madalya = ""
        if sira == 1: madalya = "🥇"
        elif sira == 2: madalya = "🥈"
        elif sira == 3: madalya = "🥉"
        else: madalya = f"**#{sira}**"
        liste_satirlari.append(f"{madalya} {uye.display_name} — **{sayi}** mesaj")
        toplam += sayi
        sira += 1

    if not liste_satirlari:
        return await ctx.send("❌ Bugün mesaj atan üye bulunamadı.")

    embed = discord.Embed(
        title="📊 Günlük Mesaj İstatistikleri",
        description="\n".join(liste_satirlari[:25]),
        color=0x5865F2,
        timestamp=datetime.datetime.now()
    )
    embed.set_footer(text=f"📅 Tarih: {bugun} | 💬 Toplam: {toplam} mesaj")
    await ctx.send(embed=embed)


# ====================== EKSTRİ KOMUTLAR ======================
@bot.command()
async def ytstat(ctx):
    k_yetkili_rol = discord.utils.get(ctx.guild.roles, name="Kayıt Yetkilisi")
    d_yetkili_rol = discord.utils.get(ctx.guild.roles, name="Değer Yetkilisi")
    r_yetkili_rol = discord.utils.get(ctx.guild.roles, name="Rol Yetkili")
    yetkili_idleri = set()
    if k_yetkili_rol: yetkili_idleri.update([m.id for m in k_yetkili_rol.members])
    if d_yetkili_rol: yetkili_idleri.update([m.id for m in d_yetkili_rol.members])
    if r_yetkili_rol: yetkili_idleri.update([m.id for m in r_yetkili_rol.members])
    if not yetkili_idleri:
        return await ctx.send("❌ Sunucuda yetkili bulunamadı.")
    liste = []
    for uid in yetkili_idleri:
        uye = ctx.guild.get_member(uid)
        if not uye or uye.bot:
            continue
        k = kayit_sayaci.get(uid, 0)
        d = deger_sayaci.get(uid, 0)
        liste.append(f"**{uye.display_name}** ➔ 📝 Kayıt: {k} | 💰 Değer: {d}")
    aciklama = "\n".join(liste)
    embed = discord.Embed(title="📊 Yetkili İstatistikleri", description=aciklama, color=0x5865F2)
    embed.set_footer(text=f"Toplam {len(liste)} yetkili listelendi")
    await ctx.send(embed=embed)


@bot.command()
async def m(ctx):
    sayi = mesaj_sayaci.get(ctx.author.id, 0)
    await ctx.send(f"📝 {ctx.author.mention} toplam **{sayi}** mesaj yazdı!")


@bot.command()
async def hesapla(ctx, *, soru: str):
    izin_verilen = set("0123456789+-*/.() ")
    if not all(c in izin_verilen for c in soru):
        return await ctx.send("❌ Sadece sayılar ve matematiksel işaretler kullanabilirsin!")
    try:
        sonuc = eval(soru)
        await ctx.send(f"🧮 **{soru}** = {sonuc}")
    except:
        await ctx.send("❌ Geçersiz bir matematiksel ifade!")


@bot.command()
async def owner(ctx):
    sahibi = ctx.guild.owner
    await ctx.send(f"👑 Sunucu Sahibi: **{sahibi.display_name}** ({sahibi.mention})")


@bot.command()
async def snipeall(ctx):
    mesajlar = snipe_all_listesi.get(ctx.channel.id, [])
    if not mesajlar:
        return await ctx.send("❌ Son 5 dakikada silinen mesaj yok.")
    aciklama = ""
    for msg in reversed(mesajlar[-20:]):
        sure = (datetime.datetime.now() - msg["zaman"]).seconds
        aciklama += f"**{msg['yazar'].name}:** {msg['icerik'][:80]} ({sure}sn önce)\n"
    await ctx.send(f"🗑️ **Son 5 Dakikada Silinen Mesajlar:**\n{aciklama}")


@bot.command()
async def dmall(ctx, *, mesaj: str):
    if ctx.author.id != ctx.guild.owner_id:
        return await ctx.send("❌ Bu komutu sadece sunucu sahibi kullanabilir!")
    islem = await ctx.send("⏳ DM'ler gönderiliyor, lütfen bekleyin...")
    basari = 0
    for uye in ctx.guild.members:
        if uye.bot or uye.id == ctx.author.id:
            continue
        try:
            await uye.send(f"📢 **{ctx.guild.name}** sunucusundan mesajınız var:\n\n{mesaj}")
            basari += 1
            await asyncio.sleep(0.5)
        except:
            continue
    await islem.edit(content=f"✅ İşlem bitti! Toplam **{basari}** kişiye DM başarıyla gönderildi.")


@bot.command()
async def dm(ctx, uye: discord.Member, *, mesaj: str):
    try:
        await uye.send(f"📬 **{ctx.author.display_name}** size bir mesaj gönderdi:\n\n{mesaj}")
        await ctx.send(f"✅ Mesajınız {uye.mention} kişisine gönderildi.")
    except:
        await ctx.send(f"❌ {uye.mention} kişisinin DM'i kapalı veya mesaj gönderilemedi!")


@bot.command()
async def pen(ctx):
    # Ardarda aynı sonucu verme
    son = son_cark_sonucu.get(f"pen_{ctx.author.id}", -1)
    secenekler = list(range(3))
    kullanilabilir = [i for i in secenekler if i != son]
    secim_index = random.choice(kullanilabilir)
    son_cark_sonucu[f"pen_{ctx.author.id}"] = secim_index

    sonuclar = ["GOL ⚽", "KALECİ ÇIKTI 🧤", "AUT ❌"]
    sonuc = sonuclar[secim_index]

    sozler = {
        "GOL ⚽": ["Muhteşem vuruş!", "Ağları salladı!", "Gol olmaz dediğin gol!", "Köşeye yerleştirdi!"],
        "KALECİ ÇIKTI 🧤": ["Rüya gibi kurtarış!", "Kaleci şov yaptı!", "Neyi düşünüyordun?", "Demir gibi eller!"],
        "AUT ❌": ["Çok az fark!", "Aut lazımdı bu maça!", "Direkten döndü, aut!", "Ah be, tam yanından geçti!"]
    }
    soz = random.choice(sozler[sonuc])
    renk = 0x2ECC71 if "GOL" in sonuc else (0xFFA500 if "KALECİ" in sonuc else 0xE74C3C)
    embed = discord.Embed(title=sonuc, description=f"*{soz}*", color=renk)
    embed.set_footer(text=f"Penaltı atan: {ctx.author.name}")
    await ctx.send(embed=embed)


@bot.command()
async def up(ctx, uye: discord.Member):
    if ctx.author.id not in [ctx.guild.owner_id, 1290738144609828877]:
        return await ctx.send("❌ Bu komutu kullanma yetkiniz yok!")
    rol_siniflama = [
        "Kayıt Yetkilisi", "Değer Yetkilisi", "Rehber", "Deneme Moderatör",
        "Moderatör", "Üst Moderatör", "Admin", "Üst Admin",
        "Sunucu Amiri", "Bot Commander", "League Commander"
    ]
    mevcut_roller = [r.name for r in uye.roles]
    bulunulan_index = -1
    for i, rol_adi in enumerate(rol_siniflama):
        if rol_adi in mevcut_roller:
            bulunulan_index = i
    if bulunulan_index == -1:
        hedef_rol = discord.utils.get(ctx.guild.roles, name=rol_siniflama[0])
        if not hedef_rol:
            return await ctx.send("❌ Kayıt Yetkilisi rolü sunucuda bulunamadı!")
        await uye.add_roles(hedef_rol)
        return await ctx.send(f"⬆️ {uye.mention} adına **{hedef_rol.name}** rolü verildi!")
    if bulunulan_index >= len(rol_siniflama) - 1:
        return await ctx.send("❌ Zaten en üst rolde (League Commander)!")
    eski_rol = discord.utils.get(ctx.guild.roles, name=rol_siniflama[bulunulan_index])
    yeni_rol = discord.utils.get(ctx.guild.roles, name=rol_siniflama[bulunulan_index + 1])
    if not yeni_rol:
        return await ctx.send("❌ Bir üst rol sunucuda bulunamadı!")
    await uye.remove_roles(eski_rol)
    await uye.add_roles(yeni_rol)
    await ctx.send(f"⬆️ {uye.mention} rolü güncellendi: {eski_rol.name} → {yeni_rol.name}")


@bot.command()
async def deup(ctx, uye: discord.Member):
    if ctx.author.id != ctx.guild.owner_id:
        return await ctx.send("❌ Bu komutu sadece sunucu sahibi kullanabilir!")
    rol_siniflama = [
        "Kayıt Yetkilisi", "Değer Yetkilisi", "Rehber", "Deneme Moderatör",
        "Moderatör", "Üst Moderatör", "Admin", "Üst Admin",
        "Sunucu Amiri", "Bot Commander", "League Commander"
    ]
    mevcut_roller = [r.name for r in uye.roles]
    bulunulan_index = -1
    for i, rol_adi in enumerate(rol_siniflama):
        if rol_adi in mevcut_roller:
            bulunulan_index = i
    if bulunulan_index <= 0:
        return await ctx.send("❌ Zaten en alt rolde veya listede değil!")
    eski_rol = discord.utils.get(ctx.guild.roles, name=rol_siniflama[bulunulan_index])
    yeni_rol = discord.utils.get(ctx.guild.roles, name=rol_siniflama[bulunulan_index - 1])
    if not eski_rol or not yeni_rol:
        return await ctx.send("❌ Roller bulunamadı!")
    await uye.remove_roles(eski_rol)
    await uye.add_roles(yeni_rol)
    await ctx.send(f"⬇️ {uye.mention} rolü güncellendi: {eski_rol.name} → {yeni_rol.name}")


# ====================== YARDIM SİSTEMİ ======================
class YardimDropDown(ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="🛡️ Moderasyon", description="Ban, Kick, Mute, Unmute, Nuke..."),
            discord.SelectOption(label="🎭 Rol Yönetimi", description="Rol Ver, Rol Al, Toplu Rol..."),
            discord.SelectOption(label="🎬 Roleplay", description="Kayıt, Değer, Antrenman komutları."),
            discord.SelectOption(label="⚽ Kariyer Sistemi", description="Kariyer, Gol, Asist komutları."),
            discord.SelectOption(label="📢 NOVA KAP", description="Transfer, Kiralama, Yenileme, FESH"),
            discord.SelectOption(label="🎉 Etkinlik", description="Etkinlik başlat, Çark, Bilgi, Eşleştir..."),
            discord.SelectOption(label="🌍 Genel & Eğlence", description="Ping, Avatar, Snipe, AFK, Hikaye..."),
            discord.SelectOption(label="⚡ Ekstra & Sahip", description="Up, Deup, Dmall, Hesapla, Pen...")
        ]
        super().__init__(placeholder="Kategori seçin...", options=options)

    async def callback(self, interaction: discord.Interaction):
        embed = discord.Embed(title=f"{self.values[0]} Komutları", color=0x2f3136)
        if self.values[0] == "🛡️ Moderasyon":
            embed.description = (
                "**.lock** - Kanalı kilitler.\n"
                "**.unlock** - Kanal kilidini açar.\n"
                "**.ban @üye [sebep]** - Üyeyi yasaklar.\n"
                "**.unban [ID]** - Yasağı kaldırır.\n"
                "**.kick @üye [sebep]** - Üyeyi atar.\n"
                "**.mute @üye [dakika]** - Üyeyi susturur.\n"
                "**.unmute @üye** - Susturmayı kaldırır.\n"
                "**.nuke** - Kanalı sıfırlar."
            )
        elif self.values[0] == "🎭 Rol Yönetimi":
            embed.description = (
                "**.rolver @üye [rol adı]** - Rol verir. (Büyük/küçük harf fark etmez)\n"
                "**.rolal @üye [rol adı]** - Rolü alır. (Büyük/küçük harf fark etmez)\n"
                "**.toplurolver @üye/hepsi [roller]** - Toplu rol verir.\n"
                "**.toplurolal @üye/hepsi [roller]** - Toplu rol alır."
            )
        elif self.values[0] == "🎬 Roleplay":
            embed.description = (
                "**.k @üye [İsim | Değer | Takım]** - Kayıt yapar.\n"
                "**.dver @üye [miktar] [sebep]** - Kişiye değer ekler.\n"
                "**.dsil @üye [miktar] [sebep]** - Kişiden değer siler.\n"
                "**.antrenman** - Antrenman yapar, 10/10 olunca +3M verir. (Kaldığı yerden devam eder!)"
            )
        elif self.values[0] == "⚽ Kariyer Sistemi":
            embed.description = (
                "**.kariyer [@üye]** - Kariyer istatistiklerini gösterir.\n"
                "**.golekle @üye [miktar]** - Gol ekler. **(League Commander)**\n"
                "**.asistekle @üye [miktar]** - Asist ekler. **(League Commander)**\n"
                "**.takimekle @üye [takım adı]** - Kariyer geçmişine takım ekler. **(League Commander)**"
            )
        elif self.values[0] == "📢 NOVA KAP":
            takim_listesi = "\n".join([f"• {t}" for t in TAKIM_ROLLERI.keys()])
            embed.description = (
                f".kap komutu ile panel açılır.\n"
                f"Transfer ve Kiralama 2 aşamalıdır.\n\n"
                f"📋 **Sadece şu takımların rolü verilebilir:**\n{takim_listesi}"
            )
        elif self.values[0] == "🎉 Etkinlik":
            embed.description = (
                "**.etkinlik** - Etkinlik panelini açar, oyun seçilir ve duyuru yapılır.\n"
                "**.cark [@üye]** - Şans çarkını çevirir! Günlük limit: **5 hak**.\n"
                "**.bilgi** - Futbol sorusu sorar! **200 farklı soru** arasından gelir.\n"
                "**.eslestir** - İki sunucu üyesini rastgele eşleştirir!\n"
                "**.vk** - **Vampir Köylü** oyununu başlatır. (Vampir + Köylü + **Doktor** rolleri)\n"
                "**.günlükmesaj** - Bugün en çok mesaj atanları listeler.\n\n"
                "**Mevcut Etkinlik Oyunları:**\n" +
                "\n".join([f"{v['emoji']} **{k.split(' ', 1)[1]}**" for k, v in OYUNLAR.items()])
            )
        elif self.values[0] == "🌍 Genel & Eğlence":
            embed.description = (
                "**.ping** - Bot gecikmesini gösterir.\n"
                "**.avatar @üye** - Profil fotoğrafını gösterir.\n"
                "**.snipe** - Silinen son mesajı gösterir.\n"
                "**.snipeall** - Son 5 dk silinen tüm mesajlar.\n"
                "**.afk [sebep]** - AFK moduna geçer.\n"
                "**.ship @üye** - Uyumu ölçer.\n"
                "**.roll [seçenek1, seçenek2]** - Şanslı seçim.\n"
                "**.ara [isim]** - Sunucuda isim arar.\n"
                "**.hikaye** - Yazdığın cümle üzerinden bot bir hikaye oluşturur!"
            )
        elif self.values[0] == "⚡ Ekstra & Sahip":
            embed.description = (
                "**.ytstat** - Tüm yetkililerin kayıt/değer sayıları.\n"
                "**.m** - Mesaj sayınız.\n"
                "**.günlükmesaj** - Günlük mesaj sıralaması.\n"
                "**.hesapla [işlem]** - Matematiksel işlem yapar.\n"
                "**.owner** - Sunucu sahibini gösterir.\n"
                "**.dmall [mesaj]** - Herkese DM atar (Sahip).\n"
                "**.dm @üye [mesaj]** - Kişiye DM atar.\n"
                "**.pen** - Penaltı atar (Gol/Kale/Aut) — ardarda aynı sonuç çıkmaz!\n"
                "**.up @üye** - Rol yükseltir (Sahip/Özel).\n"
                "**.deup @üye** - Rol düşürür (Sahip)."
            )
        await interaction.response.edit_message(embed=embed)


@bot.command()
async def yardım(ctx):
    view = ui.View()
    view.add_item(YardimDropDown())
    embed = discord.Embed(
        title="NOVA PLUS | YARDIM MENÜSÜ",
        description="Aşağıdaki menüden kategori seçin.",
        color=0x2f3136
    )
    await ctx.send(embed=embed, view=view)


# ====================== BOT ÇALIŞTIR ======================
if not TOKEN:
    print("❌ HATA: DISCORD_TOKEN bulunamadı! Lütfen Railway'de çevre değişkenleri (Variables) kısmına tokeninizi ekleyin.")
else:
    bot.run(TOKEN)

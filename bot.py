import discord
from discord.ext import commands
from discord import ui
import datetime
import asyncio
import random
import os

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

# Veri Saklama Alanları
son_silinenler = {}
afk_kullanicilar = {}
kap_bellek = {}
kayit_sayaci = {}
deger_sayaci = {}
antrenman_sayac = {}
mesaj_sayaci = {}
snipe_all_listesi = {}
aktif_bilgi_oyunu = {}
aktif_vampir_oyunu = {}

@bot.event
async def on_ready():
    print(f'--------------------------------------------------')
    print(f'🚀 NOVA PLUS SİSTEMİ %100 KAPASİTEYLE ÇALIŞIYOR!')
    print(f'🤖 Bot Kullanıcı Adı: {bot.user.name}')
    print(f'🆔 Bot ID: {bot.user.id}')
    print(f'📅 Tarih: {datetime.datetime.now().strftime("%d/%m/%Y")}')
    print(f'--------------------------------------------------')
    await bot.change_presence(activity=discord.Streaming(name=".yardım | NOVA PLUS", url="https://twitch.tv/NOVA"))


# --- OLAYLAR ---
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

    kanal_id = message.channel.id
    if kanal_id not in snipe_all_listesi:
        snipe_all_listesi[kanal_id] = []
    snipe_all_listesi[kanal_id].append({"yazar": message.author, "icerik": message.content, "zaman": datetime.datetime.now()})
    simdi = datetime.datetime.now()
    snipe_all_listesi[kanal_id] = [m for m in snipe_all_listesi[kanal_id] if (simdi - m["zaman"]).total_seconds() < 300]

    if message.author.id in afk_kullanicilar:
        del afk_kullanicilar[message.author.id]
        await message.channel.send(f"👋 Tekrar hoş geldin {message.author.mention}! AFK modundan çıkarıldın.", delete_after=5)

    for mention in message.mentions:
        if mention.id in afk_kullanicilar:
            sebep = afk_kullanicilar[mention.id]
            await message.channel.send(f"⚠️ {mention.name} şu an AFK durumda! \n📝 Sebep: **{sebep}**")

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
            await interaction.response.send_message("❌ Bu üyeyi şu an başkası kaydediyor, 10 dakika sonra tekrar deneyin!", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="ÜSTLEN", style=discord.ButtonStyle.success, emoji="✅")
    async def ustlen_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not kayit_yetkisi_var_mi(interaction.user):
            await interaction.response.send_message("❌ Bu butonu kullanmak için **Kayıt Yetkilisi** rolüne sahip olmalısın!", ephemeral=True)
            return
        button.disabled = True
        button.label = f"{interaction.user.display_name} üstlendi"
        embed = interaction.message.embeds[0]
        embed.description = f"**{self.uye.mention}** kullanıcısının kaydı **{interaction.user.mention}** tarafından üstlenildi!\n\n📝 Kayıt komutu: `.k {self.uye.mention} İsim | Değer | Takım`"
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
        description=f"**{member.mention}** sunucuya katıldı!\n\nAşağıdaki **ÜSTLEN** butonuna basarak bu üyenin kaydını yapabilirsin.",
        color=0xFF6B00,
        timestamp=datetime.datetime.now()
    )
    embed.add_field(name="👤 Kullanıcı", value=f"{member.name}#{member.discriminator}", inline=True)
    embed.add_field(name="🆔 ID", value=f"`{member.id}`", inline=True)
    embed.add_field(name="📅 Katılım Tarihi", value=f"<t:{int(datetime.datetime.now().timestamp())}:R>", inline=True)
    embed.set_footer(text="Üstlenen kişi 10 dakika boyunca kayıt yapabilir")
    view = UstelenView(member)
    await kanal.send(embed=embed, view=view)


# ====================== MODERASYON KOMUTLARI ======================
@bot.command()
@commands.has_permissions(manage_channels=True)
async def lock(ctx):
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False)
    embed = discord.Embed(title="🔒 Kanal Kilidlendi", description=f"Bu kanal {ctx.author.mention} tarafından mesaj gönderimine kapatıldı.", color=0xff0000)
    await ctx.send(embed=embed)


@bot.command()
@commands.has_permissions(manage_channels=True)
async def unlock(ctx):
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=True)
    embed = discord.Embed(title="🔓 Kanal Kilidi Açıldı", description=f"Bu kanal {ctx.author.mention} tarafından tekrar mesaj gönderimine açıldı.", color=0x00ff00)
    await ctx.send(embed=embed)


@bot.command()
@commands.has_permissions(ban_members=True)
async def unban(ctx, user_id: int):
    try:
        user = await bot.fetch_user(user_id)
        await ctx.guild.unban(user)
        embed = discord.Embed(title="✅ Ban Kaldırıldı", description=f"{user.name}#{user.discriminator} adlı kullanıcının yasağı kaldırıldı.", color=0x2ecc71)
        await ctx.send(embed=embed)
    except discord.NotFound:
        await ctx.send("❌ Bu ID'ye sahip bir yasaklama bulunamadı.")
    except Exception as e:
        await ctx.send(f"❌ Bir hata oluştu: `{e}`")


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
        await ctx.send(f"❌ Mute hatası: `{e}`")


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
        await ctx.send(f"❌ Unmute hatası: `{e}`")


@bot.command()
@commands.has_permissions(manage_nicknames=True)
async def isim(ctx, member: discord.Member, *, yeni_isim):
    try:
        await member.edit(nick=yeni_isim)
        await ctx.send(f"✅ {member.name} kullanıcısının yeni ismi: `{yeni_isim}`")
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


# ====================== ROL KOMUTLARI ======================
@bot.command()
async def rolver(ctx, member: discord.Member, *, rol: discord.Role):
    if not rol_yetkisi_var_mi(ctx.author):
        return await ctx.send("❌ Bu komutu kullanmak için yetkiniz yok!")
    try:
        await member.add_roles(rol)
        embed = discord.Embed(title="🎭 Rol Verildi", description=f"{member.mention} kullanıcısına {rol.mention} rolü verildi.", color=0x3498db)
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"❌ Hata: `{e}`")


@bot.command()
async def rolal(ctx, member: discord.Member, *, rol: discord.Role):
    if not rol_yetkisi_var_mi(ctx.author):
        return await ctx.send("❌ Bu komutu kullanmak için yetkiniz yok!")
    try:
        await member.remove_roles(rol)
        embed = discord.Embed(title="🎭 Rol Alındı", description=f"{member.mention} kullanıcısından {rol.mention} rolü geri alındı.", color=0xe67e22)
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"❌ Hata: `{e}`")


@bot.command()
async def toplurolver(ctx, *, girdi: str):
    if not rol_yetkisi_var_mi(ctx.author):
        return await ctx.send("❌ Bu komutu kullanmak için yetkiniz yok!")
    try:
        parcalar = girdi.split(' ', 1)
        if len(parcalar) < 2:
            return await ctx.send("❌ Hatalı Kullanım! \nÖrnek: `.toplurolver @Kullanıcı Rol 1, Rol 2` veya `.toplurolver hepsi Oyuncu`")
        hedef = parcalar[0]
        roller_metni = parcalar[1]
        rol_adlari = [r.strip() for r in roller_metni.split(',')]
        verilecek_rollar = []
        for ad in rol_adlari:
            rol = discord.utils.get(ctx.guild.roles, name=ad)
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
            return await ctx.send("❌ Lütfen birini etiketleyin veya `hepsi` yazın.")
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
        await islem_mesaji.edit(content=f"✅ İşlem Tamamlandı! \n👥 Toplam **{sayac}** kişiye `{', '.join([r.name for r in verilecek_rollar])}` rolleri başarıyla tanımlandı.")
    except Exception as e:
        await ctx.send(f"⚠️ Kritik bir hata oluştu: `{e}`")


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
            rol = discord.utils.get(ctx.guild.roles, name=ad)
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
            return await ctx.send("❌ Lütfen birini etiketleyin veya `hepsi` yazın.")
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
        await islem_mesaji.edit(content=f"✅ Başarılı! \n👥 **{sayac}** kişiden belirtilen roller geri alındı.")
    except Exception as e:
        await ctx.send(f"⚠️ Hata: `{e}`")


# ====================== EĞLENCE KOMUTLARI ======================
@bot.command()
async def roll(ctx, *, secenekler: str):
    liste = [s.strip() for s in secenekler.split(',')]
    if len(liste) < 2:
        return await ctx.send("❌ Lütfen en az iki seçeneği virgül ile ayırın!")
    secim = random.choice(liste)
    embed = discord.Embed(title="🎲 Karar Verildi!", description=f"Seçenekler: `{', '.join(liste)}` \n\n✨ Sonuç: **{secim}**", color=discord.Color.purple())
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
    afk_kullanicilar[ctx.author.id] = sebep
    await ctx.send(f"✅ {ctx.author.mention} artık AFK! Sebep: **{sebep}**")


@bot.command()
async def ship(ctx, member: discord.Member):
    oran = random.randint(0, 100)
    emoji = "❤️" if oran > 50 else "💔"
    await ctx.send(f"📊 {ctx.author.mention} ❤️ {member.mention} \n💘 Aşk Uyumu: **%{oran}** {emoji}")


@bot.command()
async def ara(ctx, *, isim: str):
    bulananlar = []
    aranan_kucuk = isim.lower()
    for member in ctx.guild.members:
        if member.bot: continue
        if aranan_kucuk in member.display_name.lower() or aranan_kucuk in member.name.lower():
            bulananlar.append(member)
    if not bulananlar:
        return await ctx.send(f"❌ **{isim}** adında veya içinde geçen isimde sunucuda kimse bulunamadı!")
    if len(bulananlar) > 15:
        kalan_mesaj = f"\n\n*...ve {len(bulananlar) - 15} kişi daha (toplam {len(bulananlar)} kişi)*"
        bulananlar = bulananlar[:15]
    else:
        kalan_mesaj = ""
    liste_metni = "\n".join([f"• {m.mention}  `(Takma ad: {m.display_name})`" for m in bulananlar])
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
        return None, "İsim formatı hatalı! Format: `Ad | 1M | ...`"
    mevcut = parse_deger(parcalar[1])
    if mevcut is None:
        return None, "Mevcut değer okunamadı!"
    eklenecek = parse_deger(miktar_str)
    if eklenecek is None:
        return None, f"`{miktar_str}` geçersiz bir değer!"
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
            return await ctx.send(embed=hata_embed(f"❌ **{uye.display_name}** isminde '|' işareti yok!\nFormat: `Ad | 1M | Takım` olmalı."))
        eski_deger = parcalar[1].strip()
        yeni_isim, islem_detay = deger_isle(mevcut_isim, miktar, "ekle")
        if yeni_isim is None:
            return await ctx.send(embed=hata_embed(islem_detay))
        try:
            await uye.edit(nick=yeni_isim)
        except discord.Forbidden:
            return await ctx.send(embed=hata_embed("❌ İsim değiştirilemedi! Botun rolü bu üyenin rolünden yüksek olmalı."))
        except Exception as hata:
            return await ctx.send(embed=hata_embed(f"❌ Discord hatası: `{hata}`"))
        deger_sayaci[ctx.author.id] = deger_sayaci.get(ctx.author.id, 0) + 1
        yeni_parcalar = yeni_isim.split("|")
        yeni_deger = yeni_parcalar[1].strip() if len(yeni_parcalar) >= 2 else "?"
        await ctx.send(embed=basari_embed(f"**{uye.mention}** değeri güncellendi: {islem_detay}\n📝 Yeni isim: `{yeni_isim}`"))
        await log_deger_gonder(ctx.guild, ctx.author, uye, eski_deger, yeni_deger, "➕ Değer Eklendi", sebep)
    except Exception as e:
        await ctx.send(embed=hata_embed(f"Hata: `{e}`"))


@bot.command(name="dsil")
async def dsil(ctx, uye: discord.Member, miktar: str = None, *, sebep: str = "Belirtilmedi"):
    try:
        if not deger_yetkisi_var_mi(ctx.author):
            return await ctx.send(embed=hata_embed("Bu komutu kullanmak için **Değer Yetkilisi** rolüne sahip olmalısın!"))
        mevcut_isim = uye.display_name
        parcalar = mevcut_isim.split("|")
        if len(parcalar) < 2:
            return await ctx.send(embed=hata_embed(f"❌ **{uye.display_name}** isminde '|' işareti yok!\nFormat: `Ad | 1M | Takım` olmalı."))
        eski_deger = parcalar[1].strip()
        if miktar is None:
            parcalar[1] = "0M"
            yeni_isim = " | ".join(parcalar)
            try:
                await uye.edit(nick=yeni_isim)
            except discord.Forbidden:
                return await ctx.send(embed=hata_embed("❌ İsim değiştirilemedi! Botun rolü bu üyenin rolünden yüksek olmalı."))
            except Exception as hata:
                return await ctx.send(embed=hata_embed(f"❌ Discord hatası: `{hata}`"))
            deger_sayaci[ctx.author.id] = deger_sayaci.get(ctx.author.id, 0) + 1
            await ctx.send(embed=basari_embed(f"**{uye.mention}** değeri sıfırlandı: `{eski_deger}` → `0M`\n📝 Yeni isim: `{yeni_isim}`"))
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
            return await ctx.send(embed=hata_embed(f"❌ Discord hatası: `{hata}`"))
        deger_sayaci[ctx.author.id] = deger_sayaci.get(ctx.author.id, 0) + 1
        yeni_parcalar = yeni_isim.split("|")
        yeni_deger = yeni_parcalar[1].strip() if len(yeni_parcalar) >= 2 else "?"
        await ctx.send(embed=basari_embed(f"**{uye.mention}** değeri güncellendi: {islem_detay}\n📝 Yeni isim: `{yeni_isim}`"))
        await log_deger_gonder(ctx.guild, ctx.author, uye, eski_deger, yeni_deger, "➖ Değer Çıkarıldı", sebep)
    except Exception as e:
        await ctx.send(embed=hata_embed(f"Hata: `{e}`"))


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
                embed=hata_embed("Bu seçimi yalnızca komutu kullanan kişi yapabilir!"), ephemeral=True)
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
                embed=hata_embed(f"Sunucuda şu roller bulunamadı: `{'`, `'.join(eksik)}`"), view=None)
        if kayitsiz_rol and kayitsiz_rol in hedef.roles:
            try:
                await hedef.remove_roles(kayitsiz_rol)
            except:
                pass
        try:
            await hedef.add_roles(baskan_rol, kayitli_rol, takim_rol)
        except Exception as e:
            return await interaction.response.edit_message(embed=hata_embed(f"Rol verilemedi: `{e}`"), view=None)
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
        sonuc.add_field(name="📝 Nick", value=f"`{yeni_nick}`", inline=True)
        sonuc.add_field(name="🎭 Verilen Roller", value=f"`{ROL_TAKIM_BASKANI}`, `{KAYITLI_ROL}`, `{takim_adi}`", inline=False)
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
                embed=hata_embed("Bu butonları yalnızca komutu kullanan kişi kullanabilir!"), ephemeral=True)
            return False
        return True

    async def kayit_yap(self, interaction: discord.Interaction, rol_adi: str):
        if self.kullanildi:
            return await interaction.response.send_message(embed=hata_embed("Bu kayıt zaten tamamlandı!"), ephemeral=True)
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
        sonuc.add_field(name="📝 Nick", value=f"`{yeni_nick}`", inline=True)
        sonuc.add_field(name="🎭 Verilen Rol", value=f"`{rol_adi}` + `{KAYITLI_ROL}`", inline=False)
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
            return await interaction.response.send_message(embed=hata_embed("Bu kayıt zaten başlatıldı!"), ephemeral=True)
        self.kullanildi = True
        takim_view = TakimSecView(hedef=self.hedef, yeni_nick=self.yeni_nick, yapan_id=self.yapan.id)
        embed = discord.Embed(
            title="👑 Takım Başkanı — Takım Seçin",
            description=f"**{self.hedef.mention}** için hangi takımın başkanı olacağını aşağıdaki menüden seçin.\n📝 Nick: `{self.yeni_nick}`",
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
        return await ctx.send(embed=hata_embed("Kullanım: `.k @üye L.Messi | 1M | SNT`"))
    embed = discord.Embed(
        title="📋 Kayıt Türü Seç",
        description=f"**{uye.mention}** için kayıt türü seçin.\n📝 Nick: `{yeni_nick}`",
        color=0x5865F2
    )
    embed.set_footer(text="Aşağıdaki butonlardan birini seçin")
    view = KayitSecimView(hedef=uye, yeni_nick=yeni_nick, yapan=ctx.author)
    await ctx.send(embed=embed, view=view)


# --- ANTRENMAN KOMUTU ---
@bot.command(name="antrenman")
async def antrenman(ctx):
    if ANTRENMAN_KANAL_ID != 0 and ctx.channel.id != ANTRENMAN_KANAL_ID:
        return await ctx.send("❌ Bu komutu sadece antrenman kanalında kullanabilirsin!")
    uye = ctx.author
    mevcut = antrenman_sayac.get(uye.id, 0) + 1
    if mevcut > 10:
        mevcut = 1
    antrenman_sayac[uye.id] = mevcut
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
                    f"📊 Değer: `{eski_d}` → `{yeni_d}`\n"
                    f"📝 Yeni isim: `{yeni_isim}`"))
                await log_deger_gonder(ctx.guild, ctx.author, uye, eski_d, yeni_d, "🏋️ Antrenman Tamamlandı (+3M)", "Antrenman ödülü verildi")
            except (discord.Forbidden, discord.HTTPException):
                await ctx.send(embed=basari_embed(
                    f"💰 {uye.mention} antrenman ödülü: **+3M** kazandı!\n"
                    f"📊 Değer: `{eski_d}` → `{yeni_d}`\n"
                    f"⚠️ İsim güncellenemedi, manuel güncelle: `{yeni_isim}`"))
                await log_deger_gonder(ctx.guild, ctx.author, uye, eski_d, yeni_d, "🏋️ Antrenman Tamamlandı (+3M)", "Antrenman ödülü (İsim değiştirilemedi)")
        else:
            await ctx.send(embed=hata_embed(
                f"{uye.mention} 10/10 tamamladı fakat isim formatı hatalı!\n"
                f"Format: `Ad | 1M | takım | SNT` olmalı."))
        antrenman_sayac[uye.id] = 0


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
            await interaction.response.send_message(f"❌ **{eski}** geçersiz bir takım adı!\n\n📋 Geçerli takımlar:\n" + "\n".join([f"• {t}" for t in TAKIM_ROLLERI.keys()]), ephemeral=True)
            return
        kap_bellek[interaction.user.id] = {
            "oid": self.oid.value, "oyuncu": self.oyuncu_ismi.value,
            "eski": self.eski_takim.value, "bonservis": self.bonservis.value, "yillik_maas": self.yillik_maas.value
        }
        await interaction.response.send_message("✅ 1. kısım alındı. 2. kısma geçmek için butona basın.", ephemeral=True, view=TransferDevamView())


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
            await interaction.response.send_message(f"❌ **{yeni}** geçersiz bir takım adı!\n\n📋 Geçerli takımlar:\n" + "\n".join([f"• {t}" for t in TAKIM_ROLLERI.keys()]), ephemeral=True)
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
            await interaction.response.send_message(f"❌ **{hatali_takim}** geçersiz bir takım! Rol verilmedi.", ephemeral=True)
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
        await interaction.response.send_message(f"❌ Hata: `{e}`", ephemeral=True)


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
            await interaction.response.send_message(f"❌ **{eski}** geçersiz bir takım adı!\n\n📋 Geçerli takımlar:\n" + "\n".join([f"• {t}" for t in TAKIM_ROLLERI.keys()]), ephemeral=True)
            return
        kap_bellek[interaction.user.id] = {
            "oid": self.oid.value, "oyuncu": self.oyuncu_ismi.value,
            "eski": self.eski_takim.value, "kiralama_bedeli": self.kiralama_bedeli.value, "yillik_maas": self.yillik_maas.value
        }
        await interaction.response.send_message("✅ 1. kısım alındı. 2. kısma geçmek için butona basın.", ephemeral=True, view=KiralikDevamView())


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
            await interaction.response.send_message(f"❌ **{yeni}** geçersiz bir takım adı!\n\n📋 Geçerli takımlar:\n" + "\n".join([f"• {t}" for t in TAKIM_ROLLERI.keys()]), ephemeral=True)
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
            await interaction.response.send_message(f"❌ **{hatali_takim}** geçersiz bir takım! Rol verilmedi.", ephemeral=True)
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
        await interaction.response.send_message(f"❌ Hata: `{e}`", ephemeral=True)


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
                await interaction.response.send_message(f"❌ **{takim_adi}** geçersiz bir takım adı!\n\n📋 Geçerli takımlar:\n" + "\n".join([f"• {t}" for t in TAKIM_ROLLERI.keys()]), ephemeral=True)
                return
            member = await interaction.guild.fetch_member(int(self.oid.value))
            await kap_rol_islemi(member, boslari_x(self.takim.value))
            embed = discord.Embed(title="**SÖZLEŞME YENİLEME KAP AÇIKLAMASI**", color=0x2ecc71, timestamp=datetime.datetime.now())
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
            await interaction.response.send_message(f"❌ Hata: `{e}`", ephemeral=True)


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
                await interaction.response.send_message(f"❌ **{takim_adi}** geçersiz bir takım adı!\n\n📋 Geçerli takımlar:\n" + "\n".join([f"• {t}" for t in TAKIM_ROLLERI.keys()]), ephemeral=True)
                return
            member = await interaction.guild.fetch_member(int(self.oid.value))
            await kap_rol_islemi(member, boslari_x(self.eski_takim.value))
            embed = discord.Embed(title="**FESİH KAP AÇIKLAMASI**", color=0xe74c3c, timestamp=datetime.datetime.now())
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
            await interaction.response.send_message(f"❌ Hata: `{e}`", ephemeral=True)


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
    async def FESH(self, interaction: discord.Interaction, button):
        await interaction.response.send_modal(FESHModal())


@bot.command()
async def kap(ctx):
    takim_listesi = "\n".join([f"• {t}" for t in TAKIM_ROLLERI.keys()])
    embed = discord.Embed(
        title="📣 NOVA PLUS | KAP YÖNETİM PANELİ",
        description=f"Aşağıdan istediğiniz işlemi seçin:\n*(Transfer ve Kiralama işlemleri 2 aşamalıdır)*\n\n📋 **Geçerli Takımlar:**\n{takim_listesi}",
        color=0x2f3136
    )
    await ctx.send(embed=embed, view=KAPPaneli())


# ====================== ETKİNLİK SİSTEMİ ======================

OYUNLAR = {
    "🎯 Değer Tahmini": {
        "aciklama": "Yetkili rastgele bir oyuncu seçer, herkes o oyuncunun değerini tahmin eder. En yakın olan kazanır!",
        "nasil": "Yetkili `.ara [isim]` ile oyuncuyu bulur. Herkes sohbete tahminini yazar. En yakın tahmin eden kazanır!",
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
        "nasil": "Sırayla her kişi `.cark` yazar. Bot rastgele bir sonuç seçer. Ödül mü, ceza mı? Şansına bak!",
        "katilimci": "Herkes",
        "sure": "Sınırsız",
        "emoji": "🎲"
    },
    "⚡ Hızlı Bilgi": {
        "aciklama": "Bot futbol soruları sorar! 10 saniye içinde doğru cevaplayan puan kazanır. En çok puan toplayan şampiyon!",
        "nasil": "`.bilgi` komutuyla soru gelir. Herkes cevabını yazar. İlk ve doğru cevap veren 1 puan alır. 5 puana ulaşan kazanır!",
        "katilimci": "2+ kişi",
        "sure": "10–15 dakika",
        "emoji": "⚡"
    },
    "🔀 Kim Kimle Eşleşir?": {
        "aciklama": "Bot sunucudaki iki oyuncuyu rastgele eşleştirir! Antrenman partneri, transfer tahmini veya saf eğlence için!",
        "nasil": "`.eslestir` komutuyla bot iki kişiyi rastgele eşleştirir ve uyum yüzdesini açıklar. Eğlenceli sonuçlar garantili!",
        "katilimci": "2+ kişi",
        "sure": "5 dakika",
        "emoji": "🔀"
    },
    "🧛 Vampir Köylü": {
        "aciklama": "Klasik Vampir Köylü oyunu! 2 Vampir gizlice birini öldürür, Köylüler ise oylama ile vampiri bulmaya çalışır.",
        "nasil": "`.vk` komutu ile başlatın ve katılın. Bot size özel rolünüzü (Vampir/Köylü) DM'den söyler. Vampirler gece DM'den hedef seçer, gündüz herkes oylama yapar.",
        "katilimci": "5–20 kişi",
        "sure": "15–30 dakika",
        "emoji": "🧛"
    },
}

CARK_SONUCLARI = [
    ("🏆 BÜYÜK ÖDÜL", "Tebrikler! Bir yetkili sana **+5M** değer ekleyecek!", "odul", 0x2ECC71),
    ("⭐ KÜÇÜK ÖDÜL", "Tebrikler! Bir yetkili sana **+1M** değer ekleyecek!", "odul", 0x27AE60),
    ("🎁 SÜRPRİZ ÖDÜL", "Yetkili istediği özel ödülü seçiyor! Ne çıkacak bilinmez...", "odul", 0xF39C12),
    ("🧛 VAMPİR İŞARETİ", "Bir sonraki Vampir Köylü oyununda otomatik olarak **Vampir** olacaksın!", "odul", 0x8E44AD),
    ("🛡️ KÖYLÜ KALKANI", "Bir sonraki Vampir Köylü oyununda geceleyin bir kez ölümden kurtulma hakkın var!", "odul", 0x2ECC71),
    ("😂 UTANÇ CEZASI", "5 dakika boyunca profilinde en utanç verici fotoğrafı kullanacaksın!", "ceza", 0xE67E22),
    ("💀 SUSTURMA CEZASI", "1 dakika sessize alındın! Çarkın adaleti böyle!", "ceza", 0xE74C3C),
    ("⚡ DEĞER DEĞİŞİMİ", "Yanındaki kişiyle değerlerinin yarısı el değiştirir! Yetkili uygular.", "ceza", 0x9B59B6),
    ("🔁 TEKRAR ÇEVİR", "Şans sana gülmedi! Bir kez daha çevirme hakkın var.", "notr", 0x3498DB),
    ("🌟 ŞAMPIYON UNVANI", "Bu haftalık 'Çark Şampiyonu' unvanı senin! Tebrikler!", "odul", 0xF1C40F),
    ("🎭 ROL DEĞİŞİMİ", "Bir sonraki mesajında başka bir kullanıcının adına konuşacaksın!", "notr", 0x1ABC9C),
    ("💸 DEĞERSİZ", "Bugünlük değerin sıfırlandı sayılır! (Gerçek değil, sadece roleplay!)", "ceza", 0xC0392B),
    ("🩸 KAN KAYBI", "Vampirler seni buldu! Bir yetkili senden **-2M** değer çıkaracak!", "ceza", 0xE74C3C),
    ("🏥 DOKTOR MÜDAHALESİ", "Tam ölecektin ama doktor yetişti! Değerin sabit kalıyor, şanslısın!", "notr", 0x3498DB),
]

BILGI_SORULARI = [
    ("1954 Dünya Kupası'nda 'Büyük Facia' olarak bilinen olayda hangi takım, favori olduğu halde ilk turda elenmiştir?", "macaristan", "🇭🇺 Macaristan — Sırrı Ortaç'ın unutulmaz röportajının konusu!"),
    ("FIFA Dünya Kupası tarihinde 'Maracanazo' olarak bilinen şok sonuca hangi maç damga vurmuştur?", "uruguay brezilya", "🇺🇾 1950'de Uruguay, Brezilya'yı kendi evinde yenmiştir!"),
    ("İngiltere Premier League'deArsenal'in 'Invincibles' (Yenilmezler) sezonunda kaç maçta yenilmedikleri tarihe geçmiştir?", "49", "🏆 2003-2004 sezonunda tam 49 maç!"),
    ("Lionel Messi'nin Barcelona'daki tek bir sezonda en fazla gol attığı '60+' gol rekorunu kırdığı sezon hangi yıla aittir?", "2012", "⚽ 2011-2012 sezonunda tam 73 gol atmıştır!"),
    ("Serie A tarihinde 'Calciopoli' skandalı sonucunda 2006'da şampiyonluğu elinden alınan takım hangisidir?", "juventus", "⚫⚪ Juventus şampiyonluğu gasp edilmiş ve Serie B'ye düşürülmüştür!"),
    ("Bir futbol maçında bir kalecinin attığı golden sonra 'Kaleci Golü' denmez de literatüre girmiş özel bir gol türü olan 'Olimpik Gol' hangi yöntemle atılır?", "açaraktan", "🥅 Açıktan ayağı değer touching yapmadan doğrudan kaleye!"),
    ("UEFA Şampiyonlar Ligi'nde bir takımın aynı maç içinde 4-0 geriden gelip kazandığı tarihi 'Miracle of Istanbul' (İstanbul Mucizesi) maçı hangi yıldadır?", "2005", "🔴 Liverpool, 2005 finalinde Milan'ı penaltılarla geçmiştir!"),
    ("Galatasaray'ın 2000 UEFA Kupası finalinde attığı tarihi gollerin toplam skoru kaçtır?", "4-1", "🦁 Galatasaray, Arsenal'i ekstra sürelerde 4-1 mağlup etmiştir!"),
    ("Hugo Sánchez'in attığı 'Rabbit Jump' (Tavşan Zıplaması) olarak bilinen ve literatüre giren şutun özelliği nedir?", "ters çevrilerek zıplayar", "🐰 Meksikalı efsane golü atarken arka arkaya zıplardı!"),
    ("Real Madrid'in 'Los Galácticos' (Galaksi Takımı) döneminde 2000 yılında transfer edilen ilk efsanevi isim hangisidir?", "figo", "⭐ Luís Figo, Barcelona'dan Real Madrid'e transfer olmuştu!"),
    ("FIFA kurallarına göre bir futbol topunun çeper uzunluğunun (çevresinin) santimetre cinsinden kabul edilen resmi aralığı nedir?", "68-70", "📏 68 cm ile 70 cm arasında olmalıdır!"),
    ("Hangi Afrika ülkesi, Dünya Kupası tarihinde çeyrek finale yükselen ilk ve tek takım unvanını taşımaktadır?", "kamerun gana senegal marako", "🌍 Kamerun (1990), Senegal (2002) ve Gana (2010) çeyrek final görmüştür!"),
    ("Bir penaltı atışında kalecinin çizgiden kaymadan önce kalecinin hareket etmesi durumunda uygulanacak kuralın FIFA'daki tam adı nedir?", "erken hareket", "🚫 Kaleci çizgiden erken çıkarsa penaltı tekrar atılır!"),
    ("Trabzonspor'un 1970'lerde Türkiye 1. Ligi'ni 3 kez üst üste kazandığı 'Efsanevi 3'lü' dönemine hangi teknik direktör başkanlık etmiştir?", "ahmet sualp", "🎨 Ahmet Sualp ile Trabzonspor'un altın çağı başlamıştır!"),
]

# Aktif bilgi oyunu takibi
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
            embed=discord.Embed(title="✅ Etkinlik Başlatıldı!", description=f"**{secilen}** etkinliği seçildi.", color=0x2ECC71),
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


# --- ŞANS ÇARKI KOMUTU ---
@bot.command(name="cark")
async def cark(ctx, uye: discord.Member = None):
    hedef = uye or ctx.author

    animasyon = await ctx.send(f"🎲 **{hedef.display_name}** için çark çevriliyor...")
    await asyncio.sleep(0.8)
    await animasyon.edit(content=f"🌀 **Çark dönüyor...** ◐")
    await asyncio.sleep(0.6)
    await animasyon.edit(content=f"🌀 **Çark dönüyor...** ◓")
    await asyncio.sleep(0.6)
    await animasyon.edit(content=f"🌀 **Çark dönüyor...** ◑")
    await asyncio.sleep(0.6)
    await animasyon.edit(content=f"🌀 **Çark yavaşlıyor...** ◒")
    await asyncio.sleep(0.8)

    sonuc_adi, sonuc_aciklama, tur, renk = random.choice(CARK_SONUCLARI)

    embed = discord.Embed(
        title=f"🎡 ŞANS ÇARKI SONUCU",
        color=renk,
        timestamp=datetime.datetime.now()
    )
    embed.add_field(name="👤 Oyuncu", value=hedef.mention, inline=True)
    embed.add_field(name="🎯 Sonuç", value=f"**{sonuc_adi}**", inline=True)
    embed.add_field(name="📋 Ne Olacak?", value=sonuc_aciklama, inline=False)

    if tur == "odul":
        embed.set_footer(text="🎉 Tebrikler! Şans sana güldü!")
    elif tur == "ceza":
        embed.set_footer(text="😈 Çarkın adaleti işledi!")
    else:
        embed.set_footer(text="🔄 Ne ödül ne ceza, ortada kaldın!")

    await animasyon.delete()
    await ctx.send(embed=embed)


# --- HIZLI BİLGİ KOMUTU ---
@bot.command(name="bilgi")
async def bilgi(ctx):
    if ctx.channel.id in aktif_bilgi_oyunu:
        return await ctx.send("❌ Bu kanalda zaten aktif bir bilgi oyunu var! Bitmesini bekleyin.")

    # Tüm soruların hepsi kullanıldıysa sıfırla
    if len(kullanilan_bilgi_sorulari) >= len(BILGI_SORULARI):
        kullanilan_bilgi_sorulari.clear()

    # Kullanılmamış soru seç
    available_sorular = [s for s in BILGI_SORULARI if BILGI_SORULARI.index(s) not in kullanilan_bilgi_sorulari]
    if not available_sorular:
        kullanilan_bilgi_sorulari.clear()
        available_sorular = BILGI_SORULARI

    soru_ogesi = random.choice(available_sorular)
    soru, cevap, aciklama = soru_ogesi
    kullanilan_bilgi_sorulari.append(BILGI_SORULARI.index(soru_ogesi))

    aktif_bilgi_oyunu[ctx.channel.id] = {"cevap": cevap, "aciklama": aciklama, "soruldu": True}

    embed = discord.Embed(
        title="⚡ HIZLI BİLGİ SORUSU!",
        description=f"**{soru}**\n\n⏰ 20 saniye içinde cevapla!",
        color=0xF1C40F,
        timestamp=datetime.datetime.now()
    )
    embed.set_footer(text="İlk doğru cevap veren 1 puan kazanır! | .bilgi komutu")
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

    embed = discord.Embed(
        title="🔀 RASTGELE EŞLEŞTİRME",
        color=renk,
        timestamp=datetime.datetime.now()
    )
    embed.add_field(name="👤 Oyuncu 1", value=ctx.author.mention, inline=True)
    embed.add_field(name=emoji, value=f"**%{uyum}**", inline=True)
    embed.add_field(name="👤 Oyuncu 2", value=eslesen.mention, inline=True)
    embed.add_field(name="💬 Yorum", value=yorum, inline=False)
    embed.set_footer(text="Rastgele eşleştirme sistemi")
    await ctx.send(embed=embed)


# ====================== VAMPİR KÖYLÜ SİSTEMİ ======================

class VampirKatilimView(ui.View):
    def __init__(self, kanal_id):
        super().__init__(timeout=120)
        self.kanal_id = kanal_id

    @discord.ui.button(label="🧛 Katıl", style=discord.ButtonStyle.danger, emoji="🩸")
    async def katil_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        kanal = bot.get_channel(self.kanal_id)
        if not kanal or kanal.id not in aktif_vampir_oyunu:
            return await interaction.response.send_message("❌ Oyun zaman aşımına uğradı veya başlatılmadı!", ephemeral=True)
        
        oyuncular = aktif_vampir_oyunu[self.kanal_id]["oyuncular"]
        if interaction.user.id in oyuncular:
            return await interaction.response.send_message("❌ Zaten oyuna katıldın!", ephemeral=True)
        if len(oyuncular) >= 20:
            return await interaction.response.send_message("❌ Oyun dolu!", ephemeral=True)

        oyuncular.append(interaction.user.id)
        await interaction.response.send_message("✅ Oyuna başarıyla katıldın! Beklemede kal...", ephemeral=True)
        
        guncel_sayi = len(oyuncular)
        mesaj = interaction.message
        embed = mesaj.embeds[0]
        embed.clear_fields()
        embed.add_field(name="👥 Katılımcı Sayısı", value=f"**{guncel_sayi} / 20**", inline=True)
        embed.add_field(name="⏳ Kalan Süre", value="**2 Dakika**", inline=True)
        await mesaj.edit(embed=embed, view=self)


async def baslat_vampir_oyunu(ctx):
    kanal_id = ctx.channel.id
    aktif_vampir_oyunu[kanal_id] = {
        "oyuncular": [ctx.author.id],
        "roller": {},
        "hayatta": [],
        "vampirler": [],
        "basladi": False
    }

    embed = discord.Embed(
        title="🧛 VAMPİR KÖYLÜ BAŞLADI!",
        description="Köy karanlığa gömüldü... Aranızda 2 kan emici Vampir var! Onları bulmak için belowdaki butona bas ve hayatta kalma şansını artır!",
        color=0x8E44AD,
        timestamp=datetime.datetime.now()
    )
    embed.add_field(name="👥 Katılımcı Sayısı", value="**1 / 20**", inline=True)
    embed.add_field(name="⏳ Kalan Süre", value="**2 Dakika**", inline=True)
    embed.set_footer(text="Oyun 2 dakika içinde veya 5 kişi olduğunda otomatik başlayacaktır.")
    
    view = VampirKatilimView(kanal_id)
    mesaj = await ctx.send(embed=embed, view=view)

    # 2 dakika bekleme veya 5 kişi olma kontrolü
    for _ in range(24): # 24 * 5sn = 120sn = 2dk
        await asyncio.sleep(5)
        if kanal_id not in aktif_vampir_oyunu:
            return
        
        mevcut_oyuncular = aktif_vampir_oyunu[kanal_id]["oyuncular"]
        if len(mevcut_oyuncular) >= 5:
            break

    if kanal_id not in aktif_vampir_oyunu:
        return

    mevcut_oyuncular = aktif_vampir_oyunu[kanal_id]["oyuncular"]
    if len(mevcut_oyuncular) < 4:
        del aktif_vampir_oyunu[kanal_id]
        await mesaj.edit(content="❌ Oyun iptal edildi! Yeterli katılımcı yok (Minimum 4 kişi gerekli).", embed=None, view=None)
        return

    # Roller dağıtımı
    aktif_vampir_oyunu[kanal_id]["hayatta"] = mevcut_oyuncular.copy()
    random.shuffle(mevcut_oyuncular)
    
    secilen_vampirler = mevcut_oyuncular[:2]
    aktif_vampir_oyunu[kanal_id]["vampirler"] = secilen_vampirler
    
    for oid in mevcut_oyuncular:
        if oid in secilen_vampirler:
            aktif_vampir_oyunu[kanal_id]["roller"][oid] = "Vampir"
        else:
            aktif_vampir_oyunu[kanal_id]["roller"][oid] = "Köylü"

    # DM Bildirimleri
    for oid in mevcut_oyuncular:
        uye = ctx.guild.get_member(oid)
        if not uye: continue
        try:
            if oid in secilen_vampirler:
                diger_vampir = ctx.guild.get_member([v for v in secilen_vampirler if v != oid][0])
                dm_embed = discord.Embed(title="🩸 VAMPİR KÖYLÜ - ROLÜN", color=0xE74C3C)
                dm_embed.description = f"**Rolün: VAMPIR** 🧛\n\nGörevin: Geceleyin köylülerden birini öldürmek ve gündüz yakalanmamak!\n\n🎲 Takım arkadaşın: **{diger_vampir.display_name}**"
                await uye.send(embed=dm_embed)
            else:
                dm_embed = discord.Embed(title="🛡️ VAMPİR KÖYLÜ - ROLÜN", color=0x2ECC71)
                dm_embed.description = f"**Rolün: KÖYLÜ** 🧑‍🌾\n\nGörevin: Gündüz yapılan oylamalarda vampirleri bulmak ve köyü kurtarmak! Kimseye güvenme..."
                await uye.send(embed=dm_embed)
        except discord.Forbidden:
            pass

    aktif_vampir_oyunu[kanal_id]["basladi"] = True
    baslangic_embed = discord.Embed(
        title="🌙 GECE ÇÖKTÜ!",
        description=f"**{len(mevcut_oyuncular)}** kişiyle oyun başladı! Herkese rolleri özel mesaj (DM) olarak gönderildi.\n\n🧛 **2 Vampir** görevini yapıyor...",
        color=0x2C3E50
    )
    baslangic_embed.set_footer(text="Vampirler hedeflerini seçiyorlar...")
    await mesaj.edit(embed=baslangic_embed, view=None)

    await asyncio.sleep(2)
    await vampir_gece_fazı(ctx, kanal_id, mesaj)


async def vampir_gece_fazı(ctx, kanal_id, ana_mesaj):
    if kanal_id not in aktif_vampir_oyunu:
        return
    veri = aktif_vampir_oyunu[kanal_id]
    if not veri["basladi"]:
        return

    hayatta_köylüler = [oid for oid in veri["hayatta"] if oid not in veri["vampirler"]]
    
    if not hayatta_köylüler:
        await vampir_oyunu_bitti(ctx, kanal_id, ana_mesaj, "vampir")
        return

    # Vampirlere DM ile Hedef Seçtirme
    for vid in veri["vampirler"]:
        if vid not in veri["hayatta"]: continue
        vampir_uye = ctx.guild.get_member(vid)
        if not vampir_uye: continue
        
        hedef_listesi = "\n".join([f"• **{ctx.guild.get_member(oid).display_name}** (ID: `{oid}`)" for oid in hayatta_köylüler])
        
        dm_embed = discord.Embed(
            title="🌙 GECE FAZI - HEDEF SEÇ",
            description=f"Öldürmek istediğin köylüyü seç. Takım arkadaşınla aynı kişiye zarar vermeyi deneyin!\n\n**Hedefler:**\n{hedef_listesi}",
            color=0x8E44AD
        )
        dm_embed.set_footer(text="NOT: Kanala sadece ID'yi yazarak oylama yapabilirsiniz.")
        
        try:
            await vampir_uye.send(embed=dm_embed)
        except:
            pass

    bekleme = await ana_mesaj.channel.send("⏳ Vampirler hedeflerini belirliyor... (30 saniye)")
    
    hedef_oylar = {}
    def check_vampir(m):
        if m.channel.id != kanal_id or m.author.bot: return False
        if m.author.id not in veri["vampirler"]: return False
        if m.author.id not in veri["hayatta"]: return False
        try:
            hedef_id = int(m.content.strip())
            return hedef_id in veri["hayatta"] and hedef_id not in veri["vampirler"]
        except ValueError:
            return False

    try:
        while True:
            msg = await bot.wait_for("message", timeout=30.0, check=check_vampir)
            hedef_oylar[msg.author.id] = int(msg.content.strip())
            if len(hedef_oylar) >= len([v for v in veri["vampirler"] if v in veri["hayatta"]]):
                break
    except asyncio.TimeoutError:
        pass

    await bekleme.delete()

    # Öldürme Mantığı
    oy_sayilari = {}
    for _, hedef in hedef_oylar.items():
        oy_sayilari[hedef] = oy_sayilari.get(hedef, 0) + 1
    
    if oy_sayilari:
        en_cok_oy = max(oy_sayilari.values())
        olasi_hedefler = [k for k, v in oy_sayilari.items() if v == en_cok_oy]
        kurban_id = random.choice(olasi_hedefler)
        
        veri["hayatta"].remove(kurban_id)
        kurban_uye = ctx.guild.get_member(kurban_id)
        
        gunduz_embed = discord.Embed(
            title="☀️ GÜNDÜZ DOĞDU!",
            description=f"Gece boyunca korkunç çığlıklar duyuldu...\n\n🩸 **{kurban_uye.mention}** vampirler tarafından acımasızca öldürüldü!",
            color=0xE67E22
        )
        gunduz_embed.set_footer(text="Köylüler toplandı! Vampirlerin kim olduğunu bulmak için oylama başlıyor...")
        await ana_mesaj.channel.send(embed=gunduz_embed)
        
        # Kurbanın DM'ine Ölüm Haberi
        try:
            olum_embed = discord.Embed(title="💀 ÖLDÜRÜLDÜN!", description="Vampirler seni gece vahşice yok etti! Artık oyun dışısın ama izlemeye devam edebilirsin.", color=0x000000)
            await kurban_uye.send(embed=olum_embed)
        except:
            pass

        await asyncio.sleep(3)
        await vampir_gunduz_oylamasi(ctx, kanal_id, ana_mesaj)
    else:
        kimse_embed = discord.Embed(title="🌅 Sabah Oldu!", description="Gece sessiz geçti... Vampirler kimseyi öldüremedi veya hedef seçmedi!", color=0xF1C40F)
        await ana_mesaj.channel.send(embed=kimse_embed)
        await asyncio.sleep(3)
        await vampir_gunduz_oylamasi(ctx, kanal_id, ana_mesaj)


async def vampir_gunduz_oylamasi(ctx, kanal_id, ana_mesaj):
    if kanal_id not in aktif_vampir_oyunu:
        return
    veri = aktif_vampir_oyunu[kanal_id]
    
    hayatta_oyuncular = [oid for oid in veri["hayatta"]]
    if len(hayatta_oyuncular) == 0:
        return

    # Oylama Listesi Oluşturma
    oylama_metni = "\n".join([f"**{ctx.guild.get_member(oid).display_name}** (ID: `{oid}`)" for oid in hayatta_oyuncular])
    
    oylama_embed = discord.Embed(
        title="⚖️ OYLAMA BAŞLADI!",
        description=f"Vampir olduğuna inandığın kişinin **ID'sini** yazıp gönder!\n\n**Adaylar:**\n{oylama_metni}",
        color=0x3498DB
    )
    oylama_embed.set_footer(text="45 saniyeniz var! En çok oyu alan kişinin kartı açılacak.")
    await ana_mesaj.channel.send(embed=oylama_embed)

    oylar = {}
    def check_oylama(m):
        if m.channel.id != kanal_id or m.author.bot: return False
        if m.author.id not in veri["hayatta"]: return False
        try:
            hedef_id = int(m.content.strip())
            return hedef_id in veri["hayatta"] and hedef_id != m.author.id
        except ValueError:
            return False

    try:
        while True:
            msg = await bot.wait_for("message", timeout=45.0, check=check_oylama)
            oylar[msg.author.id] = int(msg.content.strip())
    except asyncio.TimeoutError:
        pass

    # Oylama Sonuçları
    oy_sayilari = {}
    for _, hedef in oylar.items():
        oy_sayilari[hedef] = oy_sayilari.get(hedef, 0) + 1
    
    if not oy_sayilari:
        await ana_mesaj.channel.send("❌ Kimse oy vermedi! Oylama atlandı, gece tekrar başlıyor...")
        await asyncio.sleep(3)
        await vampir_gece_fazı(ctx, kanal_id, ana_mesaj)
        return

    en_cok_oy = max(oy_sayilari.values())
    birinci_adaylar = [k for k, v in oy_sayilari.items() if v == en_cok_oy]
    secilen_id = random.choice(birinci_adaylar)
    
    secilen_uye = ctx.guild.get_member(secilen_id)
    gercek_rol = veri["roller"].get(secilen_id, "Bilinmiyor")
    
    if gercek_rol == "Vampir":
        veri["hayatta"].remove(secilen_id)
        sonuc_embed = discord.Embed(
            title="🛡️ VAMPIR YAKALANDI!",
            description=f"**{secilen_uye.mention}** kişisine **{en_cok_oy}** oy verildi!\n\n🩸 Kartı açıldı: **VAMPİR**\nKöylüler zaferi bir adım daha yaklaştı!",
            color=0x2ECC71
        )
        await ana_mesaj.channel.send(embed=sonuc_embed)
    else:
        veri["hayatta"].remove(secilen_id)
        sonuc_embed = discord.Embed(
            title="😭 MASUM BİR KÖYLÜ ÖLDÜ!",
            description=f"**{secilen_uye.mention}** kişisine **{en_cok_oy}** oy verildi!\n\n🛡️ Kartı açıldı: **KÖYLÜ**\nVampirler kıkırdıyor...",
            color=0xE74C3C
        )
        await ana_mesaj.channel.send(embed=sonuc_embed)

    # Kazanma/Kaybetme Kontrolü
    kalan_vampir_sayisi = len([v for v in veri["vampirler"] if v in veri["hayatta"]])
    kalan_koylu_sayisi = len([o for o in veri["hayatta"] if o not in veri["vampirler"]])
    
    if kalan_vampir_sayisi == 0:
        await vampir_oyunu_bitti(ctx, kanal_id, ana_mesaj, "koylu")
    elif kalan_vampir_sayisi >= kalan_koylu_sayisi:
        await vampir_oyunu_bitti(ctx, kanal_id, ana_mesaj, "vampir")
    else:
        await asyncio.sleep(4)
        gece_msg = await ana_mesaj.channel.send("🌙 Tekrar gece çöktü... Herkes korkuyla evlerine kapandı!")
        await asyncio.sleep(3)
        await vampir_gece_fazı(ctx, kanal_id, ana_mesaj)


async def vampir_oyunu_bitti(ctx, kanal_id, ana_mesaj, kazanan):
    if kanal_id in aktif_vampir_oyunu:
        del aktif_vampir_oyunu[kanal_id]
    
    if kazanan == "koylu":
        bitis_embed = discord.Embed(
            title="🎉 KÖYLÜLER KAZANDI!",
            description="Tüm vampirler temizlendi! Köyde huzur yeniden sağlandı.",
            color=0x2ECC71
        )
        bitis_embed.set_footer(text="Tebrikler masum köylüler!")
    else:
        bitis_embed = discord.Embed(
            title="🩸 VAMPIRLER KAZANDI!",
            description="Vampirler köyün kontrolünü tamamen ele geçirdi! Karanlık çöktü...",
            color=0x8E44AD
        )
        bitis_embed.set_footer(text="Köylüler için çok geçti...")
        
    await ana_mesaj.channel.send(embed=bitis_embed)


@bot.command(name="vk")
async def vk(ctx):
    if ctx.channel.id in aktif_vampir_oyunu:
        return await ctx.send("❌ Bu kanalda zaten aktif bir Vampir Köylü oyunu devam ediyor!")
    
    await baslat_vampir_oyunu(ctx)


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
        if not uye or uye.bot: continue
        k = kayit_sayaci.get(uid, 0)
        d = deger_sayaci.get(uid, 0)
        liste.append(f"**{uye.display_name}** ➔ 📝 Kayıt: `{k}` | 💰 Değer: `{d}`")
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
        await ctx.send(f"🧮 **{soru}** = `{sonuc}`")
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
        aciklama += f"**{msg['yazar'].name}:** {msg['icerik'][:80]} `({sure}sn önce)`\n"
    await ctx.send(f"🗑️ **Son 5 Dakikada Silinen Mesajlar:**\n{aciklama}")


@bot.command()
async def dmall(ctx, *, mesaj: str):
    if ctx.author.id != ctx.guild.owner_id:
        return await ctx.send("❌ Bu komutu sadece sunucu sahibi kullanabilir!")
    islem = await ctx.send("⏳ DM'ler gönderiliyor, lütfen bekleyin...")
    basari = 0
    for uye in ctx.guild.members:
        if uye.bot or uye.id == ctx.author.id: continue
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
    secenekler = ["GOL ⚽", "KALECİ ÇIKTI 🧤", "AUT ❌"]
    sonuc = random.choice(secenekler)
    sozler = {
        "GOL ⚽": ["Muhteşem vuruş!", "Ağları salladı!", "Gol olmaz dediğin gol!"],
        "KALECİ ÇIKTI 🧤": ["Rüya gibi kurtarış!", "Kaleci şov yaptı!", "Neyi düşünüyordun?"],
        "AUT ❌": ["Çok az fark!", "Aut lazımdı bu maça!", "Direkten döndü, aut!"]
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
        if not hedef_rol: return await ctx.send("❌ Kayıt Yetkilisi rolü sunucuda bulunamadı!")
        await uye.add_roles(hedef_rol)
        return await ctx.send(f"⬆️ {uye.mention} adına **{hedef_rol.name}** rolü verildi!")
    if bulunulan_index >= len(rol_siniflama) - 1:
        return await ctx.send("❌ Zaten en üst rolde (League Commander)!")
    eski_rol = discord.utils.get(ctx.guild.roles, name=rol_siniflama[bulunulan_index])
    yeni_rol = discord.utils.get(ctx.guild.roles, name=rol_siniflama[bulunulan_index + 1])
    if not yeni_rol: return await ctx.send("❌ Bir üst rol sunucuda bulunamadı!")
    await uye.remove_roles(eski_rol)
    await uye.add_roles(yeni_rol)
    await ctx.send(f"⬆️ {uye.mention} rolü güncellendi: `{eski_rol.name}` -> `{yeni_rol.name}`")


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
    if not eski_rol or not yeni_rol: return await ctx.send("❌ Roller bulunamadı!")
    await uye.remove_roles(eski_rol)
    await uye.add_roles(yeni_rol)
    await ctx.send(f"⬇️ {uye.mention} rolü güncellendi: `{eski_rol.name}` -> `{yeni_rol.name}`")


# ====================== YARDIM SİSTEMİ ======================
class YardimDropDown(ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="🛡️ Moderasyon", description="Ban, Kick, Mute, Unmute, Nuke..."),
            discord.SelectOption(label="🎭 Rol Yönetimi", description="Rol Ver, Rol Al, Toplu Rol..."),
            discord.SelectOption(label="🎬 Roleplay", description="Kayıt, Değer, Antrenman komutları."),
            discord.SelectOption(label="📢 NOVA KAP", description="Transfer, Kiralama, Yenileme, FESH"),
            discord.SelectOption(label="🎉 Etkinlik", description="Etkinlik başlat, Çark, Bilgi, Eşleştir..."),
            discord.SelectOption(label="🌍 Genel & Eğlence", description="Ping, Avatar, Snipe, AFK..."),
            discord.SelectOption(label="⚡ Ekstra & Sahip", description="Up, Deup, Dmall, Hesapla, Pen...")
        ]
        super().__init__(placeholder="Kategori seçin...", options=options)

    async def callback(self, interaction: discord.Interaction):
        embed = discord.Embed(title=f"{self.values[0]} Komutları", color=0x2f3136)

        if self.values[0] == "🛡️ Moderasyon":
            embed.description = "**`.lock`** - Kanalı kilitler.\n**`.unlock`** - Kanal kilidini açar.\n**`.ban @üye [sebep]`** - Üyeyi yasaklar.\n**`.unban [ID]`** - Yasağı kaldırır.\n**`.kick @üye [sebep]`** - Üyeyi atar.\n**`.mute @üye [dakika]`** - Üyeyi susturur.\n**`.unmute @üye`** - Susturmayı kaldırır.\n**`.nuke`** - Kanalı sıfırlar."

        elif self.values[0] == "🎭 Rol Yönetimi":
            embed.description = "**`.rolver @üye [rol]`** - Role verir.\n**`.rolal @üye [rol]`** - Rolü alır.\n**`.toplurolver @üye/hepsi [roller]`** - Toplu rol verir.\n**`.toplurolal @üye/hepsi [roller]`** - Toplu rol alır."

        elif self.values[0] == "🎬 Roleplay":
            embed.description = "**`.k @üye [İsim | Değer | Takım]`** - Kayıt yapar.\n**`.dver @üye [miktar] [sebep]`** - Kişiye değer ekler.\n**`.dsil @üye [miktar] [sebep]`** - Kişiden değer siler.\n**`.antrenman`** - Antrenman yapar, 10/10 olunca +3M verir."

        elif self.values[0] == "📢 NOVA KAP":
            takim_listesi = "\n".join([f"• {t}" for t in TAKIM_ROLLERI.keys()])
            embed.description = f"`.kap` komutu ile panel açılır.\nTransfer ve Kiralama 2 aşamalıdır.\n\n📋 **Sadece şu takımların rolü verilebilir:**\n{takim_listesi}"

        elif self.values[0] == "🎉 Etkinlik":
            embed.description = (
                "**`.etkinlik`** - Etkinlik panelini açar, oyun seçilir ve duyuru yapılır.\n"
                "**`.cark [@üye]`** - Şans çarkını çevirir! Ödül veya ceza çıkabilir.\n"
                "**`.bilgi`** - Futbol sorusu sorar, ilk doğru cevaplayan kazanır!\n"
                "**`.eslestir`** - İki sunucu üyesini rastgele eşleştirir!\n"
                "**`.vk`** - **Vampir Köylü** oyununu başlatır. (Katılmak için butona bas)\n\n"
                "**Mevcut Etkinlik Oyunları:**\n" +
                "\n".join([f"{v['emoji']} **{k.split(' ', 1)[1]}**" for k, v in OYUNLAR.items()])
            )

        elif self.values[0] == "🌍 Genel & Eğlence":
            embed.description = "**`.ping`** - Bot gecikmesini gösterir.\n**`.avatar @üye`** - Profil fotoğrafını gösterir.\n**`.snipe`** - Silinen son mesajı gösterir.\n**`.snipeall`** - Son 5 dk silinen tüm mesajlar.\n**`.afk [sebep]`** - AFK moduna geçer.\n**`.ship @üye`** - Uyumu ölçer.\n**`.roll [seçenek1, seçenek2]`** - Şanslı seçim.\n**`.ara [isim]`** - Sunucuda isim arar."

        elif self.values[0] == "⚡ Ekstra & Sahip":
            embed.description = "**`.ytstat`** - Tüm yetkililerin kayıt/değer sayıları.\n**`.m`** - Mesaj sayınız.\n**`.hesapla [işlem]`** - Matematiksel işlem yapar.\n**`.owner`** - Sunucu sahibini gösterir.\n**`.dmall [mesaj]`** - Herkese DM atar (Sahip).\n**`.dm @üye [mesaj]`** - Kişiye DM atar.\n**`.pen`** - Penaltı atar (Gol/Kale/Aut).\n**`.up @üye`** - Rol yükseltir (Sahip/Özel).\n**`.deup @üye`** - Rol düşürür (Sahip)."

        await interaction.response.edit_message(embed=embed)


@bot.command()
async def yardım(ctx):
    view = ui.View()
    view.add_item(YardimDropDown())
    embed = discord.Embed(title="NOVA PLUS | YARDIM MENÜSÜ", description="Aşağıdaki menüden kategori seçin.", color=0x2f3136)
    await ctx.send(embed=embed, view=view)


# ====================== BOT ÇALIŞTIR ======================
if not TOKEN:
    print("❌ HATA: DISCORD_TOKEN bulunamadı! Lütfen Railway'de çevre değişkenleri (Variables) kısmına tokeninizi ekleyin.")
else:
    bot.run(TOKEN)

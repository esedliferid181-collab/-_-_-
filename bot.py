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
antrenman_sayac = {}


@bot.event
async def on_ready():
    print(f'--------------------------------------------------')
    print(f'🚀 NOVA PLUS SİSTEMİ %100 KAPASİTEYLE ÇALIŞIYOR!')
    print(f'🤖 Bot Kullanıcı Adı: {bot.user.name}')
    print(f'🆔 Bot ID: {bot.user.id}')
    print(f'📅 Tarih: {datetime.datetime.now().strftime("%d/%m/%Y")}')
    print(f'--------------------------------------------------')
    await bot.change_presence(activity=discord.Streaming(name=".yardım | NOVA PLUS", url="https://twitch.tv/NOVA"))


# --- OLAYLAR (EVENTLER) ---
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


# ====================== ROL YETKİSİ KONTROL FONKSİYONU ======================
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
        mevcut_isim = uye.display_name; parcalar = mevcut_isim.split("|")
        if len(parcalar) < 2: return await ctx.send(embed=hata_embed(f"❌ **{uye.display_name}** isminde '|' işareti yok!\nFormat: `Ad | 1M | Takım` olmalı."))
        eski_deger = parcalar[1].strip()
        yeni_isim, islem_detay = deger_isle(mevcut_isim, miktar, "ekle")
        if yeni_isim is None: return await ctx.send(embed=hata_embed(islem_detay))
        try: await uye.edit(nick=yeni_isim)
        except discord.Forbidden: return await ctx.send(embed=hata_embed("❌ İsim değiştirilemedi! Botun rolü bu üyenin rolünden yüksek olmalı."))
        except Exception as hata: return await ctx.send(embed=hata_embed(f"❌ Discord hatası: `{hata}`"))
        yeni_parcalar = yeni_isim.split("|"); yeni_deger = yeni_parcalar[1].strip() if len(yeni_parcalar) >= 2 else "?"
        await ctx.send(embed=basari_embed(f"**{uye.mention}** değeri güncellendi: {islem_detay}\n📝 Yeni isim: `{yeni_isim}`"))
        await log_deger_gonder(ctx.guild, ctx.author, uye, eski_deger, yeni_deger, "➕ Değer Eklendi", sebep)
    except Exception as e: await ctx.send(embed=hata_embed(f"Hata: `{e}`"))

@bot.command(name="dsil")
async def dsil(ctx, uye: discord.Member, miktar: str = None, *, sebep: str = "Belirtilmedi"):
    try:
        if not deger_yetkisi_var_mi(ctx.author):
            return await ctx.send(embed=hata_embed("Bu komutu kullanmak için **Değer Yetkilisi** rolüne sahip olmalısın!"))
        mevcut_isim = uye.display_name; parcalar = mevcut_isim.split("|")
        if len(parcalar) < 2: return await ctx.send(embed=hata_embed(f"❌ **{uye.display_name}** isminde '|' işareti yok!\nFormat: `Ad | 1M | Takım` olmalı."))
        eski_deger = parcalar[1].strip()
        if miktar is None:
            parcalar[1] = "0M"; yeni_isim = " | ".join(parcalar)
            try: await uye.edit(nick=yeni_isim)
            except discord.Forbidden: return await ctx.send(embed=hata_embed("❌ İsim değiştirilemedi! Botun rolü bu üyenin rolünden yüksek olmalı."))
            except Exception as hata: return await ctx.send(embed=hata_embed(f"❌ Discord hatası: `{hata}`"))
            await ctx.send(embed=basari_embed(f"**{uye.mention}** değeri sıfırlandı: `{eski_deger}` → `0M`\n📝 Yeni isim: `{yeni_isim}`"))
            await log_deger_gonder(ctx.guild, ctx.author, uye, eski_deger, "0M", "🔄 Değer Sıfırlandı", sebep); return
        yeni_isim, islem_detay = deger_isle(mevcut_isim, miktar, "çıkar")
        if yeni_isim is None: return await ctx.send(embed=hata_embed(islem_detay))
        try: await uye.edit(nick=yeni_isim)
        except discord.Forbidden: return await ctx.send(embed=hata_embed("❌ İsim değiştirilemedi! Botun rolü bu üyenin rolünden yüksek olmalı."))
        except Exception as hata: return await ctx.send(embed=hata_embed(f"❌ Discord hatası: `{hata}`"))
        yeni_parcalar = yeni_isim.split("|"); yeni_deger = yeni_parcalar[1].strip() if len(yeni_parcalar) >= 2 else "?"
        await ctx.send(embed=basari_embed(f"**{uye.mention}** değeri güncellendi: {islem_detay}\n📝 Yeni isim: `{yeni_isim}`"))
        await log_deger_gonder(ctx.guild, ctx.author, uye, eski_deger, yeni_deger, "➖ Değer Çıkarıldı", sebep)
    except Exception as e: await ctx.send(embed=hata_embed(f"Hata: `{e}`"))


# ====================== TAKIM BASKANI - DROPDOWN SELECT (DÜZELTİLDİ) ======================

class TakimSecDropdown(ui.Select):
    """Takım başkanı kaydı için dropdown menü — dinamik buton yerine Select kullanılıyor."""

    def __init__(self, hedef: discord.Member, yeni_nick: str, yapan_id: int):
        self.hedef = hedef
        self.yeni_nick = yeni_nick
        self.yapan_id = yapan_id

        options = [
            discord.SelectOption(label=takim_adi, value=takim_adi)
            for takim_adi in TAKIM_ROLLERI.keys()
        ]
        super().__init__(
            placeholder="Takımı seçin...",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        # Sadece komutu kullanan kişi seçim yapabilsin
        if interaction.user.id != self.yapan_id:
            return await interaction.response.send_message(
                embed=hata_embed("Bu seçimi yalnızca komutu kullanan kişi yapabilir!"),
                ephemeral=True
            )

        takim_adi = self.values[0]
        guild = interaction.guild
        hedef = self.hedef
        yeni_nick = self.yeni_nick

        kayitli_rol  = discord.utils.get(guild.roles, name=KAYITLI_ROL)
        kayitsiz_rol = discord.utils.get(guild.roles, name=KAYITSIZ_ROL)
        baskan_rol   = discord.utils.get(guild.roles, name=ROL_TAKIM_BASKANI)
        takim_rol    = guild.get_role(TAKIM_ROLLERI.get(takim_adi, 0))

        # Eksik rol kontrolü
        eksik = []
        if not takim_rol:   eksik.append(takim_adi)
        if not kayitli_rol: eksik.append(KAYITLI_ROL)
        if not baskan_rol:  eksik.append(ROL_TAKIM_BASKANI)
        if eksik:
            return await interaction.response.edit_message(
                embed=hata_embed(f"Sunucuda şu roller bulunamadı: `{'`, `'.join(eksik)}`"),
                view=None
            )

        # Kayıtsız rolü kaldır
        if kayitsiz_rol and kayitsiz_rol in hedef.roles:
            try:
                await hedef.remove_roles(kayitsiz_rol)
            except:
                pass

        # Rolleri ver
        try:
            await hedef.add_roles(baskan_rol, kayitli_rol, takim_rol)
        except Exception as e:
            return await interaction.response.edit_message(
                embed=hata_embed(f"Rol verilemedi: `{e}`"),
                view=None
            )

        # Nick güncelle
        nick_hata = None
        try:
            await hedef.edit(nick=yeni_nick)
        except discord.Forbidden:
            nick_hata = "⚠️ Nick değiştirilemedi: Botun rolü üyenin rolünden yukarıda olmalı."
        except discord.HTTPException as e:
            nick_hata = f"⚠️ Nick değiştirilemedi: {e}"

        renk = 0x2ECC71 if not nick_hata else 0xFFA500
        sonuc = discord.Embed(
            title="✅ Başkan Kaydı Tamamlandı",
            color=renk,
            timestamp=datetime.datetime.now()
        )
        sonuc.add_field(name="👤 Üye",         value=hedef.mention,    inline=True)
        sonuc.add_field(name="📝 Nick",         value=f"`{yeni_nick}`", inline=True)
        sonuc.add_field(
            name="🎭 Verilen Roller",
            value=f"`{ROL_TAKIM_BASKANI}`, `{KAYITLI_ROL}`, `{takim_adi}`",
            inline=False
        )
        if nick_hata:
            sonuc.add_field(name="❗ Uyarı", value=nick_hata, inline=False)
        sonuc.set_footer(text=f"Kaydeden: {interaction.user.display_name}")

        # View'i kapat (dropdown'ı devre dışı bırak)
        self.disabled = True
        await interaction.response.edit_message(embed=sonuc, view=None)


class TakimSecView(ui.View):
    """Takım başkanı seçim ekranı için View."""

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
                embed=hata_embed("Bu butonları yalnızca komutu kullanan kişi kullanabilir!"),
                ephemeral=True
            )
            return False
        return True

    async def kayit_yap(self, interaction: discord.Interaction, rol_adi: str):
        if self.kullanildi:
            return await interaction.response.send_message(
                embed=hata_embed("Bu kayıt zaten tamamlandı!"), ephemeral=True
            )
        
        self.kullanildi = True
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
        sonuc.add_field(name="👤 Üye",        value=hedef.mention,    inline=True)
        sonuc.add_field(name="📝 Nick",        value=f"`{yeni_nick}`", inline=True)
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
            return await interaction.response.send_message(
                embed=hata_embed("Bu kayıt zaten başlatıldı!"), ephemeral=True
            )
        self.kullanildi = True

        # Dropdown ile takım seçim ekranına geç
        takim_view = TakimSecView(
            hedef=self.hedef,
            yeni_nick=self.yeni_nick,
            yapan_id=self.yapan.id
        )
        embed = discord.Embed(
            title="👑 Takım Başkanı — Takım Seçin",
            description=(
                f"**{self.hedef.mention}** için hangi takımın başkanı olacağını "
                f"aşağıdaki menüden seçin.\n📝 Nick: `{self.yeni_nick}`"
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
    bos  = "⬜" * (10 - mevcut)
    
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
            "oid": self.oid.value,
            "oyuncu": self.oyuncu_ismi.value,
            "eski": self.eski_takim.value,
            "bonservis": self.bonservis.value,
            "yillik_maas": self.yillik_maas.value
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
            "oid": self.oid.value,
            "oyuncu": self.oyuncu_ismi.value,
            "eski": self.eski_takim.value,
            "kiralama_bedeli": self.kiralama_bedeli.value,
            "yillik_maas": self.yillik_maas.value
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


class FesihModal(ui.Modal, title="🚫 SÖZLEŞME FESİH"):
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
            
            member = await interaction.guild.fetch_member(int(self.eski_takim.value))
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
                await interaction.response.send_message("✅ Fesih işlemi KAP kanalına gönderildi!", ephemeral=True)
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

    @ui.button(label="Fesih", style=discord.ButtonStyle.danger, emoji="✂️")
    async def fesih(self, interaction: discord.Interaction, button):
        await interaction.response.send_modal(FesihModal())


@bot.command()
async def kap(ctx):
    takim_listesi = "\n".join([f"• {t}" for t in TAKIM_ROLLERI.keys()])
    embed = discord.Embed(
        title="📣 NOVA PLUS | KAP YÖNETİM PANELİ", 
        description=f"Aşağıdan istediğiniz işlemi seçin:\n*(Transfer ve Kiralama işlemleri 2 aşamalıdır)*\n\n📋 **Geçerli Takımlar:**\n{takim_listesi}", 
        color=0x2f3136
    )
    await ctx.send(embed=embed, view=KAPPaneli())


# ====================== YARDIM SİSTEMİ ======================
class YardimDropDown(ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="🛡️ Moderasyon", description="Ban, Kick, Mute, Unmute, Nuke..."),
            discord.SelectOption(label="🎭 Rol Yönetimi", description="Rol Ver, Rol Al, Toplu Rol..."),
            discord.SelectOption(label="🎬 Roleplay", description="Kayıt, Değer, Antrenman komutları."),
            discord.SelectOption(label="📢 NOVA KAP", description="Transfer, Kiralama, Yenileme, Fesih"),
            discord.SelectOption(label="🌍 Genel & Eğlence", description="Ping, Avatar, Snipe, AFK...")
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
            
        elif self.values[0] == "🌍 Genel & Eğlence":
            embed.description = "**`.ping`** - Bot gecikmesini gösterir.\n**`.avatar @üye`** - Profil fotoğrafını gösterir.\n**`.snipe`** - Silinen son mesajı gösterir.\n**`.afk [sebep]`** - AFK moduna geçer.\n**`.ship @üye`** - Uyumu ölçer.\n**`.roll [seçenek1, seçenek2]`** - Şanslı seçim.\n**`.ara [isim]`** - Sunucuda isim arar."
            
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

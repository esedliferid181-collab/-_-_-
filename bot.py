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
KAP_KANAL_ID = 1499044277316096010
KAYIT_KANAL_ID = 1499043903196631060
PREFIX = "."
intents = discord.Intents.all()
bot = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=None)

# ====================== ROLEPLAY AYARLARI ======================
KAYIT_YETKILI_ROL_ID = 1499363286615855144
DEGER_YETKILI_ROL_ID = 1499385795155595296
DEGER_LOG_KANAL_ID = 1499367585266012233
ROL_YETKILI_ROL_ID = 1499073372804481055
KAYITLI_ROL = "Kayıtlı Üye┇🎪"
KAYITSIZ_ROL = "Kayıtsız Üye┇🎪"
ROL_UYE = "Üye"
ROL_FUTBOLCU = "Futbolcu┇🧩"
ROL_TAKIM_BASKANI = "Takım Başkanı┇🪄"
LIG_COMMANDER_ROL_ADI = "Lig Commander"
SPIKER_ROL_ADI = "Spiker"

# Bot sahibi ID'leri (vk komutunu kullanabilecekler)
VK_YETKILI_IDS = [1135886736807964713]

# ====================== TAKIM ROL ID'LERİ ======================
TAKIM_ROLLERI = {
    "FC Barcelona": 1499363299538636840,
    "Real Madrid CF": 1499363299538636840,
    "ATLETİCO MADRİD": 1499363322594594956,
    "LİVERPOOL": 1499363306513764402,
    "MANCHESTER CİTY": 1499363301950226572,
    "MANCHESTER UNİTED": 1499363302998806528,
    "BAYERN MÜNİH": 1499363314977865848,
    "GALATASARAY": 1499363313451270205,
    "FENERBAHÇE": 1499363324205465620,
    "BEŞİKTAŞ": 1499363327615307896,
    "DORTMUND": 1499363318467399730,
    "PSG": 1499363326524915744,
    "JUVENTUS": 1499363309852299275,
    "AC MİLAN": 1499363312058499092,
    "İNTER": 1499363310934691890,
    "TRABZONSPOR": 1499363304085131435,
    "ARSENAL": 1499363305209204887,
    "TOTTENHAM": 1499363307679649802,
    "NEWCASTLE UNITED": 1499363308535418891,
    "BAYER LEVERKUSEN": 1499363319595667608,
    "FEYENOORD": 1499363325463756840,
}

# Veri dosyaları
KARIYER_DOSYA = "kariyer_verileri.json"

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
cark_gunluk = {}
son_cark_sonucu = {}
kariyer_verileri = {}

# ====================== KALICI VERİ (JSON) ======================
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
kariyer_verileri = kariyer_yukle()

# ====================== YARDIMCI FONKSİYONLAR ======================
def rol_bul_esnek(guild, rol_adi):
    for rol in guild.roles:
        if rol.name.lower() == rol_adi.lower():
            return rol
    return None

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

def spiker_mi(kisi):
    if kisi.guild_permissions.administrator:
        return True
    return any(rol.name.lower() == SPIKER_ROL_ADI.lower() for rol in kisi.roles)

def hata_embed(mesaj):
    return discord.Embed(title="❌ Hata", description=mesaj, color=0xff0000)

def basari_embed(mesaj):
    return discord.Embed(title="✅ Başarılı", description=mesaj, color=0x00ff00)

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

# ====================== KAYITSIZ HERKES KOMUTU ======================
@bot.command(name="kayıtsızherkes")
@commands.has_permissions(administrator=True)
async def kayitsiz_herkes(ctx):
    kayitsiz_rol = discord.utils.get(ctx.guild.roles, name=KAYITSIZ_ROL)
    if not kayitsiz_rol:
        return await ctx.send(embed=hata_embed(
            f"❌ **{KAYITSIZ_ROL}** adında bir rol bulunamadı!\nLütfen önce bu rolü oluşturun."
        ))

    owner_id = ctx.guild.owner_id

    hedefler = [
        m for m in ctx.guild.members
        if not m.bot and m.id != owner_id
    ]

    if not hedefler:
        return await ctx.send("❌ İşlem yapılacak uygun üye bulunamadı!")

    islem_msg = await ctx.send(
        f"⏳ **{len(hedefler)}** üye işleniyor, lütfen bekleyin...\n"
        f"⚠️ Botlar ve sunucu sahibi atlanacak."
    )

    basarili = 0
    hatali = 0
    atlanan = 0

    for uye in hedefler:
        try:
            bot_rol = ctx.guild.me.top_role
            uye_rolleri = [r for r in uye.roles if r != ctx.guild.default_role and r.position < bot_rol.position]

            if len(uye.roles) <= 1:
                if kayitsiz_rol not in uye.roles and kayitsiz_rol.position < bot_rol.position:
                    await uye.add_roles(kayitsiz_rol)
                    basarili += 1
                else:
                    atlanan += 1
                continue

            await uye.remove_roles(*uye_rolleri)

            if kayitsiz_rol.position < bot_rol.position:
                await uye.add_roles(kayitsiz_rol)
                basarili += 1
            else:
                hatali += 1

            await asyncio.sleep(0.3)
        except discord.Forbidden:
            hatali += 1
        except Exception:
            hatali += 1

    embed = discord.Embed(
        title="🔄 Toplu Kayıtsız Çekme Tamamlandı",
        color=0x2ECC71,
        timestamp=datetime.datetime.now()
    )
    embed.add_field(name="✅ Başarılı", value=f"**{basarili}** üye", inline=True)
    embed.add_field(name="❌ Hatalı", value=f"**{hatali}** üye", inline=True)
    embed.add_field(name="⏭️ Atlanan", value=f"**{atlanan}** üye", inline=True)
    embed.add_field(name="ℹ️ Bilgi", value="Botlar ve sunucu sahibi atlandı.", inline=False)
    embed.set_footer(text=f"İşlemi yapan: {ctx.author.display_name}")

    await islem_msg.edit(embed=embed)

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
                return await ctx.send(embed=hata_embed("❌ İsim değiştirilemedi!"))
            deger_sayaci[ctx.author.id] = deger_sayaci.get(ctx.author.id, 0) + 1
            await ctx.send(embed=basari_embed(f"**{uye.mention}** değeri sıfırlandı: {eski_deger} → 0M"))
            await log_deger_gonder(ctx.guild, ctx.author, uye, eski_deger, "0M", "🔄 Değer Sıfırlandı", sebep)
            return
        yeni_isim, islem_detay = deger_isle(mevcut_isim, miktar, "çıkar")
        if yeni_isim is None:
            return await ctx.send(embed=hata_embed(islem_detay))
        try:
            await uye.edit(nick=yeni_isim)
        except discord.Forbidden:
            return await ctx.send(embed=hata_embed("❌ İsim değiştirilemedi!"))
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
        f"🏟️ **{uye.display_name}** için **{takim_adi}** takımı kaydedildi!"
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
                    f"❌ **{takim_adi}** geçersiz bir takım adı!", ephemeral=True
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
                    f"❌ **{takim_adi}** geçersiz bir takım adı!", ephemeral=True
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
    ("Süper Lig tarihinde en fazla şampiyonluğu olan takım hangisidir?", "galatasaray", "🦁 Galatasaray!"),
    ("Fenerbahçe hangi yıl kuruludu?", "1907", "🟡🔵 1907!"),
    ("İlk Dünya Kupası hangi ülkede düzenlendi?", "uruguay", "🇺🇾 1930 Uruguay!"),
    ("UEFA Şampiyonlar Ligi tarihinin en pahalı transferi kimdir?", "neymar", "💰 Neymar 222M Euro!"),
    ("Messi kaç kez Ballon d'Or kazandı?", "8", "🌟 Rekor 8 kez!"),
    ("2022 Dünya Kupası'nı hangi takım kazandı?", "arjantin", "🇦🇷 Arjantin!"),
    ("Türkiye Milli Takımı hangi Dünya Kupası'nda 3. oldu?", "2002", "🇹🇷 2002 Güney Kore-Japonya!"),
    ("Hakan Şükür'ün Dünya Kupası tarihindeki en hızlı golü kaç saniyedeydi?", "11", "⚡ 11 saniye!"),
    ("Süper Lig'in ilk şampiyonu kimdir?", "fenerbahce", "🟡🔵 Fenerbahçe!"),
    ("Serie A'yı en fazla kazanan takım hangisidir?", "juventus", "⚫⚪ Juventus!"),
    ("La Liga'yı en fazla kazanan takım hangisidir?", "real madrid", "👑 Real Madrid!"),
    ("Bundesliga'yı en fazla kazanan takım hangisidir?", "bayern", "🔴 Bayern Münih!"),
    ("Camp Nou hangi takımın stadyumudur?", "barcelona", "🔵🔴 Barcelona!"),
    ("Bernabéu hangi takımın stadyumudur?", "real madrid", "⭐ Real Madrid!"),
    ("Galatasaray'ın stadyumunun adı nedir?", "rams park", "🦁 Rams Park!"),
    ("Fenerbahçe'nin stadyumunun adı nedir?", "sukru saracoglu", "🟡🔵 Şükrü Saracoğlu!"),
    ("Beşiktaş'ın stadyumunun adı nedir?", "besiktas park", "⚫⚪ Beşiktaş Park!"),
    ("VAR sistemi hangi yıl Dünya Kupası'nda ilk kullanıldı?", "2018", "📹 2018 Rusya!"),
    ("Tiki-taka oyun stilini dünyaya hangi takım tanıttı?", "barcelona", "🔵🔴 Barcelona!"),
    ("Fatih Terim'in lakabı nedir?", "imparator", "👑 İmparator!"),
    ("Pelé'nin gerçek adı nedir?", "edson arantes", "🇧🇷 Edson Arantes do Nascimento!"),
    ("Johan Cruyff'un 14 numaralı formasıyla özdeşleştiği kulüp hangisidir?", "ajax", "🇳🇱 Ajax!"),
    ("Kylian Mbappé'nin Dünya Kupası'nı kazandığı yaş kaçtır?", "19", "🌟 19 yaşında!"),
    ("EURO 2024'ü hangi takım kazandı?", "ispanya", "🇪🇸 İspanya!"),
    ("Benzema Ballon d'Or'u hangi yıl kazandı?", "2022", "🏆 2022!"),
    ("Mourinho'nun lakabı nedir?", "the special one", "😎 The Special One!"),
    ("Liverpool'un stadyumunun adı nedir?", "anfield", "🔴 Anfield!"),
    ("Borussia Dortmund'un stadyumunun adı nedir?", "signal iduna park", "🟡 Signal Iduna Park!"),
    ("Bayern Münih'in stadyumunun adı nedir?", "allianz arena", "🔴 Allianz Arena!"),
    ("San Siro hangi iki takımın stadyumudur?", "ac milan inter", "🔴⚫ AC Milan ve Inter!"),
    ("Zlatan Ibrahimovic'in en çok golü olan kulübü hangisidir?", "psg", "🔵🔴 PSG!"),
    ("Miroslav Klose Dünya Kupası tarihinin en golcüsüdür. Kaç gol attı?", "16", "🇩🇪 16 gol!"),
    ("Luka Modrić hangi ülkedendir?", "hirvatistan", "🇭🇷 Hırvatistan!"),
    ("Modrić Ballon d'Or'u hangi yıl kazandı?", "2018", "🏆 2018!"),
    ("Robert Lewandowski kaç kez Bundesliga golcüsü oldu?", "9", "🇵🇱 9 kez!"),
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
    await ctx.send(embed=embed, view=EtkinlikView())


@bot.command(name="cark")
async def cark(ctx, uye: discord.Member = None):
    hedef = uye or ctx.author
    bugun = datetime.date.today().isoformat()
    kullanici_cark = cark_gunluk.get(hedef.id, {"tarih": "", "sayi": 0})
    if kullanici_cark["tarih"] == bugun and kullanici_cark["sayi"] >= 5:
        return await ctx.send(embed=hata_embed(
            f"⏰ **{hedef.display_name}** günlük çark limitine ulaştı! (5/5)\nYarın tekrar dene!"
        ))
    if kullanici_cark["tarih"] != bugun:
        cark_gunluk[hedef.id] = {"tarih": bugun, "sayi": 0}
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
    embed.set_footer(text=f"Kalan hakkın: {kalan}/5")
    await animasyon.delete()
    await ctx.send(embed=embed)


@bot.command(name="bilgi")
async def bilgi(ctx):
    if ctx.channel.id in aktif_bilgi_oyunu:
        return await ctx.send("❌ Bu kanalda zaten aktif bir bilgi oyunu var!")
    if len(kullanilan_bilgi_sorulari) >= len(BILGI_SORULARI):
        kullanilan_bilgi_sorulari.clear()
    kullanilmayanlar = [i for i, _ in enumerate(BILGI_SORULARI) if i not in kullanilan_bilgi_sorulari]
    if not kullanilmayanlar:
        kullanilan_bilgi_sorulari.clear()
        kullanilmayanlar = list(range(len(BILGI_SORULARI)))
    secilen_index = random.choice(kullanilmayanlar)
    kullanilan_bilgi_sorulari.append(secilen_index)
    soru, cevap, aciklama = BILGI_SORULARI[secilen_index]
    aktif_bilgi_oyunu[ctx.channel.id] = {"cevap": cevap, "aciklama": aciklama}
    embed = discord.Embed(
        title="⚡ HIZLI BİLGİ SORUSU!",
        description=f"**{soru}**\n\n⏰ 20 saniye içinde cevapla!",
        color=0xF1C40F
    )
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
        await ctx.send(embed=discord.Embed(
            title="⏰ SÜRE DOLDU!",
            description=f"Kimse doğru cevaplayamadı!\n\n💡 **Doğru Cevap:** {aciklama}",
            color=0xE74C3C
        ))


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
    embed = discord.Embed(title="🔀 RASTGELE EŞLEŞTİRME", color=renk)
    embed.add_field(name="👤 Oyuncu 1", value=ctx.author.mention, inline=True)
    embed.add_field(name=emoji, value=f"**%{uyum}**", inline=True)
    embed.add_field(name="👤 Oyuncu 2", value=eslesen.mention, inline=True)
    embed.add_field(name="💬 Yorum", value=yorum, inline=False)
    await ctx.send(embed=embed)

# ====================== PENALTI ANTRENMAN KOMUTU ======================
PENALTI_KANAL_ID = 1499363897553977394

@bot.command(name="pen")
async def pen(ctx):
    if ctx.channel.id != PENALTI_KANAL_ID:
        return await ctx.send(embed=hata_embed("❌ Bu komut sadece **Penaltı Antrenman** kanalında kullanılabilir!"))

    son = son_cark_sonucu.get(f"pen_{ctx.author.id}", -1)
    kullanilabilir = [i for i in range(3) if i != son]
    secim_index = random.choice(kullanilabilir)
    son_cark_sonucu[f"pen_{ctx.author.id}"] = secim_index

    sonuclar = ["GOL ⚽", "KALECİ ÇIKTI 🧤", "AUT ❌"]
    sozler = {
        "GOL ⚽": ["Muhteşem vuruş!", "Ağları salladı!", "Köşeye yerleştirdi!"],
        "KALECİ ÇIKTI 🧤": ["Rüya gibi kurtarış!", "Kaleci şov yaptı!", "Demir gibi eller!"],
        "AUT ❌": ["Çok az fark!", "Direkten döndü!", "Ah be, yanından geçti!"]
    }

    sonuc = sonuclar[secim_index]
    soz = random.choice(sozler[sonuc])
    renk = 0x2ECC71 if "GOL" in sonuc else (0xFFA500 if "KALECİ" in sonuc else 0xE74C3C)

    embed = discord.Embed(title=sonuc, description=f"*{soz}*", color=renk)
    embed.set_footer(text=f"Penaltı atan: {ctx.author.name}")
    await ctx.send(embed=embed)

# ====================== HİKAYE KOMUTU ======================
hikaye_bekleyen = {}

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
    await ctx.send(embed=embed)

    def kontrol(m):
        return m.channel.id == ctx.channel.id and m.author.id == ctx.author.id and not m.author.bot

    try:
        mesaj = await bot.wait_for("message", timeout=60.0, check=kontrol)
        cumle = mesaj.content.strip()
        del hikaye_bekleyen[ctx.channel.id]
        yukleniyor = await ctx.send("✍️ Hikayeniz yazılıyor, lütfen bekleyin...")
        hikayeler = [
            f"""
🌙 **Karanlık Saha**

Sahalar boştu. Seyirciler çoktan evlerine dönmüştü. Yalnızca fenerler yanıyordu.

*"{cumle}"*

O gece kimse onu görmüyordu. Ama o, kendini izliyordu. İçindeki ses her atışta büyüdü, her koşuda güçlendi.

Sabah olduğunda saha hâlâ boştu. Ama o artık aynı kişi değildi.
""",
            f"""
⚽ **Son Dakika**

Maçın 90. dakikasıydı. Skor 0-0.

*"{cumle}"*

Top ağlara girdiğinde stadyum çatladı. Gözlerinden yaşlar aktı — sevinçten mi, yorgunluktan mı, bilinmez.

O gece herkes onun adını haykırdı.
""",
            f"""
🏆 **Efsanenin Doğuşu**

Küçük bir kasabada, küçük bir çocuk vardı.

*"{cumle}"*

Yıllar geçti. Kasaba büyümedi, ama çocuk büyüdü.

Bir gün o küçük kasabadan büyük bir şehre adım attı. Ve o, gerçekten hazırdı.
""",
        ]
        secilen_hikaye = random.choice(hikayeler)
        embed = discord.Embed(
            title="📖 Hikayen Hazır!",
            description=secilen_hikaye.strip(),
            color=0x9B59B6
        )
        embed.set_footer(text=f"Cümle: \"{cumle[:50]}{'...' if len(cumle)>50 else ''}\" | {ctx.author.display_name} için yazıldı")
        await yukleniyor.delete()
        await ctx.send(embed=embed)
    except asyncio.TimeoutError:
        if ctx.channel.id in hikaye_bekleyen:
            del hikaye_bekleyen[ctx.channel.id]
        await ctx.send("⏰ Süre doldu!", delete_after=10)


# ====================== VAMPİR KÖYLÜ ======================
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
            return await interaction.response.send_message("❌ Oyun zaman aşımına uğradı!", ephemeral=True)
        oyuncular = aktif_vampir_oyunu[self.kanal_id]["oyuncular"]
        if interaction.user.id in oyuncular:
            return await interaction.response.send_message("❌ Zaten oyuna katıldın!", ephemeral=True)
        if len(oyuncular) >= 20:
            return await interaction.response.send_message("❌ Oyun dolu!", ephemeral=True)
        oyuncular.append(interaction.user.id)
        await interaction.response.send_message("✅ Oyuna katıldın! Rolün DM ile gelecek.", ephemeral=True)
        guncel_sayi = len(oyuncular)
        katilan_metni = vampir_katilan_listesi_yap(interaction.guild, oyuncular)
        embed = discord.Embed(title="🧛 VAMPİR KÖYLÜ — KATILIM", color=0x8E44AD)
        embed.add_field(name="👥 Katılımcı", value=f"**{guncel_sayi}/20**", inline=True)
        embed.add_field(name="📋 Katılanlar", value=katilan_metni, inline=False)
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
        await interaction.response.edit_message(
            embed=discord.Embed(title="🩸 Hedef Seçildi!", description=f"**{self.label}** hedef alındı!", color=0x8E44AD),
            view=self.parent_view
        )
        self.parent_view.stop()


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
        await interaction.response.edit_message(
            embed=discord.Embed(title="💉 Koruma Yapıldı!", description=f"**{self.label}** korundu!", color=0x2ECC71),
            view=self.parent_view
        )
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
            return await interaction.response.send_message("❌ Oyun dışısın!", ephemeral=True)
        if interaction.user.id == self.hedef_id:
            return await interaction.response.send_message("❌ Kendine oy veremezsin!", ephemeral=True)
        if interaction.user.id in self.parent_view.oy_verenler:
            return await interaction.response.send_message("❌ Zaten oy kullandın!", ephemeral=True)
        self.parent_view.oy_verenler.add(interaction.user.id)
        self.parent_view.oylar[self.hedef_id] = self.parent_view.oylar.get(self.hedef_id, 0) + 1
        hedef_uye = interaction.guild.get_member(self.hedef_id)
        await interaction.response.send_message(f"✅ **{hedef_uye.display_name}** için oy kullandın!", ephemeral=True)


async def baslat_vampir_oyunu(ctx):
    kanal_id = ctx.channel.id
    aktif_vampir_oyunu[kanal_id] = {
        "oyuncular": [ctx.author.id], "roller": {}, "hayatta": [],
        "vampirler": [], "doktor": None, "doktor_koruma": None,
        "basladi": False, "gece_secimler": {}
    }
    embed = discord.Embed(title="🧛 VAMPİR KÖYLÜ — KATILIM", color=0x8E44AD)
    embed.description = "Köy karanlığa gömüldü! Aşağıdaki butona basarak katıl!"
    embed.add_field(name="👥 Katılımcı", value="1/20", inline=True)
    embed.add_field(name="📋 Katılanlar", value=f"🧛 {ctx.author.display_name}", inline=False)
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
        await ana_mesaj.edit(embed=discord.Embed(title="❌ İptal", description="Minimum 4 kişi gerekli!", color=0xFF0000), view=None)
        return

    aktif_vampir_oyunu[kanal_id]["hayatta"] = mevcut_oyuncular.copy()
    random.shuffle(mevcut_oyuncular)
    vampir_sayisi = 1 if len(mevcut_oyuncular) <= 6 else 2
    secilen_vampirler = mevcut_oyuncular[:vampir_sayisi]
    aktif_vampir_oyunu[kanal_id]["vampirler"] = secilen_vampirler
    kalan_koyluler = [p for p in mevcut_oyuncular if p not in secilen_vampirler]
    doktor = random.choice(kalan_koyluler) if len(kalan_koyluler) >= 2 else None
    aktif_vampir_oyunu[kanal_id]["doktor"] = doktor

    for oid in mevcut_oyuncular:
        if oid in secilen_vampirler:
            aktif_vampir_oyunu[kanal_id]["roller"][oid] = "Vampir"
        elif oid == doktor:
            aktif_vampir_oyunu[kanal_id]["roller"][oid] = "Doktor"
        else:
            aktif_vampir_oyunu[kanal_id]["roller"][oid] = "Köylü"

    for oid in mevcut_oyuncular:
        uye = ctx.guild.get_member(oid)
        if not uye:
            continue
        try:
            if oid in secilen_vampirler:
                diger = [ctx.guild.get_member(v) for v in secilen_vampirler if v != oid]
                diger_isimler = ", ".join([d.display_name for d in diger if d]) or "Yok"
                dm = discord.Embed(title="🩸 ROLÜN: VAMPİR", color=0xE74C3C)
                dm.description = f"**Vampir takım arkadaşların:** `{diger_isimler}`\nGece köylülerden birini seç!"
                await uye.send(embed=dm)
            elif oid == doktor:
                dm = discord.Embed(title="💉 ROLÜN: DOKTOR", color=0x2ECC71)
                dm.description = "Her gece bir kişiyi vampirlerden koru!"
                await uye.send(embed=dm)
            else:
                dm = discord.Embed(title="🛡️ ROLÜN: KÖYLÜ", color=0x3498DB)
                dm.description = "Vampiri bul, köyü kurtar!"
                await uye.send(embed=dm)
        except discord.Forbidden:
            pass

    aktif_vampir_oyunu[kanal_id]["basladi"] = True
    baslangic = discord.Embed(title="🌙 OYUN BAŞLADI!", color=0x2C3E50)
    baslangic.description = f"**{len(mevcut_oyuncular)}** kişi katıldı! Roller DM olarak gönderildi.\n🧛 **{vampir_sayisi} Vampir** | 💉 **Doktor** | 🧑‍🌾 **Köylüler**"
    await ana_mesaj.edit(embed=baslangic, view=None)
    await asyncio.sleep(2)
    await vampir_gece_fazi(ctx, kanal_id, ana_mesaj)


async def vampir_gece_fazi(ctx, kanal_id, ana_mesaj):
    if kanal_id not in aktif_vampir_oyunu:
        return
    veri = aktif_vampir_oyunu[kanal_id]
    hayatta_koyluler = [oid for oid in veri["hayatta"] if oid not in veri["vampirler"]]
    if not hayatta_koyluler:
        await vampir_oyunu_bitti(ctx, kanal_id, ana_mesaj, "vampir")
        return

    gece_embed = discord.Embed(title="🌙 GECE FAZI", description="Vampirler ve Doktor seçimlerini yapıyor... (25 saniye)", color=0x2C3E50)
    await ctx.channel.send(embed=gece_embed)
    veri["gece_secimler"] = {}
    veri["doktor_koruma"] = None

    for vid in veri["vampirler"]:
        if vid not in veri["hayatta"]:
            continue
        vampir_uye = ctx.guild.get_member(vid)
        if not vampir_uye:
            continue
        hedef_listesi = [(oid, ctx.guild.get_member(oid).display_name) for oid in hayatta_koyluler if ctx.guild.get_member(oid)]
        dm = discord.Embed(title="🌙 Hedef Seç!", color=0x8E44AD)
        v_view = VampirGeceSecimView(kanal_id, hedef_listesi, vid)
        try:
            await vampir_uye.send(embed=dm, view=v_view)
        except discord.Forbidden:
            pass

    doktor_id = veri.get("doktor")
    if doktor_id and doktor_id in veri["hayatta"]:
        doktor_uye = ctx.guild.get_member(doktor_id)
        if doktor_uye:
            koruma_listesi = [(oid, ctx.guild.get_member(oid).display_name) for oid in veri["hayatta"] if ctx.guild.get_member(oid)]
            dm = discord.Embed(title="💉 Kimi Koruyacaksın?", color=0x2ECC71)
            d_view = DoktorKoruyuView(kanal_id, koruma_listesi, doktor_id)
            try:
                await doktor_uye.send(embed=dm, view=d_view)
            except discord.Forbidden:
                pass

    await asyncio.sleep(25)

    oy_sayilari = {}
    for _, hedef in veri.get("gece_secimler", {}).items():
        oy_sayilari[hedef] = oy_sayilari.get(hedef, 0) + 1
    korunan = veri.get("doktor_koruma")

    if oy_sayilari:
        en_cok = max(oy_sayilari.values())
        olasi = [k for k, v in oy_sayilari.items() if v == en_cok]
        kurban_id = random.choice(olasi)
        if kurban_id == korunan:
            korunan_uye = ctx.guild.get_member(kurban_id)
            await ctx.channel.send(embed=discord.Embed(
                title="💉 DOKTOR KURTARDI!",
                description=f"**{korunan_uye.mention}** vampirlerden kurtarıldı!",
                color=0x2ECC71
            ))
        else:
            if kurban_id in veri["hayatta"]:
                veri["hayatta"].remove(kurban_id)
            kurban_uye = ctx.guild.get_member(kurban_id)
            if kurban_uye:
                await ctx.channel.send(embed=discord.Embed(
                    title="☀️ GÜNDÜZ DOĞDU!",
                    description=f"🩸 **{kurban_uye.mention}** vampirler tarafından öldürüldü!",
                    color=0xE67E22
                ))
    else:
        await ctx.channel.send(embed=discord.Embed(title="🌅 Sessiz Bir Gece...", description="Vampirler bu gece kimseyi öldürmedi!", color=0xF1C40F))

    await asyncio.sleep(2)
    kalan_vampir = len([v for v in veri["vampirler"] if v in veri["hayatta"]])
    kalan_koylu = len([o for o in veri["hayatta"] if o not in veri["vampirler"]])
    if kalan_vampir == 0:
        await vampir_oyunu_bitti(ctx, kanal_id, ana_mesaj, "koylu")
    elif kalan_vampir >= kalan_koylu:
        await vampir_oyunu_bitti(ctx, kanal_id, ana_mesaj, "vampir")
    else:
        await vampir_gunduz_oylamasi(ctx, kanal_id, ana_mesaj)


async def vampir_gunduz_oylamasi(ctx, kanal_id, ana_mesaj):
    if kanal_id not in aktif_vampir_oyunu:
        return
    veri = aktif_vampir_oyunu[kanal_id]
    hayatta_oyuncular = veri["hayatta"]
    oylama_embed = discord.Embed(title="⚖️ GÜNDÜZ OYLAMASI!", description="Vampir olduğunu düşündüğün kişiye oy ver! (20 saniye)", color=0x3498DB)
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
        await ctx.channel.send(embed=discord.Embed(title="🤷 Kimse Oy Vermedi!", color=0xF1C40F))
        await asyncio.sleep(2)
        await vampir_gece_fazi(ctx, kanal_id, ana_mesaj)
        return

    en_cok = max(oy_sayilari.values())
    birinci = [k for k, v in oy_sayilari.items() if v == en_cok]
    secilen_id = random.choice(birinci)
    secilen_uye = ctx.guild.get_member(secilen_id)
    gercek_rol = veri["roller"].get(secilen_id, "Bilinmiyor")

    if gercek_rol == "Vampir":
        veri["hayatta"].remove(secilen_id)
        sonuc = discord.Embed(title="🛡️ VAMPİR YAKALANDI!", description=f"**{secilen_uye.mention}** → **VAMPİR** 🧛", color=0x2ECC71)
    else:
        veri["hayatta"].remove(secilen_id)
        emoji = "💉" if gercek_rol == "Doktor" else "🧑‍🌾"
        sonuc = discord.Embed(title="😭 YANLIŞ KİŞİ İDAM EDİLDİ!", description=f"**{secilen_uye.mention}** → **{gercek_rol}** {emoji}", color=0xE74C3C)
        if gercek_rol == "Doktor":
            veri["doktor"] = None

    await ctx.channel.send(embed=sonuc)
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
                e = "🧛" if rol == "Vampir" else ("💉" if rol == "Doktor" else "🧑‍🌾")
                rol_listesi.append(f"{e} **{uye.display_name}** — {rol}")
        del aktif_vampir_oyunu[kanal_id]
    else:
        rol_listesi = []

    if kazanan == "koylu":
        embed = discord.Embed(title="🎉 KÖYLÜLER KAZANDI!", description="Tüm vampirler temizlendi! ☀️", color=0x2ECC71)
    else:
        embed = discord.Embed(title="🩸 VAMPİRLER KAZANDI!", description="Karanlık çöktü... 🌙", color=0x8E44AD)

    if rol_listesi:
        embed.add_field(name="📋 Tüm Roller", value="\n".join(rol_listesi), inline=False)
    await ctx.channel.send(embed=embed)


@bot.command(name="vk")
async def vk(ctx):
    yetkili = ctx.author.id == ctx.guild.owner_id or ctx.author.id in VK_YETKILI_IDS
    if not yetkili:
        return await ctx.send(embed=hata_embed("Bu komutu sadece **sunucu sahibi** veya yetkili kişiler kullanabilir!"))
    if ctx.channel.id in aktif_vampir_oyunu:
        return await ctx.send("❌ Bu kanalda zaten aktif bir oyun var!")
    await baslat_vampir_oyunu(ctx)


# ====================== GÜNLÜK MESAJ ======================
@bot.command(name="günlükmesaj")
async def gunluk_mesaj(ctx):
    bugun = datetime.date.today().isoformat()
    bugunun_verileri = gunluk_mesaj_sayaci.get(bugun, {})
    if not bugunun_verileri:
        return await ctx.send("❌ Bugün mesaj istatistiği yok!")
    sirali = sorted(bugunun_verileri.items(), key=lambda x: x[1], reverse=True)
    liste = []
    toplam = 0
    sira = 1
    for uid, sayi in sirali:
        uye = ctx.guild.get_member(uid)
        if not uye or uye.bot:
            continue
        m = "🥇" if sira == 1 else ("🥈" if sira == 2 else ("🥉" if sira == 3 else f"**#{sira}**"))
        liste.append(f"{m} {uye.display_name} — **{sayi}** mesaj")
        toplam += sayi
        sira += 1
    if not liste:
        return await ctx.send("❌ Bugün mesaj atan üye bulunamadı.")
    embed = discord.Embed(title="📊 Günlük Mesaj İstatistikleri", description="\n".join(liste[:25]), color=0x5865F2)
    embed.set_footer(text=f"📅 {bugun} | 💬 Toplam: {toplam} mesaj")
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
    embed = discord.Embed(title="📊 Yetkili İstatistikleri", description="\n".join(liste), color=0x5865F2)
    await ctx.send(embed=embed)


@bot.command(name="m", aliases=["mesaj_say"])
async def mesaj_say(ctx):
    sayi = mesaj_sayaci.get(ctx.author.id, 0)
    await ctx.send(f"📝 {ctx.author.mention} toplam **{sayi}** mesaj yazdı!")


@bot.command()
async def hesapla(ctx, *, soru: str):
    izin_verilen = set("0123456789+-*/.() ")
    if not all(c in izin_verilen for c in soru):
        return await ctx.send("❌ Sadece matematiksel işaretler kullanabilirsin!")
    try:
        sonuc = eval(soru)
        await ctx.send(f"🧮 **{soru}** = {sonuc}")
    except:
        await ctx.send("❌ Geçersiz işlem!")


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
    islem = await ctx.send("⏳ DM'ler gönderiliyor...")
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
    await islem.edit(content=f"✅ **{basari}** kişiye DM gönderildi.")


@bot.command()
async def dm(ctx, uye: discord.Member, *, mesaj: str):
    try:
        await uye.send(f"📬 **{ctx.author.display_name}** size bir mesaj gönderdi:\n\n{mesaj}")
        await ctx.send(f"✅ Mesajınız {uye.mention} kişisine gönderildi.")
    except:
        await ctx.send(f"❌ {uye.mention} kişisine mesaj gönderilemedi!")


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
            return await ctx.send("❌ Kayıt Yetkilisi rolü bulunamadı!")
        await uye.add_roles(hedef_rol)
        return await ctx.send(f"⬆️ {uye.mention} → **{hedef_rol.name}**")
    if bulunulan_index >= len(rol_siniflama) - 1:
        return await ctx.send("❌ Zaten en üst rolde!")
    eski_rol = discord.utils.get(ctx.guild.roles, name=rol_siniflama[bulunulan_index])
    yeni_rol = discord.utils.get(ctx.guild.roles, name=rol_siniflama[bulunulan_index + 1])
    if not yeni_rol:
        return await ctx.send("❌ Üst rol bulunamadı!")
    await uye.remove_roles(eski_rol)
    await uye.add_roles(yeni_rol)
    await ctx.send(f"⬆️ {uye.mention}: {eski_rol.name} → {yeni_rol.name}")


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
        return await ctx.send("❌ Zaten en alt rolde!")
    eski_rol = discord.utils.get(ctx.guild.roles, name=rol_siniflama[bulunulan_index])
    yeni_rol = discord.utils.get(ctx.guild.roles, name=rol_siniflama[bulunulan_index - 1])
    if not eski_rol or not yeni_rol:
        return await ctx.send("❌ Roller bulunamadı!")
    await uye.remove_roles(eski_rol)
    await uye.add_roles(yeni_rol)
    await ctx.send(f"⬇️ {uye.mention}: {eski_rol.name} → {yeni_rol.name}")


# ====================== YARDIM SİSTEMİ ======================
class YardimDropDown(ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="🛡️ Moderasyon", description="Ban, Kick, Mute, Unmute, Nuke..."),
            discord.SelectOption(label="🎭 Rol Yönetimi", description="Rol Ver, Rol Al, Toplu Rol..."),
            discord.SelectOption(label="🎬 Roleplay", description="Kayıt, Değer komutları."),
            discord.SelectOption(label="⚽ Kariyer Sistemi", description="Kariyer, Gol, Asist komutları."),
            discord.SelectOption(label="📢 NOVA KAP", description="Transfer, Kiralama, Yenileme, FESH"),
            discord.SelectOption(label="🎉 Etkinlik", description="Etkinlik, Çark, Bilgi, Eşleştir, VK..."),
            discord.SelectOption(label="🌍 Genel & Eğlence", description="Ping, Avatar, Snipe, AFK, Hikaye..."),
            discord.SelectOption(label="⚡ Ekstra & Sahip", description="Up, Deup, Dmall, Hesapla, KayıtsızHerkes..."),
        ]
        super().__init__(placeholder="Kategori seçin...", options=options)

    async def callback(self, interaction: discord.Interaction):
        embed = discord.Embed(title=f"{self.values[0]} Komutları", color=0x2f3136)
        if self.values[0] == "🛡️ Moderasyon":
            embed.description = (
                "**.lock** - Kanalı kilitler.\n"
                "**.unlock** - Kanal kilidini açar.\n"
                "**.ban @üye [sebep]** - Yasaklar.\n"
                "**.unban [ID]** - Yasağı kaldırır.\n"
                "**.kick @üye [sebep]** - Atar.\n"
                "**.mute @üye [dakika]** - Susturur.\n"
                "**.unmute @üye** - Susturmayı kaldırır.\n"
                "**.nuke** - Kanalı sıfırlar."
            )
        elif self.values[0] == "🎭 Rol Yönetimi":
            embed.description = (
                "**.rolver @üye [rol]** - Rol verir.\n"
                "**.rolal @üye [rol]** - Rol alır.\n"
                "**.toplurolver @üye/hepsi [roller]** - Toplu rol verir.\n"
                "**.toplurolal @üye/hepsi [roller]** - Toplu rol alır."
            )
        elif self.values[0] == "🎬 Roleplay":
            embed.description = (
                "**.k @üye [İsim | Değer | Takım]** - Kayıt yapar.\n"
                "**.dver @üye [miktar] [sebep]** - Değer ekler.\n"
                "**.dsil @üye [miktar] [sebep]** - Değer siler."
            )
        elif self.values[0] == "⚽ Kariyer Sistemi":
            embed.description = (
                "**.kariyer [@üye]** - Kariyer istatistikleri.\n"
                "**.golekle @üye [miktar]** - Gol ekler. **(League Commander)**\n"
                "**.asistekle @üye [miktar]** - Asist ekler. **(League Commander)**\n"
                "**.takimekle @üye [takım]** - Kariyer geçmişine takım ekler."
            )
        elif self.values[0] == "📢 NOVA KAP":
            takim_listesi = "\n".join([f"• {t}" for t in TAKIM_ROLLERI.keys()])
            embed.description = (
                "**.kap** ile panel açılır.\n"
                f"📋 **Geçerli Takımlar:**\n{takim_listesi}"
            )
        elif self.values[0] == "🎉 Etkinlik":
            embed.description = (
                "**.etkinlik** - Etkinlik paneli.\n"
                "**.cark [@üye]** - Şans çarkı! (Günlük 5 hak)\n"
                "**.bilgi** - Futbol sorusu.\n"
                "**.eslestir** - Rastgele eşleştirme.\n"
                "**.vk** - Vampir Köylü oyunu."
            )
        elif self.values[0] == "🌍 Genel & Eğlence":
            embed.description = (
                "**.ping** - Gecikme.\n"
                "**.avatar [@üye]** - Profil fotoğrafı.\n"
                "**.snipe** - Son silinen mesaj.\n"
                "**.snipeall** - Son 5dk silinen mesajlar.\n"
                "**.afk [sebep]** - AFK modu.\n"
                "**.ship @üye** - Uyum ölçer.\n"
                "**.roll [seçenek1, seçenek2]** - Şanslı seçim.\n"
                "**.ara [isim]** - İsim arar.\n"
                "**.hikaye** - Hikaye oluşturur."
            )
        elif self.values[0] == "⚡ Ekstra & Sahip":
            embed.description = (
                "**.ytstat** - Yetkili istatistikleri.\n"
                "**.m** - Mesaj sayısı.\n"
                "**.günlükmesaj** - Günlük sıralama.\n"
                "**.hesapla [işlem]** - Matematik.\n"
                "**.owner** - Sunucu sahibi.\n"
                "**.dmall [mesaj]** - Herkese DM (Sahip).\n"
                "**.dm @üye [mesaj]** - DM gönder.\n"
                "**.pen** - Penaltı atar.\n"
                "**.up @üye** - Rol yükselt.\n"
                "**.deup @üye** - Rol düşür.\n"
                "**.kayıtsızherkes** - Herkesi kayıtsız çeker, tüm rolleri siler. **(Admin)**"
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
    print("❌ HATA: DISCORD_TOKEN bulunamadı!")
else:
    bot.run(TOKEN)

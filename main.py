import math
import os
import re
import sqlite3
import time
from pathlib import Path

import aiohttp
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
_data_dir = Path("/data") if Path("/data").exists() else Path(".")
DB_PATH = _data_dir / "bot.db"

print("DB PATH:", DB_PATH)

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix=".", intents=intents, help_command=None)

# ———————————————––
# Hardcoded text — this is the client's exact wording, baked in on purpose.
# No .template_* commands in this build: they didn't ask for self-editable
# text, so there's nothing here for them to accidentally break. Wording
# changes later are a small follow-up job, not a self-serve command.
# ———————————————––

AGREE_REACT_EMOJIS = [
    "<a:316099angel1:1515075390971056179>",
    "<:DnsBowBon:1515405474848047265>",
    "<a:316099angel2:1515075425804751109>",
]

TOS_RULES_TEXT = """<:INVISIBLEBLOCK:1419367268751642654> ͏  **‿ ₊ ׁ ͏ ︶ ₊‿** <:INVISIBLEBLOCK:1419367268751642654> <:bonBOWDNS:1515751859128635533> <:bonBOWDNS2:1515751886840402112> <:INVISIBLEBLOCK:1419367268751642654>**‿₊ ︶ ׁ ͏ ₊ ‿**
<:INVISIBLEBLOCK:1419367268751642654><:INVISIBLEBLOCK:1419367268751642654><:INVISIBLEBLOCK:1419367268751642654><:dnsBUTTERFLYbonDNSDNSDNS:1515774840395665609>.˚ ა  ***my rules*** ໒ ˚ . <:DNSButterflyBON:1515405223215108198>
<:BowsCredsToNapsDiscord:1514749536088621207> **p**ayment must always be sent **first**
<:BowsCredsToNapsDiscord:1514749536088621207> **p**ayment must also be pre__pared__, **no waiting**
<:BowsCredsToNapsDiscord:1514749536088621207> **t**here is no **refunds** unless its an is__sue__ on my end
<:BowsCredsToNapsDiscord:1514749536088621207> **p**urchasing an **assetpack** & you leave server = loose access no **refunds**
<:BowsCredsToNapsDiscord:1514749536088621207> **b**e r**espectful** to all staff members & owner
<:BowsCredsToNapsDiscord:1514749536088621207> **y**ou cannot **resell** any of my ugcs
<:BowsCredsToNapsDiscord:1514749536088621207> **y**ou cannot **steal** my meshes
<:BowsCredsToNapsDiscord:1514749536088621207> **y**ou cannot **inspo** off my **designs**/**concepts**.
<:BowsCredsToNapsDiscord:1514749536088621207> **n**o __ageplay__ charms
<:BowsCredsToNapsDiscord:1514749536088621207> **no** __ai__ charms
<:BowsCredsToNapsDiscord:1514749536088621207> **m**ust vouch before you can recieve **codes**/**files**
<:BowsCredsToNapsDiscord:1514749536088621207> **f**ake/**c**harging back payments will re__sult__ in a ban (**no appeal**) and a **DMCA**
<:BowsCredsToNapsDiscord:1514749536088621207> **y**our agreement will be **logged** incase of any __issues__
<:CredWishingPenR:1528355071392350288> {mention} **t**o agree to my rules, type "**i agree**" in chat <:LolipopRCredsToNapsDiscord:1514749987026767872> 
-# not agreeing will lead to your ticket being closed"""

TOS_THANKYOU_TEXT = """<:LolipopLCredsToNapsDiscord:1514750012465352904> thank you, {mention} you have agreed to my rules 𓈒 𓈒 𓈒
<:bonBOWDNS:1515751859128635533><:bonBOWDNS2:1515751886840402112> {staff_mention} or {owner_mention} will help you shortly <:HeartOutline:1528358317112557578>"""

LIM_TEXT = """<:INVISIBLEBLOCK:1419367268751642654> ͏  **‿ ₊ ׁ ͏ ︶ ₊‿** <:INVISIBLEBLOCK:1419367268751642654><:bonBOWDNS:1515751859128635533><:bonBOWDNS2:1515751886840402112> <:INVISIBLEBLOCK:1419367268751642654>**‿₊ ︶ ׁ ͏ ₊ ‿**
<:INVISIBLEBLOCK:1419367268751642654><:INVISIBLEBLOCK:1419367268751642654><:dnsBUTTERFLYbonDNSDNSDNS:1515774840395665609>**.˚ ა ** ***claim your ugc*** ໒ ˚ . <:DNSButterflyBON:1515405223215108198>
<:bonBOWDNS:1515751859128635533><:bonBOWDNS2:1515751886840402112> ‿𓈒೨ [/pum](https://www.roblox.com/communities/219623990/pum#!/about) ౿𓈒‿ <:CredWishingPenL:1528355102706892893>
<:BowsCredsToNapsDiscord:1514749536088621207> **y**ou must be in my **roblox group**, to claim your neck__lace__ otherwise it will not allow you to claim your **customized** ugc
-# <:pumwhitedot:1470159876431810754>must be role 4+ or higher <:exclamation_mark:1515080695104409810> 
<:bonBOWDNS:1515751859128635533><:bonBOWDNS2:1515751886840402112> ‿𓈒೨ join [here](https://www.roblox.com/games/15108736400/Flex-UGC-Codes) to claim your ugc ౿𓈒‿ <:CredWishingPenL:1528355102706892893>
<:BowsCredsToNapsDiscord:1514749536088621207> **y**our ugc **code** is 𓈒 𓈒 𓈒 `{code}`
-# <:pumwhitedot:1470159876431810754>if any problems while trying to claim, let staff know <:exclamation_mark:1515080695104409810> 
<:INVISIBLEBLOCK:1419367268751642654> ͏  **‿ ₊ ׁ ͏ ︶ ₊‿ ‿ <a:316099angel1:1515075390971056179><:INVISIBLEBLOCK:1419367268751642654><a:316099angel2:1515075425804751109>‿ ‿₊ ︶ ׁ ͏ ₊ ‿**"""

EURO_TEXT = """**‿𓈒೨**<a:316099angel1:1515075390971056179>**gbp** to **euro**<a:316099angel2:1515075425804751109> **౿𓈒‿**
<:LolipopLCredsToNapsDiscord:1514750012465352904>ა **gbp**: £{gbp} <:LongBowRCredsToNapsDiscord:1514749604158246962>
<:LolipopRCredsToNapsDiscord:1514749987026767872>ა **euro**: €{converted}<:CredWishingPenL:1528355102706892893>"""

USD_TEXT = """**‿𓈒೨** <a:316099angel1:1515075390971056179>**gbp** to **usd** <a:316099angel2:1515075425804751109>  **౿𓈒‿**
<:LolipopLCredsToNapsDiscord:1514750012465352904>ა **gbp**: £{gbp} <:LongBowRCredsToNapsDiscord:1514749604158246962>
<:LolipopRCredsToNapsDiscord:1514749987026767872>ა **usd**: ${converted}<:CredWishingPenL:1528355102706892893>"""

TAX_TEXT = """**‿𓈒೨** <a:316099angel1:1515075390971056179>***robux tax*** <a:316099angel2:1515075425804751109>  **౿𓈒‿**
<:LolipopLCredsToNapsDiscord:1514750012465352904>ა **before tax**: <:robux:1515100825792413766> {before} <:LongBowRCredsToNapsDiscord:1514749604158246962>
<:LolipopRCredsToNapsDiscord:1514749987026767872>ა **after tax**: <:robux:1515100825792413766> {after} <:CredWishingPenL:1528355102706892893>"""

RATE_CACHE: dict[tuple[str, str], tuple[float, float]] = {}
RATE_CACHE_TTL_SECONDS = 3600


def format_number(value: float) -> str:
    rounded = round(value, 2)
    if rounded == int(rounded):
        return str(int(rounded))
    return f"{rounded:.2f}"


# ———————————————––
# Database Helpers — just enough to run .tos_ticket_config / .tos_roles /
# the "who's allowed to say i agree" tracking. No templates table at all.
# ———————————————––

def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS settings (
            guild_id INTEGER PRIMARY KEY,
            tos_ticket_category_id INTEGER,
            tos_ticket_prefix TEXT,
            staff_role_id INTEGER,
            owner_role_id INTEGER
        )
        """
    )

    # target_user_id is nullable: if we couldn't confidently figure out who
    # the ticket belongs to, we still post the TOS (just without a personal
    # @mention), and then anyone who types "i agree" in that channel counts.
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS tos_pending (
            channel_id INTEGER PRIMARY KEY,
            guild_id INTEGER NOT NULL,
            target_user_id INTEGER
        )
        """
    )

    conn.commit()
    conn.close()


def get_settings(guild_id: int) -> sqlite3.Row | None:
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM settings WHERE guild_id = ?", (guild_id,))
    row = cur.fetchone()
    conn.close()
    return row


def upsert_settings(guild_id: int, **kwargs) -> None:
    allowed = {"tos_ticket_category_id", "tos_ticket_prefix", "staff_role_id", "owner_role_id"}
    updates = {k: v for k, v in kwargs.items() if k in allowed}
    if not updates:
        return

    conn = get_db()
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO settings (guild_id) VALUES (?)", (guild_id,))
    for key, value in updates.items():
        cur.execute(f"UPDATE settings SET {key} = ? WHERE guild_id = ?", (value, guild_id))
    conn.commit()
    conn.close()


def set_tos_pending(channel_id: int, guild_id: int, target_user_id: int | None) -> None:
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "INSERT OR REPLACE INTO tos_pending (channel_id, guild_id, target_user_id) VALUES (?, ?, ?)",
        (channel_id, guild_id, target_user_id),
    )
    conn.commit()
    conn.close()


def get_tos_pending(channel_id: int) -> sqlite3.Row | None:
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM tos_pending WHERE channel_id = ?", (channel_id,))
    row = cur.fetchone()
    conn.close()
    return row


def clear_tos_pending(channel_id: int) -> None:
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM tos_pending WHERE channel_id = ?", (channel_id,))
    conn.commit()
    conn.close()


# ———————————————––
# Helpers
# ———————————————––

def role_mention_or_fallback(guild: discord.Guild, role_id, fallback: str) -> str:
    if not role_id:
        return fallback
    role = guild.get_role(int(role_id))
    return role.mention if role else fallback


MENTION_OR_ID_RE = re.compile(r'<@!?(\d+)>|\b(\d{15,20})\b')


def guess_ticket_owner(channel: discord.TextChannel) -> discord.Member | None:
    """Best-effort guess at who a ticket belongs to, tried in order:
    1) Most ticket bots grant an explicit per-member permission overwrite to
       the customer who opened the ticket — if exactly one non-bot member has
       one, that's them.
    2) Some ticket bots put the opener's mention/ID in the channel topic —
       check there next.
    If neither works we return None. The TOS still gets posted either way
    (see post_tos) — it just won't have a personal @mention in that case."""
    candidates = [
        target for target in channel.overwrites
        if isinstance(target, discord.Member) and not target.bot
    ]
    if len(candidates) == 1:
        return candidates[0]

    if channel.topic:
        m = MENTION_OR_ID_RE.search(channel.topic)
        if m:
            user_id = int(m.group(1) or m.group(2))
            member = channel.guild.get_member(user_id)
            if member:
                return member

    return None


async def get_exchange_rate(base: str, target: str) -> float | None:
    """Live rate from the free, keyless Frankfurter API (ECB data), cached for
    an hour. Falls back to the last cached rate if the API call fails."""
    cache_key = (base, target)
    cached = RATE_CACHE.get(cache_key)
    now = time.time()
    if cached and now - cached[1] < RATE_CACHE_TTL_SECONDS:
        return cached[0]

    try:
        async with aiohttp.ClientSession() as session:
            url = f"https://api.frankfurter.app/latest?from={base}&to={target}"
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status != 200:
                    return cached[0] if cached else None
                data = await resp.json()
                rate = data["rates"][target]
                RATE_CACHE[cache_key] = (rate, now)
                return rate
    except Exception as e:
        print(f"[DEBUG] Failed to fetch exchange rate {base}->{target}: {e}")
        return cached[0] if cached else None


async def post_tos(channel: discord.TextChannel, target: discord.Member | None) -> None:
    """Posts the TOS. target is optional — if we couldn't identify the ticket
    owner, it still posts (just with an empty {mention}), and then anyone who
    types "i agree" in that channel is accepted instead of one specific
    person."""
    mention = target.mention if target else ""
    await channel.send(TOS_RULES_TEXT.format(mention=mention))
    set_tos_pending(channel.id, channel.guild.id, target.id if target else None)


# ———————————————––
# Events
# ———————————————––

@bot.event
async def on_ready():
    init_db()
    print(f"Bot user: {bot.user}")


@bot.event
async def on_command_error(ctx: commands.Context, error: commands.CommandError):
    if isinstance(error, commands.CheckFailure):
        await ctx.reply("⚠️ You don't have permission to use that command.", mention_author=False)
        return
    if isinstance(error, (commands.MissingRequiredArgument, commands.BadArgument)):
        await ctx.reply(f"⚠️ {error}", mention_author=False)
        return
    if isinstance(error, commands.CommandNotFound):
        return
    print(f"[COMMAND ERROR] {ctx.command}: {error!r}")
    await ctx.reply("⚠️ Something went wrong running that command. It's been logged.", mention_author=False)


@bot.event
async def on_guild_channel_create(channel: discord.abc.GuildChannel):
    """Auto-posts the TOS the moment a new ticket channel is created — no
    command needed — as long as .tos_ticket_config has been set. It always
    posts; if it can't confidently identify the owner, it just posts without
    a personal mention rather than skipping."""
    if not isinstance(channel, discord.TextChannel):
        return

    settings = get_settings(channel.guild.id)
    if not settings or not settings["tos_ticket_category_id"] or not settings["tos_ticket_prefix"]:
        return

    if not channel.category or str(channel.category.id) != str(settings["tos_ticket_category_id"]):
        return

    if not channel.name.lower().startswith(settings["tos_ticket_prefix"].lower()):
        return

    owner = guess_ticket_owner(channel)
    if not owner:
        print(f"[DEBUG] Couldn't identify ticket owner for new channel {channel.id}; posting TOS without a personal mention.")

    try:
        await post_tos(channel, owner)
    except Exception as e:
        print(f"[DEBUG] Failed to auto-post TOS in new ticket channel {channel.id}: {e}")


@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    await bot.process_commands(message)

    if not message.guild:
        return

    pending = get_tos_pending(message.channel.id)
    if not pending:
        return
    if pending["target_user_id"] is not None and pending["target_user_id"] != message.author.id:
        return
    if "i agree" not in message.content.lower():
        return

    for emoji in AGREE_REACT_EMOJIS:
        try:
            await message.add_reaction(emoji)
        except Exception as e:
            print(f"[DEBUG] Failed to add reaction {emoji} to agreement message: {e}")

    settings = get_settings(message.guild.id)
    staff_mention = role_mention_or_fallback(message.guild, settings["staff_role_id"] if settings else None, "staff")
    owner_mention = role_mention_or_fallback(message.guild, settings["owner_role_id"] if settings else None, "owner")

    await message.channel.send(TOS_THANKYOU_TEXT.format(mention=message.author.mention, staff_mention=staff_mention, owner_mention=owner_mention))
    clear_tos_pending(message.channel.id)


# ———————————————––
# Commands — TOS
# ———————————————––

@bot.command(name="a")
@commands.has_permissions(manage_messages=True)
async def tos_agreement(ctx: commands.Context, member: discord.Member = None):
    """.a [@user] — manual fallback for when auto-posting isn't set up (or
    guessed wrong). If you don't specify a user, it tries the same
    auto-detection the ticket-creation hook uses."""
    target = member or guess_ticket_owner(ctx.channel)
    await post_tos(ctx.channel, target)
    try:
        await ctx.message.delete()
    except discord.Forbidden:
        pass


@bot.command(name="tos_ticket_config")
@commands.has_permissions(manage_guild=True)
async def tos_ticket_config(ctx: commands.Context, category: discord.CategoryChannel, prefix: str):
    """.tos_ticket_config <category> <prefix> — new channels created under that
    category starting with that prefix will get the TOS auto-posted, no
    command needed."""
    upsert_settings(ctx.guild.id, tos_ticket_category_id=str(category.id), tos_ticket_prefix=prefix.strip())
    await ctx.reply(
        f"✅ New channels under **{category.name}** starting with `{prefix.strip()}` will get the TOS auto-posted.",
        mention_author=False,
    )


@bot.command(name="tos_ticket_config_clear")
@commands.has_permissions(manage_guild=True)
async def tos_ticket_config_clear(ctx: commands.Context):
    """.tos_ticket_config_clear — turns off auto-posting; use .a manually instead."""
    upsert_settings(ctx.guild.id, tos_ticket_category_id="", tos_ticket_prefix="")
    await ctx.reply("✅ Auto-posting TOS on new tickets is now off.", mention_author=False)


@bot.command(name="tos_roles")
@commands.has_permissions(manage_guild=True)
async def tos_roles(ctx: commands.Context, staff_role: discord.Role, owner_role: discord.Role):
    """.tos_roles @StaffRole @OwnerRole — sets which roles get pinged in the
    'thank you for agreeing' message."""
    upsert_settings(ctx.guild.id, staff_role_id=str(staff_role.id), owner_role_id=str(owner_role.id))
    await ctx.reply(f"✅ Staff role: {staff_role.mention} | Owner role: {owner_role.mention}", mention_author=False)


# ———————————————––
# Commands — Lim (redeem code)
# ———————————————––

@bot.command(name="lim")
@commands.has_permissions(manage_messages=True)
async def lim_command(ctx: commands.Context, *, code: str):
    """.lim <code> — sends the redeem message with the code filled in."""
    text = LIM_TEXT.format(code=code.strip())
    if len(text) > 2000:
        await ctx.reply("⚠️ That message is too long to send (Discord's 2000 character limit).", mention_author=False)
        return
    await ctx.send(text)
    try:
        await ctx.message.delete()
    except discord.Forbidden:
        pass


# ———————————————––
# Commands — Currency Converters
# ———————————————––

@bot.command(name="euro")
async def euro_command(ctx: commands.Context, amount: float):
    """.euro <amount> — converts GBP to EUR using the live rate."""
    rate = await get_exchange_rate("GBP", "EUR")
    if rate is None:
        await ctx.reply("⚠️ Couldn't fetch the exchange rate right now — try again in a bit.", mention_author=False)
        return
    converted = amount * rate
    await ctx.send(EURO_TEXT.format(gbp=format_number(amount), converted=format_number(converted)))


@bot.command(name="usd")
async def usd_command(ctx: commands.Context, amount: float):
    """.usd <amount> — converts GBP to USD using the live rate."""
    rate = await get_exchange_rate("GBP", "USD")
    if rate is None:
        await ctx.reply("⚠️ Couldn't fetch the exchange rate right now — try again in a bit.", mention_author=False)
        return
    converted = amount * rate
    await ctx.send(USD_TEXT.format(gbp=format_number(amount), converted=format_number(converted)))


# ———————————————––
# Commands — Robux Tax
# ———————————————––

@bot.command(name="tax")
async def tax_command(ctx: commands.Context, amount: float):
    """.tax <amount> — how much you need to charge (after tax) to actually
    net this amount, given Roblox's 30% marketplace tax. E.g. .tax 100 ->
    before tax: 100, after tax: 143 (charge 143 to net 100)."""
    after_tax = math.ceil(amount / 0.70)
    await ctx.send(TAX_TEXT.format(before=format_number(amount), after=format_number(after_tax)))


# ———————————————––
# Run
# ———————————————––

if not TOKEN:
    raise RuntimeError("DISCORD_TOKEN environment variable is not set")

bot.run(TOKEN)

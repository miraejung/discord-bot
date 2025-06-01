import os
import discord
from discord.ext import commands
from discord import app_commands
import time
import json

# ▶ 토큰 불러오기
def load_token():
    if os.path.exists("config.json"):
        with open("config.json", "r") as f:
            return json.load(f)["token"]
    else:
        token = input("🔐 디스코드 봇 토큰을 입력하세요: ")
        with open("config.json", "w") as f:
            json.dump({"token": token}, f)
        return token

TOKEN = load_token()

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix='!', intents=intents)

ALLOWED_TEXT_CHANNEL_IDS = [
    758040017439293501,  # 필요시 채널 ID 추가
]

cooldowns = {}

class RecruitView(discord.ui.View):
    def __init__(self, invite_url: str):
        super().__init__()
        self.add_item(discord.ui.Button(label="🎧 음성 채널 입장하기", style=discord.ButtonStyle.link, url=invite_url))

@bot.event
async def on_ready():
    print(f'✅ 봇 실행됨: {bot.user}')
    try:
        synced = await bot.tree.sync()
        print(f'📌 명령어 동기화 완료 ({len(synced)}개)')
    except Exception as e:
        print(f'⚠️ 오류 발생: {e}')

@bot.tree.command(name="구인", description="현재 음성 채널 기준으로 구인 공고를 작성합니다.")
@app_commands.describe(description="설명")
@app_commands.rename(description="설명")  # ← 한글로 파라미터 보이게
async def recruit(interaction: discord.Interaction, description: str):
    maximum = 4
    user_id = interaction.user.id
    now = time.time()

    if interaction.channel.id not in ALLOWED_TEXT_CHANNEL_IDS:
        await interaction.response.send_message(
            "❗ 이 명령어는 지정된 채팅 채널에서만 사용할 수 있습니다.",
            ephemeral=True
        )
        return

    if user_id in cooldowns and now - cooldowns[user_id] < 60:
        remain = int(60 - (now - cooldowns[user_id]))
        await interaction.response.send_message(
            f"⏱️ 쿨타임 적용 중입니다. {remain}초 후 다시 시도해주세요.",
            ephemeral=True
        )
        return

    voice_state = interaction.user.voice
    if not voice_state or not voice_state.channel:
        await interaction.response.send_message(
            "❗ 먼저 음성 채널에 접속해 주세요.",
            ephemeral=True
        )
        return

    voice_channel = voice_state.channel
    members = [m for m in voice_channel.members if not m.bot]
    current = len(members)

    if current > maximum:
        await interaction.response.send_message(
            f"❗ 현재 인원 수가 최대 인원({maximum}명)을 초과했습니다. ({current}명 접속 중)",
            ephemeral=True
        )
        return

    category_name = voice_channel.category.name if voice_channel.category else "기타"
    invite = await voice_channel.create_invite(max_age=300, max_uses=5, unique=True)

    embed = discord.Embed(
        title="📢 구인 공고",
        description=f"{interaction.user.mention} 님이 멤버를 모집 중입니다!",
        color=discord.Color.green()
    )
    embed.add_field(name="카테고리", value=f"【 {category_name} 】", inline=False)
    embed.add_field(name="채널명", value=f"[{voice_channel.name}]({invite.url})", inline=True)
    embed.add_field(name="멤버 수", value=f"{current}명 / {maximum}명", inline=True)
    embed.add_field(name="설명", value=description, inline=False)

    view = RecruitView(invite.url)

    await interaction.response.send_message(
        embed=embed,
        view=view
    )

    cooldowns[user_id] = now

bot.run(TOKEN)

import os
import discord
from discord.ext import commands
from discord import app_commands
import time
import sys

# ▶ 환경 변수로 토큰 불러오기
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
if TOKEN is None:
    print("❗ 환경 변수 DISCORD_BOT_TOKEN이 설정되지 않았습니다.")
    sys.exit(1)

print(f"🔍 읽어온 토큰(repr): {repr(TOKEN)}")
print(f"🔢 토큰 길이: {len(TOKEN)} 자")

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix='!', intents=intents)

# 허용된 텍스트 채널 ID 목록
ALLOWED_TEXT_CHANNEL_IDS = [
    758040017439293501,  # 필요시 텍스트 채널 ID 수정
]

cooldowns = {}

class RecruitView(discord.ui.View):
    def __init__(self, invite_url: str):
        super().__init__()
        self.add_item(
            discord.ui.Button(
                label="🎧 음성 채널 입장하기",
                style=discord.ButtonStyle.link,
                url=invite_url
            )
        )

@bot.event
async def on_ready():
    print(f'✅ 봇 실행됨: {bot.user} (ID: {bot.user.id})')
    try:
        synced = await bot.tree.sync()
        print(f'📌 슬래시 명령어 동기화 완료 ({len(synced)}개)')
    except Exception as e:
        print(f'⚠️ 슬래시 명령어 동기화 중 오류 발생: {e}')

@bot.tree.command(name="구인", description="현재 음성 채널 기준으로 구인 공고를 작성합니다.")
@app_commands.describe(description="설명")
@app_commands.rename(description="설명")
async def recruit(interaction: discord.Interaction, description: str):
    user_id = interaction.user.id
    now = time.time()

    if interaction.channel.id not in ALLOWED_TEXT_CHANNEL_IDS:
        await interaction.response.send_message(
            "❗ 이 명령어는 지정된 텍스트 채널에서만 사용할 수 있습니다.",
            ephemeral=True
        )
        return

    if user_id in cooldowns and now - cooldowns[user_id] < 60:
        remain = int(60 - (now - cooldowns[user_id]))
        await interaction.response.send_message(
            f"⏱️ 쿨타임이 적용되어 있습니다. {remain}초 후에 다시 시도해주세요.",
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
    current_count = len(members)

    # 음성 채널 최대 인원 수 확인 (없으면 99로 설정)
    max_limit = voice_channel.user_limit if voice_channel.user_limit != 0 else 99

    if current_count > max_limit:
        await interaction.response.send_message(
            f"❗ 현재 인원 수가 최대 인원({max_limit}명)을 초과했습니다. ({current_count}명 접속 중)",
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
    embed.add_field(name="멤버 수", value=f"{current_count}명 / {max_limit}명", inline=True)
    embed.add_field(name="설명", value=description, inline=False)

    view = RecruitView(invite.url)

    # ▶ 슬래시 응답 (숨김 메시지 아님)
    await interaction.response.send_message(
        embed=embed,
        view=view
    )

    # ▶ 전체 알림 메시지
    await interaction.channel.send(
        content="@everyone 📢 새로운 구인 공고가 도착했습니다!",
        embed=embed,
        view=view
    )

    cooldowns[user_id] = now

# ▶ 봇 실행
bot.run(TOKEN)

